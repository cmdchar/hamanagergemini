"""AI file modification tracking model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.db.base import Base, TableNameMixin, TimestampMixin


class ModificationStatus(str, enum.Enum):
    """Status of AI file modification."""
    PENDING = "pending"  # Waiting for user review
    APPROVED = "approved"  # User approved and pushed to server/GitHub
    REJECTED = "rejected"  # User rejected the changes
    REVERTED = "reverted"  # Changes were reverted


class ModificationAction(str, enum.Enum):
    """Type of modification action."""
    CREATE = "create"  # AI created a new file
    UPDATE = "update"  # AI modified existing file
    DELETE = "delete"  # AI deleted a file


class AIFileModification(Base, TableNameMixin, TimestampMixin):
    """Track AI modifications to configuration files."""

    __tablename__ = "ai_file_modifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # User and conversation tracking
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("ai_conversations.id"), nullable=True
    )
    message_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("ai_messages.id"), nullable=True
    )

    # Server and file tracking
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Modification details
    action: Mapped[str] = mapped_column(
        SQLEnum(ModificationAction, native_enum=False, length=20),
        nullable=False,
        default=ModificationAction.UPDATE
    )

    # Content tracking (BEFORE/AFTER)
    content_before: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Original content
    content_after: Mapped[str] = mapped_column(Text, nullable=False)  # AI modified content

    # AI explanation
    ai_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Why AI made this change
    ai_summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Short summary

    # Status tracking
    status: Mapped[str] = mapped_column(
        SQLEnum(ModificationStatus, native_enum=False, length=20),
        nullable=False,
        default=ModificationStatus.PENDING
    )

    # Review tracking
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    review_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # User comment when approving/rejecting

    # Deployment tracking
    pushed_to_server: Mapped[bool] = mapped_column(Boolean, default=False)
    pushed_to_server_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    pushed_to_github: Mapped[bool] = mapped_column(Boolean, default=False)
    pushed_to_github_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    github_commit_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    # Version tracking
    version: Mapped[int] = mapped_column(Integer, default=1)  # Version number for this file path
    parent_modification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_file_modifications.id"), nullable=True
    )  # If this is a revision of previous modification

    # Relationships
    user = relationship("User", backref="ai_file_modifications")
    server = relationship("Server", backref="ai_file_modifications")
    conversation = relationship("AIConversation", backref="file_modifications")
    message = relationship("AIMessage", backref="file_modifications")

    def __repr__(self) -> str:
        """String representation."""
        return f"<AIFileModification(id={self.id}, file={self.file_path}, action={self.action}, status={self.status})>"
