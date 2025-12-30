"""Tailscale network and device models."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TableNameMixin, TimestampMixin


class TailscaleNetwork(Base, TableNameMixin, TimestampMixin):
    """Tailscale network (tailnet) model."""

    __tablename__ = "tailscale_networks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Network info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tailnet: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)  # organization name

    # API credentials
    api_key: Mapped[str] = mapped_column(Text, nullable=False)  # Encrypted
    oauth_client_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    oauth_client_secret: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Encrypted

    # Network settings
    magic_dns_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    subnet_routing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    exit_node_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Network metadata
    device_count: Mapped[int] = mapped_column(Integer, default=0)
    user_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        """String representation."""
        return f"<TailscaleNetwork(id={self.id}, tailnet={self.tailnet})>"


class TailscaleDevice(Base, TableNameMixin, TimestampMixin):
    """Tailscale device model."""

    __tablename__ = "tailscale_devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Network association
    network_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Server association (optional - for HA servers)
    server_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Device identifiers
    device_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)  # Tailscale device ID
    node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Network addresses
    tailscale_ip: Mapped[str] = mapped_column(String(50), nullable=False)  # 100.x.x.x
    ipv6_address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dns_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # MagicDNS name

    # Device info
    os: Mapped[Optional[str]] = mapped_column(String(50))
    os_version: Mapped[Optional[str]] = mapped_column(String(100))
    client_version: Mapped[Optional[str]] = mapped_column(String(50))

    # User info
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Capabilities
    is_exit_node: Mapped[bool] = mapped_column(Boolean, default=False)
    is_subnet_router: Mapped[bool] = mapped_column(Boolean, default=False)
    advertised_routes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    allowed_ips: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Tags
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Full device data from API
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<TailscaleDevice(id={self.id}, hostname={self.hostname}, ip={self.tailscale_ip})>"


class TailscaleACL(Base, TableNameMixin, TimestampMixin):
    """Tailscale ACL (Access Control List) model."""

    __tablename__ = "tailscale_acls"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Network association
    network_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # ACL info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ACL rules (stored as JSON)
    rules: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Groups and tags
    groups: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tag_owners: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_applied: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<TailscaleACL(id={self.id}, name={self.name})>"


class TailscaleRoute(Base, TableNameMixin, TimestampMixin):
    """Tailscale subnet route model."""

    __tablename__ = "tailscale_routes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Device association
    device_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Route info
    subnet: Mapped[str] = mapped_column(String(50), nullable=False)  # CIDR notation
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<TailscaleRoute(id={self.id}, subnet={self.subnet})>"
