"""Falcon Player device model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TableNameMixin, TimestampMixin


class FPPDevice(Base, TableNameMixin, TimestampMixin):
    """Falcon Player device model."""

    __tablename__ = "fpp_devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Device info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=80)

    # Server association
    server_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Device details
    version: Mapped[Optional[str]] = mapped_column(String(50))
    platform: Mapped[Optional[str]] = mapped_column(String(100))  # RPi, BBB, etc.
    model: Mapped[Optional[str]] = mapped_column(String(100))
    mode: Mapped[Optional[str]] = mapped_column(String(50))  # player, remote, bridge

    # Status
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Current state
    status: Mapped[Optional[str]] = mapped_column(String(50))  # idle, playing, paused
    current_playlist: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_sequence: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seconds_played: Mapped[int] = mapped_column(Integer, default=0)
    seconds_remaining: Mapped[int] = mapped_column(Integer, default=0)

    # Capabilities stored as JSON
    capabilities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # FPP-specific settings
    volume: Mapped[int] = mapped_column(Integer, default=75)  # 0-100
    brightness: Mapped[int] = mapped_column(Integer, default=100)  # 0-100

    # Multisync settings
    multisync_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    multisync_master: Mapped[bool] = mapped_column(Boolean, default=False)
    multisync_peers: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<FPPDevice(id={self.id}, name={self.name}, ip={self.ip_address})>"


class FPPPlaylist(Base, TableNameMixin, TimestampMixin):
    """FPP playlist model."""

    __tablename__ = "fpp_playlists"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Playlist info
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Associated device
    device_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Playlist content (JSON array of entries)
    entries: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Playlist settings
    repeat: Mapped[bool] = mapped_column(Boolean, default=False)
    shuffle: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    last_played: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    play_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        """String representation."""
        return f"<FPPPlaylist(id={self.id}, name={self.name}, device_id={self.device_id})>"


class FPPSequence(Base, TableNameMixin, TimestampMixin):
    """FPP sequence model."""

    __tablename__ = "fpp_sequences"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Sequence info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # Associated device
    device_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Sequence details
    duration: Mapped[int] = mapped_column(Integer, default=0)  # seconds
    channel_count: Mapped[int] = mapped_column(Integer, default=0)
    frame_count: Mapped[int] = mapped_column(Integer, default=0)
    file_size: Mapped[int] = mapped_column(Integer, default=0)  # bytes

    # Media file association
    media_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Metadata
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_played: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    play_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        """String representation."""
        return f"<FPPSequence(id={self.id}, name={self.name}, device_id={self.device_id})>"
