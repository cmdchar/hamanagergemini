"""Backup schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# Backup schemas
class BackupBase(BaseModel):
    """Base backup schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    backup_type: str = Field(..., pattern="^(nodered|zigbee2mqtt|ha_config|full)$")
    retention_days: Optional[int] = Field(None, ge=1, le=365)
    tags: Optional[List[str]] = None


class BackupCreate(BaseModel):
    """Create backup request."""

    config_id: int
    backup_type: str = Field(..., pattern="^(nodered|zigbee2mqtt)$")
    name: Optional[str] = None
    description: Optional[str] = None
    retention_days: Optional[int] = None


class BackupResponse(BackupBase):
    """Backup response."""

    id: int
    server_id: Optional[int] = None
    deployment_id: Optional[int] = None
    storage_path: str
    file_size: int
    file_hash: Optional[str] = None
    compression: str
    source_host: Optional[str] = None
    source_path: Optional[str] = None
    source_version: Optional[str] = None
    backup_date: datetime
    expires_at: Optional[datetime] = None
    status: str
    verified: bool
    encrypted: bool
    items_count: Optional[int] = None
    content_summary: Optional[dict] = None
    is_automatic: bool
    schedule_id: Optional[int] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Restore schemas
class BackupRestoreCreate(BaseModel):
    """Create restore request."""

    backup_id: int
    target_host: str
    target_path: str
    overwrite_existing: bool = False
    create_backup_before: bool = True
    restore_all: bool = True
    selected_items: Optional[List[str]] = None


class BackupRestoreResponse(BaseModel):
    """Restore response."""

    id: int
    backup_id: int
    target_host: str
    target_path: str
    overwrite_existing: bool
    create_backup_before: bool
    restore_all: bool
    selected_items: Optional[List[str]] = None
    status: str
    progress: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    items_restored: int
    items_failed: int
    rollback_backup_id: Optional[int] = None
    can_rollback: bool
    rolled_back: bool
    restore_log: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schedule schemas
class BackupScheduleBase(BaseModel):
    """Base schedule schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    backup_type: str = Field(..., pattern="^(nodered|zigbee2mqtt|ha_config|full)$")
    cron_expression: str = Field(..., min_length=1, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)
    retention_days: int = Field(default=30, ge=1, le=365)
    max_backups: Optional[int] = Field(None, ge=1, le=100)
    storage_location: str
    compression: str = Field(default="gzip", pattern="^(gzip|zip|tar|none)$")
    encrypt: bool = False
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_emails: Optional[List[str]] = None


class BackupScheduleCreate(BackupScheduleBase):
    """Create schedule request."""

    server_id: Optional[int] = None
    deployment_id: Optional[int] = None


class BackupScheduleUpdate(BaseModel):
    """Update schedule request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    enabled: Optional[bool] = None
    cron_expression: Optional[str] = None
    retention_days: Optional[int] = Field(None, ge=1, le=365)
    max_backups: Optional[int] = Field(None, ge=1, le=100)
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notification_emails: Optional[List[str]] = None


class BackupScheduleResponse(BackupScheduleBase):
    """Schedule response."""

    id: int
    server_id: Optional[int] = None
    deployment_id: Optional[int] = None
    enabled: bool
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_status: Optional[str] = None
    run_count: int
    failure_count: int
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Node-RED config schemas
class NodeREDConfigBase(BaseModel):
    """Base Node-RED config schema."""

    name: str = Field(..., min_length=1, max_length=255)
    base_url: str
    api_key: Optional[str] = None
    flows_file: str
    settings_file: Optional[str] = None
    user_dir: Optional[str] = None
    auto_backup_enabled: bool = True
    backup_on_deploy: bool = True


class NodeREDConfigCreate(NodeREDConfigBase):
    """Create Node-RED config request."""

    server_id: int


class NodeREDConfigUpdate(BaseModel):
    """Update Node-RED config request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    flows_file: Optional[str] = None
    settings_file: Optional[str] = None
    enabled: Optional[bool] = None
    auto_backup_enabled: Optional[bool] = None
    backup_on_deploy: Optional[bool] = None


class NodeREDConfigResponse(NodeREDConfigBase):
    """Node-RED config response."""

    id: int
    server_id: int
    version: Optional[str] = None
    enabled: bool
    last_backup: Optional[datetime] = None
    flows_count: int
    nodes_count: int
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Zigbee2MQTT config schemas
class Zigbee2MQTTConfigBase(BaseModel):
    """Base Zigbee2MQTT config schema."""

    name: str = Field(..., min_length=1, max_length=255)
    mqtt_server: str
    mqtt_base_topic: str = Field(default="zigbee2mqtt", max_length=100)
    data_dir: str
    config_file: str
    devices_file: Optional[str] = None
    groups_file: Optional[str] = None
    coordinator_backup: Optional[str] = None
    auto_backup_enabled: bool = True
    backup_coordinator: bool = True


class Zigbee2MQTTConfigCreate(Zigbee2MQTTConfigBase):
    """Create Zigbee2MQTT config request."""

    server_id: int


class Zigbee2MQTTConfigUpdate(BaseModel):
    """Update Zigbee2MQTT config request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    mqtt_server: Optional[str] = None
    mqtt_base_topic: Optional[str] = None
    data_dir: Optional[str] = None
    config_file: Optional[str] = None
    enabled: Optional[bool] = None
    auto_backup_enabled: Optional[bool] = None
    backup_coordinator: Optional[bool] = None


class Zigbee2MQTTConfigResponse(Zigbee2MQTTConfigBase):
    """Zigbee2MQTT config response."""

    id: int
    server_id: int
    version: Optional[str] = None
    enabled: bool
    last_backup: Optional[datetime] = None
    devices_count: int
    groups_count: int
    coordinator_type: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Utility schemas
class BackupVerifyResponse(BaseModel):
    """Backup verification response."""

    backup_id: int
    valid: bool
    file_exists: bool
    hash_match: bool
    error: Optional[str] = None


class BackupCleanupRequest(BaseModel):
    """Cleanup request."""

    retention_days: Optional[int] = Field(None, ge=1, le=365)
    max_backups: Optional[int] = Field(None, ge=1, le=100)
    backup_type: Optional[str] = None


class BackupCleanupResponse(BaseModel):
    """Cleanup response."""

    deleted_count: int
    freed_space: int  # Bytes


class BackupStatistics(BaseModel):
    """Backup statistics."""

    total_backups: int
    total_size: int  # Bytes
    backups_by_type: dict
    oldest_backup: Optional[datetime] = None
    newest_backup: Optional[datetime] = None
    total_restores: int
    successful_restores: int
    failed_restores: int
    scheduled_backups: int
    active_schedules: int
