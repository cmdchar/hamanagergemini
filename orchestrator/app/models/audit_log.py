"""Audit log model."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TableNameMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuditAction(str, enum.Enum):
    """Audit action enumeration."""

    # User actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"

    # Server actions
    SERVER_CREATED = "server_created"
    SERVER_UPDATED = "server_updated"
    SERVER_DELETED = "server_deleted"
    SERVER_CONNECTED = "server_connected"
    SERVER_DISCONNECTED = "server_disconnected"

    # Deployment actions
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DEPLOYMENT_FAILED = "deployment_failed"
    DEPLOYMENT_ROLLED_BACK = "deployment_rolled_back"

    # Snapshot actions
    SNAPSHOT_CREATED = "snapshot_created"
    SNAPSHOT_RESTORED = "snapshot_restored"
    SNAPSHOT_DELETED = "snapshot_deleted"

    # Secret actions
    SECRET_CREATED = "secret_created"
    SECRET_UPDATED = "secret_updated"
    SECRET_DELETED = "secret_deleted"
    SECRET_ACCESSED = "secret_accessed"

    # Integration actions
    INTEGRATION_ENABLED = "integration_enabled"
    INTEGRATION_DISABLED = "integration_disabled"
    INTEGRATION_CONFIGURED = "integration_configured"

    # Configuration actions
    CONFIG_VALIDATED = "config_validated"
    CONFIG_UPDATED = "config_updated"

    # System actions
    SYSTEM_SETTINGS_UPDATED = "system_settings_updated"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"


class AuditLog(Base, TableNameMixin, TimestampMixin):
    """Audit log model for tracking all system actions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Relationships
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")

    # Action details
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)

    # Request details
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    endpoint: Mapped[str] = mapped_column(String(500), nullable=True)
    method: Mapped[str] = mapped_column(String(10), nullable=True)

    # Details
    description: Mapped[str] = mapped_column(Text, nullable=True)
    changes: Mapped[dict] = mapped_column(JSON, nullable=True)  # Before/after values
    extra_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word

    # Result
    success: Mapped[bool] = mapped_column(default=True, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"
