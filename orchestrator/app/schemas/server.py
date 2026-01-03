"""Server Pydantic schemas."""

from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from app.models.server import ServerStatus, ServerType
from app.schemas.common import BaseSchema, TimestampSchema


class ServerBase(BaseSchema):
    """Base server schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(default=8123, ge=1, le=65535)
    use_ssl: bool = False


class ServerCreate(ServerBase):
    """Schema for creating a server."""

    access_token: Optional[str] = None
    api_key: Optional[str] = None
    ha_username: Optional[str] = None
    ha_password: Optional[str] = None
    ssh_host: Optional[str] = None
    ssh_port: int = Field(default=22, ge=1, le=65535)
    ssh_user: Optional[str] = None
    ssh_key_path: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_key_passphrase: Optional[str] = None
    github_repo: Optional[str] = None
    github_branch: Optional[str] = None
    server_type: ServerType = ServerType.PRODUCTION
    config_path: str = "/config"
    backup_path: Optional[str] = "/backup"
    auto_deploy: bool = False
    auto_backup: bool = True
    priority: int = Field(default=0, ge=0)
    tailscale_enabled: bool = False
    tags: Optional[List[str]] = None
    meta_data: Optional[Dict[str, Any]] = Field(None, serialization_alias="metadata")


class ServerUpdate(BaseSchema):
    """Schema for updating a server."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    use_ssl: Optional[bool] = None
    access_token: Optional[str] = None
    api_key: Optional[str] = None
    ha_username: Optional[str] = None
    ha_password: Optional[str] = None
    ssh_host: Optional[str] = None
    ssh_port: Optional[int] = Field(None, ge=1, le=65535)
    ssh_user: Optional[str] = None
    ssh_key_path: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_key_passphrase: Optional[str] = None
    github_repo: Optional[str] = None
    github_branch: Optional[str] = None
    server_type: Optional[ServerType] = None
    status: Optional[ServerStatus] = None
    config_path: Optional[str] = None
    backup_path: Optional[str] = None
    auto_deploy: Optional[bool] = None
    auto_backup: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    tailscale_enabled: Optional[bool] = None
    tailscale_ip: Optional[str] = None
    tailscale_hostname: Optional[str] = None
    tags: Optional[List[str]] = None
    meta_data: Optional[Dict[str, Any]] = Field(None, serialization_alias="metadata")


class ServerResponse(ServerBase, TimestampSchema):
    """Schema for server response."""

    id: int
    server_type: ServerType
    status: ServerStatus
    config_path: str
    backup_path: Optional[str] = None
    auto_deploy: bool
    auto_backup: bool
    priority: int
    is_active: bool
    tailscale_enabled: bool
    tailscale_ip: Optional[str] = None
    tailscale_hostname: Optional[str] = None
    version: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = Field(None, serialization_alias="metadata")
    tags: Optional[str] = None
    ssh_host: Optional[str] = None
    ssh_port: Optional[int] = None
    ssh_user: Optional[str] = None
    ha_username: Optional[str] = None
    ha_password: Optional[str] = None
    github_repo: Optional[str] = None
    github_branch: Optional[str] = None
    url: str
    ha_url: Optional[str] = None
    ha_version: Optional[str] = None
    is_online: bool = False
    last_check: Optional[str] = None


class ServerConnectionTest(BaseSchema):
    """Schema for server connection test."""

    success: bool
    message: str
    version: Optional[str] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


class ServerHealthCheck(BaseSchema):
    """Schema for server health check."""

    server_id: int
    server_name: str
    is_online: bool
    version: Optional[str] = None
    uptime_seconds: Optional[int] = None
    last_checked: str
    error: Optional[str] = None


class BulkServerOperation(BaseSchema):
    """Schema for bulk server operations."""

    server_ids: List[int] = Field(..., min_length=1)
    operation: str = Field(..., pattern="^(start|stop|restart|check_health)$")
