"""Security utilities for authentication and encryption."""

import base64
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using argon2.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        bool: True if password matches hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Optional expiration time delta

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in token
        expires_delta: Optional expiration time delta

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify

    Returns:
        Optional[Dict[str, Any]]: Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


def get_encryption_key() -> bytes:
    """
    Get or generate encryption key.

    Returns:
        bytes: Encryption key
    """
    if settings.encryption_key:
        # Use configured key
        return settings.encryption_key.encode() if isinstance(settings.encryption_key, str) else settings.encryption_key
    else:
        # Generate new key (should be stored in settings for production)
        return Fernet.generate_key()


def encrypt_value(value: str) -> str:
    """
    Encrypt a value using Fernet symmetric encryption.

    Args:
        value: Plain text value to encrypt

    Returns:
        str: Encrypted value (base64 encoded)
    """
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(value.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_value(encrypted_value: str) -> str:
    """
    Decrypt a value using Fernet symmetric encryption.

    Args:
        encrypted_value: Encrypted value (base64 encoded)

    Returns:
        str: Decrypted plain text value
    """
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = base64.urlsafe_b64decode(encrypted_value.encode())
    decrypted = f.decrypt(encrypted)
    return decrypted.decode()


def generate_api_key() -> str:
    """
    Generate a random API key.

    Returns:
        str: Random API key
    """
    import secrets

    return secrets.token_urlsafe(32)


def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """
    Mask a secret value for display.

    Args:
        secret: Secret value to mask
        visible_chars: Number of characters to show at the end

    Returns:
        str: Masked secret (e.g., "****abc123")
    """
    if len(secret) <= visible_chars:
        return "*" * len(secret)
    return "*" * (len(secret) - visible_chars) + secret[-visible_chars:]
