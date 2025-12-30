"""Tailscale Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class TailscaleNetworkBase(BaseSchema):
    """Base Tailscale network schema."""

    name: str = Field(..., min_length=1, max_length=255)
    tailnet: str = Field(..., min_length=1, max_length=255)


class TailscaleNetworkCreate(TailscaleNetworkBase):
    """Schema for creating a Tailscale network."""

    api_key: str = Field(..., min_length=1)
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    magic_dns_enabled: bool = True
    subnet_routing_enabled: bool = False
    exit_node_enabled: bool = False


class TailscaleNetworkUpdate(BaseSchema):
    """Schema for updating a Tailscale network."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    api_key: Optional[str] = Field(None, min_length=1)
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    magic_dns_enabled: Optional[bool] = None
    subnet_routing_enabled: Optional[bool] = None
    exit_node_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class TailscaleNetworkResponse(TailscaleNetworkBase, TimestampSchema):
    """Schema for Tailscale network response."""

    id: int
    magic_dns_enabled: bool
    subnet_routing_enabled: bool
    exit_node_enabled: bool
    is_active: bool
    last_synced: Optional[datetime] = None
    device_count: int
    user_count: int


class TailscaleDeviceBase(BaseSchema):
    """Base Tailscale device schema."""

    hostname: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)


class TailscaleDeviceResponse(TimestampSchema):
    """Schema for Tailscale device response."""

    id: int
    network_id: int
    server_id: Optional[int] = None
    device_id: str
    node_id: str
    hostname: str
    name: str
    tailscale_ip: str
    ipv6_address: Optional[str] = None
    dns_name: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    client_version: Optional[str] = None
    user_email: Optional[str] = None
    user_display_name: Optional[str] = None
    is_online: bool
    last_seen: Optional[datetime] = None
    expires: Optional[datetime] = None
    is_exit_node: bool
    is_subnet_router: bool
    advertised_routes: Optional[List[str]] = None
    allowed_ips: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class TailscaleSyncRequest(BaseSchema):
    """Schema for syncing devices."""

    network_id: int


class TailscaleSyncResponse(BaseSchema):
    """Schema for sync response."""

    success: bool
    devices_synced: int
    message: str


class TailscaleDeviceDelete(BaseSchema):
    """Schema for deleting a device."""

    device_id: str


class TailscaleDeviceAuthorize(BaseSchema):
    """Schema for authorizing a device."""

    device_id: str


class TailscaleDeviceTags(BaseSchema):
    """Schema for setting device tags."""

    device_id: str
    tags: List[str] = Field(..., min_length=1)


class TailscaleRouteEnable(BaseSchema):
    """Schema for enabling a route."""

    device_id: str
    subnet: str = Field(..., pattern=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$")


class TailscaleACLBase(BaseSchema):
    """Base Tailscale ACL schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    network_id: int


class TailscaleACLCreate(TailscaleACLBase):
    """Schema for creating an ACL."""

    rules: Dict[str, Any]
    groups: Optional[Dict[str, Any]] = None
    tag_owners: Optional[Dict[str, Any]] = None


class TailscaleACLUpdate(BaseSchema):
    """Schema for updating an ACL."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None
    groups: Optional[Dict[str, Any]] = None
    tag_owners: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class TailscaleACLResponse(TailscaleACLBase, TimestampSchema):
    """Schema for ACL response."""

    id: int
    rules: Dict[str, Any]
    groups: Optional[Dict[str, Any]] = None
    tag_owners: Optional[Dict[str, Any]] = None
    is_active: bool
    last_applied: Optional[datetime] = None


class TailscaleACLPolicy(BaseSchema):
    """Schema for ACL policy."""

    acls: List[Dict[str, Any]]
    groups: Optional[Dict[str, List[str]]] = None
    tagOwners: Optional[Dict[str, List[str]]] = None


class TailscaleDNSConfig(BaseSchema):
    """Schema for DNS configuration."""

    nameservers: List[str] = Field(..., min_length=1)


class TailscaleDNSResponse(BaseSchema):
    """Schema for DNS response."""

    dns: List[str]
    magic_dns: bool
    magic_dns_suffix: Optional[str] = None


class TailscaleRouteBase(BaseSchema):
    """Base Tailscale route schema."""

    device_id: int
    subnet: str = Field(..., pattern=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$")
    description: Optional[str] = None


class TailscaleRouteCreate(TailscaleRouteBase):
    """Schema for creating a route."""

    is_enabled: bool = False
    is_primary: bool = False


class TailscaleRouteUpdate(BaseSchema):
    """Schema for updating a route."""

    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_primary: Optional[bool] = None


class TailscaleRouteResponse(TailscaleRouteBase, TimestampSchema):
    """Schema for route response."""

    id: int
    is_enabled: bool
    is_primary: bool


class TailscaleNetworkStats(BaseSchema):
    """Schema for network statistics."""

    total_devices: int
    online_devices: int
    offline_devices: int
    exit_nodes: int
    subnet_routers: int
    total_routes: int
    enabled_routes: int
