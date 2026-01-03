"""
AI Context models for storing user-specific knowledge base
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, Integer, JSON, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TableNameMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class AIUserContext(Base, TableNameMixin, TimestampMixin):
    """
    Stores comprehensive context about user's infrastructure and projects
    Automatically collected and updated
    """
    __tablename__ = "ai_user_contexts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Aggregated context data
    total_servers: Mapped[int] = mapped_column(Integer, default=0)
    total_deployments: Mapped[int] = mapped_column(Integer, default=0)
    total_backups: Mapped[int] = mapped_column(Integer, default=0)

    # JSON fields for structured data
    servers_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    projects_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    recent_activities: Mapped[list] = mapped_column(JSON, default=list)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="ai_context")


class AIKnowledgeBase(Base, TableNameMixin, TimestampMixin):
    """
    Stores vectorized knowledge about user's infrastructure
    For RAG (Retrieval Augmented Generation)
    """
    __tablename__ = "ai_knowledge_base"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    entry_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    importance: Mapped[int] = mapped_column(Integer, default=5)

    # Vector embedding (stored as JSON for simplicity)
    embedding: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")


class AIActionLog(Base, TableNameMixin):
    """
    Logs all actions taken by AI on behalf of users
    """
    __tablename__ = "ai_action_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    message_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_messages.id"), nullable=True)

    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_params: Mapped[dict] = mapped_column(JSON, nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    executed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
