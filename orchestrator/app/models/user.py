"""User model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TableNameMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.security import AuditLog
    from app.models.deployment import Deployment
    from app.models.ai_context import AIUserContext


class User(Base, TableNameMixin, TimestampMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Relationships
    deployments: Mapped[list["Deployment"]] = relationship(
        "Deployment", back_populates="user", lazy="selectin"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", lazy="selectin"
    )
    ai_context: Mapped["AIUserContext"] = relationship(
        "AIUserContext", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
