"""AI conversation models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TableNameMixin, TimestampMixin


class AIConversation(Base, TableNameMixin, TimestampMixin):
    """AI conversation session model."""

    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # User association
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Conversation info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Context
    server_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # If conversation is about specific server
    deployment_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # If about specific deployment
    context_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # server, deployment, general, wled, fpp, etc.

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # Model settings
    model: Mapped[str] = mapped_column(String(100), default="deepseek-chat")
    temperature: Mapped[float] = mapped_column(default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2000)

    # Metadata
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<AIConversation(id={self.id}, title={self.title}, messages={self.message_count})>"


class AIMessage(Base, TableNameMixin, TimestampMixin):
    """AI message model."""

    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Conversation association
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("ai_conversations.id"), nullable=False)

    # Message content
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Token usage
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Context included
    context_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Server/deployment data if included

    # Model info
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    finish_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadata
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<AIMessage(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"


class AIPromptTemplate(Base, TableNameMixin, TimestampMixin):
    """AI prompt template model."""

    __tablename__ = "ai_prompt_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Template info
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # troubleshooting, automation, configuration, etc.

    # Template content
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Variables in template
    variables: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of variable names

    # Usage
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0)

    # Model settings
    recommended_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recommended_temperature: Mapped[Optional[float]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<AIPromptTemplate(id={self.id}, name={self.name}, category={self.category})>"


class AIFeedback(Base, TableNameMixin, TimestampMixin):
    """AI feedback model for improving responses."""

    __tablename__ = "ai_feedback"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Message association
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("ai_messages.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Feedback
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 stars
    helpful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Categories
    accuracy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    relevance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    clarity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5

    def __repr__(self) -> str:
        """String representation."""
        return f"<AIFeedback(id={self.id}, message_id={self.message_id}, rating={self.rating})>"
