"""ESPHome device models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TableNameMixin, TimestampMixin


class ESPHomeDevice(Base, TableNameMixin, TimestampMixin):
    """ESPHome device model."""

    __tablename__ = "esphome_devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Server association
    server_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("servers.id"), nullable=True
    )

    # Device identification
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    friendly_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    device_class: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # sensor, switch, light, etc.

    # Network information
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False)
    mac_address: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    port: Mapped[int] = mapped_column(Integer, default=6053)  # ESPHome API port

    # Platform information
    platform: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # esp32, esp8266, etc.
    board: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Firmware information
    esphome_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    compilation_time: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Configuration
    config_file: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # YAML configuration
    config_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # SHA256 hash

    # OTA settings
    ota_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ota_password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Encrypted
    requires_encryption: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    connection_status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # connected, disconnected, error

    # Update information
    update_available: Mapped[bool] = mapped_column(Boolean, default=False)
    update_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    auto_update: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ESPHomeDevice(id={self.id}, name={self.name}, ip={self.ip_address})>"


class ESPHomeOTAUpdate(Base, TableNameMixin, TimestampMixin):
    """ESPHome OTA update history model."""

    __tablename__ = "esphome_ota_updates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Device association
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("esphome_devices.id"), nullable=False
    )

    # Update information
    from_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_version: Mapped[str] = mapped_column(String(50), nullable=False)
    firmware_file: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Path or URL to firmware

    # Update status
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending, uploading, installing, completed, failed
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Result
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rollback_performed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    update_type: Mapped[str] = mapped_column(
        String(50), default="ota"
    )  # ota, serial, web
    triggered_by: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # user, auto, scheduled
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ESPHomeOTAUpdate(id={self.id}, device_id={self.device_id}, status={self.status})>"


class ESPHomeFirmware(Base, TableNameMixin, TimestampMixin):
    """ESPHome firmware storage model."""

    __tablename__ = "esphome_firmwares"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Firmware information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Platform compatibility
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # esp32, esp8266
    board: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # File information
    file_path: Mapped[str] = mapped_column(Text, nullable=False)  # Local path or S3 URL
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Bytes
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256

    # Build information
    esphome_version: Mapped[str] = mapped_column(String(50), nullable=False)
    build_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    config_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_stable: Mapped[bool] = mapped_column(Boolean, default=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    changelog: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ESPHomeFirmware(id={self.id}, name={self.name}, version={self.version})>"


class ESPHomeLog(Base, TableNameMixin, TimestampMixin):
    """ESPHome device log model."""

    __tablename__ = "esphome_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Device association
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("esphome_devices.id"), nullable=False
    )

    # Log information
    level: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # debug, info, warning, error, critical
    message: Mapped[str] = mapped_column(Text, nullable=False)
    component: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamp from device
    device_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Categorization
    category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # boot, ota, wifi, sensor, etc.
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ESPHomeLog(id={self.id}, device_id={self.device_id}, level={self.level})>"
