"""Notification model."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TableNameMixin, TimestampMixin


class NotificationType(str, enum.Enum):
    """Notification type enumeration."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationCategory(str, enum.Enum):
    """Notification category enumeration."""

    DEPLOYMENT = "deployment"
    BACKUP = "backup"
    SERVER = "server"
    SECURITY = "security"
    INTEGRATION = "integration"
    SYSTEM = "system"


class NotificationChannel(str, enum.Enum):
    """Notification channel enumeration."""

    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    PUSH = "push"
    IN_APP = "in_app"


class Notification(Base, TableNameMixin, TimestampMixin):
    """Notification model for system notifications."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Notification details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType), default=NotificationType.INFO, nullable=False
    )
    category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory), default=NotificationCategory.SYSTEM, nullable=False
    )

    # Recipients
    user_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    send_to_all_admins: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Channels
    channels: Mapped[list] = mapped_column(JSON, nullable=True)  # List of NotificationChannel

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Related resources
    resource_type: Mapped[str] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)

    # Action
    action_url: Mapped[str] = mapped_column(String(500), nullable=True)
    action_text: Mapped[str] = mapped_column(String(100), nullable=True)

    # Metadata
    meta_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Delivery
    delivery_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_retry_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Auto-delete
    auto_delete_after_days: Mapped[int] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Notification(id={self.id}, type={self.notification_type}, title={self.title})>"

    @property
    def is_unread(self) -> bool:
        """Check if notification is unread."""
        return not self.is_read

    @property
    def should_retry(self) -> bool:
        """Check if notification should be retried."""
        return (
            not self.sent
            and self.delivery_attempts < self.max_attempts
            and (self.next_retry_at is None or datetime.utcnow() >= self.next_retry_at)
        )
