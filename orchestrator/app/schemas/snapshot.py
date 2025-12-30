"""Snapshot Pydantic schemas."""

from typing import Any, Dict, Optional

from pydantic import Field

from app.models.snapshot import SnapshotStatus, SnapshotType
from app.schemas.common import BaseSchema, TimestampSchema


class SnapshotBase(BaseSchema):
    """Base snapshot schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class SnapshotCreate(SnapshotBase):
    """Schema for creating a snapshot."""

    server_id: int
    snapshot_type: SnapshotType = SnapshotType.MANUAL
    includes_secrets: bool = True
    includes_database: bool = True
    compressed: bool = True
    encrypted: bool = False
    retention_days: Optional[int] = Field(None, ge=1, le=365)
    protected: bool = False
    metadata: Optional[Dict[str, Any]] = None


class SnapshotUpdate(BaseSchema):
    """Schema for updating a snapshot."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[SnapshotStatus] = None
    protected: Optional[bool] = None
    retention_days: Optional[int] = Field(None, ge=1, le=365)
    metadata: Optional[Dict[str, Any]] = None


class SnapshotResponse(SnapshotBase, TimestampSchema):
    """Schema for snapshot response."""

    id: int
    server_id: int
    snapshot_type: SnapshotType
    status: SnapshotStatus
    storage_path: str
    s3_key: Optional[str] = None
    size_bytes: Optional[int] = None
    size_mb: float
    compressed: bool
    encrypted: bool
    file_count: Optional[int] = None
    includes_secrets: bool
    includes_database: bool
    ha_version: Optional[str] = None
    commit_sha: Optional[str] = None
    deployment_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None
    retention_days: Optional[int] = None
    auto_delete: bool
    protected: bool
    is_available: bool


class SnapshotListResponse(TimestampSchema):
    """Schema for snapshot list response (minimal)."""

    id: int
    name: str
    server_id: int
    snapshot_type: SnapshotType
    status: SnapshotStatus
    size_mb: float
    ha_version: Optional[str] = None


class RestoreSnapshotRequest(BaseSchema):
    """Schema for snapshot restore request."""

    snapshot_id: int
    server_id: Optional[int] = None  # If None, restore to original server
    backup_before_restore: bool = True
    restore_secrets: bool = True
    restore_database: bool = True


class RestoreSnapshotResponse(BaseSchema):
    """Schema for snapshot restore response."""

    success: bool
    message: str
    deployment_id: Optional[int] = None
    backup_created_id: Optional[int] = None
    error: Optional[str] = None


class SnapshotDownloadResponse(BaseSchema):
    """Schema for snapshot download response."""

    download_url: str
    expires_in_seconds: int = 3600
    filename: str
    size_bytes: int
