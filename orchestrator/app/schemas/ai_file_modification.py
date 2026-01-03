"""Schemas for AI file modification tracking."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.ai_file_modification import ModificationAction, ModificationStatus


class AIFileModificationBase(BaseModel):
    """Base schema for AI file modification."""

    file_path: str = Field(..., description="Path to the file being modified")
    action: ModificationAction = Field(default=ModificationAction.UPDATE, description="Type of modification")
    content_after: str = Field(..., description="Modified content")
    content_before: Optional[str] = Field(None, description="Original content (for UPDATE/DELETE)")
    ai_explanation: Optional[str] = Field(None, description="AI explanation of changes")
    ai_summary: Optional[str] = Field(None, max_length=500, description="Short summary of changes")


class AIFileModificationCreate(AIFileModificationBase):
    """Schema for creating a file modification."""

    server_id: int = Field(..., description="Server ID")
    conversation_id: Optional[int] = Field(None, description="Associated conversation ID")
    message_id: Optional[int] = Field(None, description="Associated message ID")


class AIFileModificationUpdate(BaseModel):
    """Schema for updating a file modification."""

    content_after: Optional[str] = None
    ai_explanation: Optional[str] = None
    ai_summary: Optional[str] = None
    status: Optional[ModificationStatus] = None
    review_comment: Optional[str] = None


class AIFileModificationReview(BaseModel):
    """Schema for reviewing a file modification."""

    status: ModificationStatus = Field(..., description="Review status (approved/rejected)")
    review_comment: Optional[str] = Field(None, description="Review comment")


class AIFileModificationPush(BaseModel):
    """Schema for pushing modifications."""

    push_to_server: bool = Field(default=False, description="Push to server")
    push_to_github: bool = Field(default=False, description="Push to GitHub")
    commit_message: Optional[str] = Field(None, description="GitHub commit message")


class AIFileModificationResponse(AIFileModificationBase):
    """Schema for file modification response."""

    id: UUID
    user_id: int
    server_id: int
    conversation_id: Optional[int]
    message_id: Optional[int]

    status: ModificationStatus
    version: int
    parent_modification_id: Optional[UUID]

    reviewed_at: Optional[datetime]
    review_comment: Optional[str]

    pushed_to_server: bool
    pushed_to_server_at: Optional[datetime]
    pushed_to_github: bool
    pushed_to_github_at: Optional[datetime]
    github_commit_sha: Optional[str]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIFileModificationDiff(BaseModel):
    """Schema for file modification diff view."""

    id: UUID
    file_path: str
    action: ModificationAction
    status: ModificationStatus

    content_before: Optional[str]
    content_after: str

    ai_summary: Optional[str]
    ai_explanation: Optional[str]

    created_at: datetime

    class Config:
        from_attributes = True


class AIFileModificationListResponse(BaseModel):
    """Schema for listing file modifications."""

    id: UUID
    file_path: str
    action: ModificationAction
    status: ModificationStatus
    ai_summary: Optional[str]

    pushed_to_server: bool
    pushed_to_github: bool

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
