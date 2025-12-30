"""WLED device Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema, TimestampSchema


class WLEDDeviceBase(BaseSchema):
    """Base WLED device schema."""

    name: str = Field(..., min_length=1, max_length=255)
    ip_address: str = Field(..., pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")


class WLEDDeviceCreate(WLEDDeviceBase):
    """Schema for creating a WLED device."""

    mac_address: Optional[str] = Field(None, max_length=20)
    server_id: Optional[int] = None
    version: Optional[str] = None
    led_count: int = Field(default=0, ge=0)
    brand: Optional[str] = None
    product: Optional[str] = None


class WLEDDeviceUpdate(BaseSchema):
    """Schema for updating a WLED device."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    ip_address: Optional[str] = Field(None, pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    server_id: Optional[int] = None
    version: Optional[str] = None
    led_count: Optional[int] = Field(None, ge=0)
    brand: Optional[str] = None
    product: Optional[str] = None
    is_online: Optional[bool] = None
    current_preset: Optional[int] = None
    brightness: Optional[int] = Field(None, ge=0, le=255)
    is_on: Optional[bool] = None
    presets: Optional[Dict[str, Any]] = None
    segments: Optional[Dict[str, Any]] = None
    sync_enabled: Optional[bool] = None
    sync_group: Optional[str] = None
    sync_master: Optional[bool] = None


class WLEDDeviceResponse(WLEDDeviceBase, TimestampSchema):
    """Schema for WLED device response."""

    id: int
    mac_address: Optional[str] = None
    server_id: Optional[int] = None
    version: Optional[str] = None
    led_count: int
    brand: Optional[str] = None
    product: Optional[str] = None
    is_online: bool
    last_seen: Optional[datetime] = None
    current_preset: Optional[int] = None
    brightness: int
    is_on: bool
    presets: Optional[Dict[str, Any]] = None
    segments: Optional[Dict[str, Any]] = None
    sync_enabled: bool
    sync_group: Optional[str] = None
    sync_master: bool


class WLEDDeviceState(BaseSchema):
    """Schema for WLED device state."""

    on: Optional[bool] = None
    bri: Optional[int] = Field(None, ge=0, le=255)  # Brightness
    ps: Optional[int] = Field(None, ge=-1, le=250)  # Preset ID (-1 for none)
    pl: Optional[int] = Field(None, ge=-1, le=250)  # Playlist ID
    nl: Optional[Dict[str, Any]] = None  # Nightlight settings
    udpn: Optional[Dict[str, Any]] = None  # UDP settings
    seg: Optional[List[Dict[str, Any]]] = None  # Segments


class WLEDPresetCreate(BaseSchema):
    """Schema for creating a WLED preset."""

    device_id: int
    preset_id: int = Field(..., ge=1, le=250)
    name: str = Field(..., min_length=1, max_length=100)
    state: WLEDDeviceState
    quick_label: Optional[str] = Field(None, max_length=2)


class WLEDPresetResponse(BaseSchema):
    """Schema for WLED preset response."""

    device_id: int
    preset_id: int
    name: str
    state: Dict[str, Any]
    quick_label: Optional[str] = None


class WLEDSyncRequest(BaseSchema):
    """Schema for syncing WLED devices."""

    device_ids: List[int] = Field(..., min_length=2)
    sync_group: str = Field(default="christmas", max_length=50)


class WLEDSyncResponse(BaseSchema):
    """Schema for sync response."""

    success: bool
    message: str
    synced_devices: int
    master_device_id: int


class WLEDDiscoveryRequest(BaseSchema):
    """Schema for device discovery."""

    timeout: int = Field(default=5, ge=1, le=30)


class WLEDDiscoveryResponse(BaseSchema):
    """Schema for discovery response."""

    devices_found: int
    devices: List[WLEDDeviceResponse]


class WLEDBulkStateUpdate(BaseSchema):
    """Schema for bulk state update."""

    device_ids: Optional[List[int]] = None
    sync_group: Optional[str] = None
    state: WLEDDeviceState


class WLEDBulkStateResponse(BaseSchema):
    """Schema for bulk state response."""

    success: bool
    devices_updated: int
    errors: List[str] = Field(default_factory=list)


class WLEDScheduleCreate(BaseSchema):
    """Schema for creating a WLED schedule."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    device_ids: Optional[List[int]] = None
    sync_group: Optional[str] = None
    cron_expression: str = Field(..., min_length=1)
    preset_id: Optional[int] = Field(None, ge=1, le=250)
    state: Optional[WLEDDeviceState] = None
    enabled: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class WLEDScheduleUpdate(BaseSchema):
    """Schema for updating a WLED schedule."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    device_ids: Optional[List[int]] = None
    sync_group: Optional[str] = None
    cron_expression: Optional[str] = None
    preset_id: Optional[int] = Field(None, ge=1, le=250)
    state: Optional[WLEDDeviceState] = None
    enabled: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class WLEDScheduleResponse(TimestampSchema):
    """Schema for WLED schedule response."""

    id: int
    name: str
    description: Optional[str] = None
    device_ids: Optional[List[int]] = None
    sync_group: Optional[str] = None
    cron_expression: str
    preset_id: Optional[int] = None
    state: Optional[Dict[str, Any]] = None
    enabled: bool
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int
