"""Pydantic schemas package."""

from app.schemas.common import (
    BaseSchema,
    BulkOperationResponse,
    ErrorResponse,
    HealthResponse,
    IDResponse,
    MessageResponse,
    PaginatedResponse,
    TimestampSchema,
)
from app.schemas.deployment import (
    DeploymentCreate,
    DeploymentListResponse,
    DeploymentProgress,
    DeploymentResponse,
    DeploymentResultResponse,
    DeploymentUpdate,
    DeploymentWebhookPayload,
    RollbackRequest,
    RollbackResponse,
)
from app.schemas.server import (
    BulkServerOperation,
    ServerConnectionTest,
    ServerCreate,
    ServerHealthCheck,
    ServerResponse,
    ServerUpdate,
)
from app.schemas.snapshot import (
    RestoreSnapshotRequest,
    RestoreSnapshotResponse,
    SnapshotCreate,
    SnapshotDownloadResponse,
    SnapshotListResponse,
    SnapshotResponse,
    SnapshotUpdate,
)
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    Token,
    TokenData,
    UserCreate,
    UserResponse,
    UserUpdate,
    UserUpdatePassword,
)

__all__ = [
    # Common
    "BaseSchema",
    "TimestampSchema",
    "MessageResponse",
    "ErrorResponse",
    "HealthResponse",
    "IDResponse",
    "PaginatedResponse",
    "BulkOperationResponse",
    # User
    "UserCreate",
    "UserUpdate",
    "UserUpdatePassword",
    "UserResponse",
    "Token",
    "TokenData",
    "LoginRequest",
    "LoginResponse",
    # Server
    "ServerCreate",
    "ServerUpdate",
    "ServerResponse",
    "ServerConnectionTest",
    "ServerHealthCheck",
    "BulkServerOperation",
    # Deployment
    "DeploymentCreate",
    "DeploymentUpdate",
    "DeploymentResponse",
    "DeploymentListResponse",
    "DeploymentResultResponse",
    "DeploymentProgress",
    "DeploymentWebhookPayload",
    "RollbackRequest",
    "RollbackResponse",
    # Snapshot
    "SnapshotCreate",
    "SnapshotUpdate",
    "SnapshotResponse",
    "SnapshotListResponse",
    "RestoreSnapshotRequest",
    "RestoreSnapshotResponse",
    "SnapshotDownloadResponse",
]
