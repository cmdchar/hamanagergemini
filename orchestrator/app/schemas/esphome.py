"""ESPHome schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, IPvAnyAddress


# Device schemas
class ESPHomeDeviceBase(BaseModel):
    """Base ESPHome device schema."""

    name: str = Field(..., min_length=1, max_length=255)
    friendly_name: Optional[str] = Field(None, max_length=255)
    device_class: Optional[str] = None
    ip_address: str
    mac_address: Optional[str] = None
    port: int = Field(default=6053, ge=1, le=65535)
    platform: Optional[str] = None
    board: Optional[str] = None
    server_id: Optional[int] = None


class ESPHomeDeviceCreate(ESPHomeDeviceBase):
    """Create ESPHome device request."""

    ota_password: Optional[str] = None
    config_file: Optional[str] = None


class ESPHomeDeviceUpdate(BaseModel):
    """Update ESPHome device request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    friendly_name: Optional[str] = None
    device_class: Optional[str] = None
    ota_enabled: Optional[bool] = None
    ota_password: Optional[str] = None
    auto_update: Optional[bool] = None
    config_file: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class ESPHomeDeviceResponse(ESPHomeDeviceBase):
    """ESPHome device response."""

    id: int
    esphome_version: Optional[str] = None
    compilation_time: Optional[str] = None
    firmware_version: Optional[str] = None
    config_hash: Optional[str] = None
    ota_enabled: bool
    requires_encryption: bool
    online: bool
    last_seen: Optional[datetime] = None
    connection_status: Optional[str] = None
    update_available: bool
    update_version: Optional[str] = None
    auto_update: bool
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# OTA Update schemas
class ESPHomeOTAUpdateCreate(BaseModel):
    """Create OTA update request."""

    device_id: int
    firmware_file: str
    password: Optional[str] = None


class ESPHomeOTAUpdateResponse(BaseModel):
    """OTA update response."""

    id: int
    device_id: int
    from_version: Optional[str] = None
    to_version: str
    firmware_file: Optional[str] = None
    status: str
    progress: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    rollback_performed: bool
    update_type: str
    triggered_by: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Firmware schemas
class ESPHomeFirmwareBase(BaseModel):
    """Base firmware schema."""

    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    platform: str = Field(..., pattern="^(esp32|esp8266|rp2040)$")
    board: Optional[str] = None
    esphome_version: str


class ESPHomeFirmwareCreate(ESPHomeFirmwareBase):
    """Create firmware request."""

    file_path: str
    config_used: Optional[str] = None
    is_stable: bool = False
    changelog: Optional[str] = None
    tags: Optional[List[str]] = None


class ESPHomeFirmwareResponse(ESPHomeFirmwareBase):
    """Firmware response."""

    id: int
    file_path: str
    file_size: int
    file_hash: str
    build_date: datetime
    config_used: Optional[str] = None
    is_active: bool
    is_stable: bool
    download_count: int
    changelog: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Log schemas
class ESPHomeLogResponse(BaseModel):
    """Log response."""

    id: int
    device_id: int
    level: str
    message: str
    component: Optional[str] = None
    device_timestamp: Optional[datetime] = None
    category: Optional[str] = None
    is_system: bool
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Discovery schemas
class ESPHomeDiscoveryRequest(BaseModel):
    """Discovery request."""

    timeout: int = Field(default=10, ge=1, le=60, description="Discovery timeout in seconds")


class ESPHomeDiscoveredDevice(BaseModel):
    """Discovered device."""

    name: str
    ip_address: str
    port: int
    mac_address: Optional[str] = None
    platform: Optional[str] = None
    esphome_version: Optional[str] = None


class ESPHomeDiscoveryResponse(BaseModel):
    """Discovery response."""

    devices: List[ESPHomeDiscoveredDevice]
    count: int


# Device status schemas
class ESPHomeDeviceStatus(BaseModel):
    """Device status."""

    device_id: int
    online: bool
    last_seen: Optional[datetime] = None
    connection_status: str
    uptime: Optional[int] = None  # seconds
    free_heap: Optional[int] = None  # bytes
    wifi_signal: Optional[int] = None  # dBm


# Bulk operation schemas
class ESPHomeBulkUpdateRequest(BaseModel):
    """Bulk update request."""

    device_ids: List[int] = Field(..., min_length=1)
    firmware_file: str
    password: Optional[str] = None
    sequential: bool = Field(
        default=True, description="Update devices one at a time or in parallel"
    )


class ESPHomeBulkUpdateResponse(BaseModel):
    """Bulk update response."""

    total: int
    started: List[int]
    failed: List[int]
    errors: dict


# Config validation schemas
class ESPHomeConfigValidateRequest(BaseModel):
    """Config validation request."""

    config: str = Field(..., description="YAML configuration content")
    platform: Optional[str] = None


class ESPHomeConfigValidateResponse(BaseModel):
    """Config validation response."""

    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    platform: Optional[str] = None
    esphome_version: Optional[str] = None


# Statistics schemas
class ESPHomeStatistics(BaseModel):
    """ESPHome statistics."""

    total_devices: int
    online_devices: int
    offline_devices: int
    devices_by_platform: dict
    total_updates: int
    successful_updates: int
    failed_updates: int
    average_update_time: Optional[float] = None  # seconds
