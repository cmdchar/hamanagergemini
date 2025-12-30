"""Falcon Player Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class FPPDeviceBase(BaseSchema):
    """Base FPP device schema."""

    name: str = Field(..., min_length=1, max_length=255)
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: str = Field(..., pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    port: int = Field(default=80, ge=1, le=65535)


class FPPDeviceCreate(FPPDeviceBase):
    """Schema for creating an FPP device."""

    server_id: Optional[int] = None
    version: Optional[str] = None
    platform: Optional[str] = None
    model: Optional[str] = None
    mode: Optional[str] = Field(default="player", pattern="^(player|remote|bridge)$")


class FPPDeviceUpdate(BaseSchema):
    """Schema for updating an FPP device."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    ip_address: Optional[str] = Field(None, pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    port: Optional[int] = Field(None, ge=1, le=65535)
    server_id: Optional[int] = None
    version: Optional[str] = None
    platform: Optional[str] = None
    model: Optional[str] = None
    mode: Optional[str] = Field(None, pattern="^(player|remote|bridge)$")
    volume: Optional[int] = Field(None, ge=0, le=100)
    brightness: Optional[int] = Field(None, ge=0, le=100)
    multisync_enabled: Optional[bool] = None
    multisync_master: Optional[bool] = None


class FPPDeviceResponse(FPPDeviceBase, TimestampSchema):
    """Schema for FPP device response."""

    id: int
    server_id: Optional[int] = None
    version: Optional[str] = None
    platform: Optional[str] = None
    model: Optional[str] = None
    mode: Optional[str] = None
    is_online: bool
    last_seen: Optional[datetime] = None
    status: Optional[str] = None
    current_playlist: Optional[str] = None
    current_sequence: Optional[str] = None
    seconds_played: int
    seconds_remaining: int
    capabilities: Optional[Dict[str, Any]] = None
    volume: int
    brightness: int
    multisync_enabled: bool
    multisync_master: bool
    multisync_peers: Optional[List[str]] = None


class FPPDiscoveryRequest(BaseSchema):
    """Schema for device discovery."""

    timeout: int = Field(default=5, ge=1, le=30)


class FPPDiscoveryResponse(BaseSchema):
    """Schema for discovery response."""

    devices_found: int
    devices: List[FPPDeviceResponse]


class FPPPlaylistBase(BaseSchema):
    """Base FPP playlist schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    device_id: int


class FPPPlaylistCreate(FPPPlaylistBase):
    """Schema for creating an FPP playlist."""

    entries: List[Dict[str, Any]] = Field(default_factory=list)
    repeat: bool = False
    shuffle: bool = False
    priority: int = Field(default=0, ge=0)


class FPPPlaylistUpdate(BaseSchema):
    """Schema for updating an FPP playlist."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    entries: Optional[List[Dict[str, Any]]] = None
    repeat: Optional[bool] = None
    shuffle: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)


class FPPPlaylistResponse(FPPPlaylistBase, TimestampSchema):
    """Schema for FPP playlist response."""

    id: int
    entries: List[Dict[str, Any]]
    repeat: bool
    shuffle: bool
    priority: int
    last_played: Optional[datetime] = None
    play_count: int


class FPPSequenceBase(BaseSchema):
    """Base FPP sequence schema."""

    name: str = Field(..., min_length=1, max_length=255)
    filename: str = Field(..., min_length=1, max_length=255)
    device_id: int


class FPPSequenceCreate(FPPSequenceBase):
    """Schema for creating an FPP sequence."""

    duration: int = Field(default=0, ge=0)
    channel_count: int = Field(default=0, ge=0)
    frame_count: int = Field(default=0, ge=0)
    file_size: int = Field(default=0, ge=0)
    media_filename: Optional[str] = None


class FPPSequenceUpdate(BaseSchema):
    """Schema for updating an FPP sequence."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    duration: Optional[int] = Field(None, ge=0)
    channel_count: Optional[int] = Field(None, ge=0)
    frame_count: Optional[int] = Field(None, ge=0)
    file_size: Optional[int] = Field(None, ge=0)
    media_filename: Optional[str] = None


class FPPSequenceResponse(FPPSequenceBase, TimestampSchema):
    """Schema for FPP sequence response."""

    id: int
    duration: int
    channel_count: int
    frame_count: int
    file_size: int
    media_filename: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    last_played: Optional[datetime] = None
    play_count: int


class FPPPlaylistControl(BaseSchema):
    """Schema for playlist control."""

    playlist_name: str = Field(..., min_length=1)
    repeat: bool = False


class FPPMultiSyncRequest(BaseSchema):
    """Schema for MultiSync configuration."""

    master_device_id: int
    peer_device_ids: List[int] = Field(..., min_length=1)


class FPPMultiSyncResponse(BaseSchema):
    """Schema for MultiSync response."""

    success: bool
    message: str
    master_device_id: int
    peer_count: int


class FPPVolumeControl(BaseSchema):
    """Schema for volume control."""

    volume: int = Field(..., ge=0, le=100)


class FPPStatusResponse(BaseSchema):
    """Schema for device status response."""

    status: str
    current_playlist: Optional[str] = None
    current_sequence: Optional[str] = None
    seconds_played: int
    seconds_remaining: int
    volume: int


class FPPSyncRequest(BaseSchema):
    """Schema for syncing playlists/sequences from device."""

    device_id: int
    sync_playlists: bool = True
    sync_sequences: bool = True


class FPPSyncResponse(BaseSchema):
    """Schema for sync response."""

    success: bool
    playlists_synced: int
    sequences_synced: int
