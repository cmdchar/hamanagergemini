"""Authentication service."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User
from app.schemas.user import LoginResponse, Token, UserCreate, UserResponse
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

settings = get_settings()


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        """Initialize auth service."""
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            Optional[User]: User instance or None
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            Optional[User]: User instance or None
        """
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            Optional[User]: User instance or None
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            User: Created user instance
        """
        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=False,
            is_superuser=False,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def authenticate_user(
        self, username: str, password: str
    ) -> Optional[User]:
        """
        Authenticate user with username and password.

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            Optional[User]: User instance if authenticated, None otherwise
        """
        # Try to find user by username or email
        user = await self.get_user_by_username(username)
        if not user:
            user = await self.get_user_by_email(username)

        if not user:
            return None

        # Verify password
        if not verify_password(password, user.hashed_password):
            return None

        # Check if user is active
        if not user.is_active:
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def login(self, username: str, password: str, remember_me: bool = False) -> Optional[LoginResponse]:
        """
        Login user and generate tokens.

        Args:
            username: Username or email
            password: Plain text password
            remember_me: Whether to extend token expiration

        Returns:
            Optional[LoginResponse]: Login response with tokens or None
        """
        # Authenticate user
        user = await self.authenticate_user(username, password)
        if not user:
            return None

        # Generate tokens
        token_data = {"sub": str(user.id), "username": user.username}

        # Extend expiration if remember_me is True
        if remember_me:
            access_token_expires = timedelta(
                minutes=settings.access_token_expire_minutes * 2
            )
            refresh_token_expires = timedelta(
                days=settings.refresh_token_expire_days * 2
            )
        else:
            access_token_expires = timedelta(
                minutes=settings.access_token_expire_minutes
            )
            refresh_token_expires = timedelta(
                days=settings.refresh_token_expire_days
            )

        access_token = create_access_token(
            data=token_data, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data=token_data, expires_delta=refresh_token_expires
        )

        # Create response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            is_superuser=user.is_superuser,
            last_login=user.last_login,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

        return LoginResponse(
            user=user_response,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
        )

    async def refresh_access_token(self, user_id: int) -> Optional[Token]:
        """
        Refresh access token for a user.

        Args:
            user_id: User ID

        Returns:
            Optional[Token]: New access token or None
        """
        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            return None

        # Generate new access token
        token_data = {"sub": str(user.id), "username": user.username}
        access_token_expires = timedelta(
            minutes=settings.access_token_expire_minutes
        )
        access_token = create_access_token(
            data=token_data, expires_delta=access_token_expires
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
        )
