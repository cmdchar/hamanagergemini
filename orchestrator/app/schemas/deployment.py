"""Deployment Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.models.deployment import DeploymentStatus, DeploymentTrigger
from app.schemas.common import BaseSchema, TimestampSchema


class DeploymentBase(BaseSchema):
    """Base deployment schema."""

    target_servers: Optional[List[int]] = None
    deploy_all: bool = False
    skip_validation: bool = False
    skip_backup: bool = False
    auto_restart: bool = True
    auto_rollback: bool = True


class DeploymentCreate(DeploymentBase):
    """Schema for creating a deployment."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    commit_sha: Optional[str] = Field(None, max_length=40)
    commit_message: Optional[str] = None
    branch: Optional[str] = None
    trigger: DeploymentTrigger = DeploymentTrigger.MANUAL
    metadata: Optional[Dict[str, Any]] = None


class DeploymentUpdate(BaseSchema):
    """Schema for updating a deployment."""

    status: Optional[DeploymentStatus] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DeploymentResultBase(BaseSchema):
    """Base deployment result schema."""

    server_id: int
    status: DeploymentStatus
    success: bool


class DeploymentResultResponse(DeploymentResultBase, TimestampSchema):
    """Schema for deployment result response."""

    id: int
    deployment_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    validation_output: Optional[str] = None
    backup_id: Optional[int] = None
    logs: Optional[str] = None
    error_message: Optional[str] = None
    files_changed: Optional[List[str]] = None
    files_added: Optional[List[str]] = None
    files_deleted: Optional[List[str]] = None


class DeploymentResponse(DeploymentBase, TimestampSchema):
    """Schema for deployment response."""

    id: int
    user_id: int
    status: DeploymentStatus
    trigger: DeploymentTrigger
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None
    branch: Optional[str] = None
    author: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    total_servers: int
    successful_servers: int
    failed_servers: int
    logs: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    can_rollback: bool
    rolled_back_from_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    server_results: List[DeploymentResultResponse] = Field(default_factory=list)


class DeploymentListResponse(TimestampSchema):
    """Schema for deployment list response (minimal)."""

    id: int
    status: DeploymentStatus
    trigger: DeploymentTrigger
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None
    branch: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    total_servers: int
    successful_servers: int
    failed_servers: int


class DeploymentProgress(BaseSchema):
    """Schema for deployment progress."""

    deployment_id: int
    status: DeploymentStatus
    progress_percent: float = Field(ge=0, le=100)
    current_step: str
    total_servers: int
    completed_servers: int
    failed_servers: int
    logs: List[str] = Field(default_factory=list)


class DeploymentWebhookPayload(BaseSchema):
    """Schema for GitHub webhook deployment."""

    ref: str  # branch ref
    repository: str
    commit_sha: str
    commit_message: str
    author: str
    pusher: str
    target_servers: Optional[List[int]] = None
    deploy_all: bool = True


class RollbackRequest(BaseSchema):
    """Schema for rollback request."""

    deployment_id: int
    target_servers: Optional[List[int]] = None
    rollback_all: bool = True
    reason: Optional[str] = None


class RollbackResponse(BaseSchema):
    """Schema for rollback response."""

    success: bool
    message: str
    new_deployment_id: Optional[int] = None
    servers_rolled_back: int
    errors: List[str] = Field(default_factory=list)
