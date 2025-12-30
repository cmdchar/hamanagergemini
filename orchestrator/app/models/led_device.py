"""LED device models (WLED, FPP)."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TableNameMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.server import Server


class LEDDeviceType(str, enum.Enum):
    """LED device type enumeration."""

    WLED = "wled"
    FPP = "fpp"
    ESPixelStick = "espixelstick"
    QUINLED = "quinled"
    OTHER = "other"


class LEDDeviceStatus(str, enum.Enum):
    """LED device status enumeration."""

    ONLINE = "online"
    OFFLINE = "offline"
    UPDATING = "updating"
    ERROR = "error"


class LEDDevice(Base, TableNameMixin, TimestampMixin):
    """LED device model for WLED, FPP, and other LED controllers."""

    __tablename__ = "led_devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Relationships
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("servers.id"), nullable=True, index=True
    )
    server: Mapped["Server"] = relationship("Server", back_populates="led_devices")

    # Device details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[LEDDeviceType] = mapped_column(
        Enum(LEDDeviceType), default=LEDDeviceType.WLED, nullable=False
    )
    status: Mapped[LEDDeviceStatus] = mapped_column(
        Enum(LEDDeviceStatus), default=LEDDeviceStatus.OFFLINE, nullable=False
    )

    # Network details
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    mac_address: Mapped[str] = mapped_column(String(17), nullable=True, unique=True)

    # mDNS discovery
    mdns_name: Mapped[str] = mapped_column(String(255), nullable=True)
    discovered_via_mdns: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Device info
    version: Mapped[str] = mapped_column(String(50), nullable=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=True)
    model: Mapped[str] = mapped_column(String(100), nullable=True)
    chip_type: Mapped[str] = mapped_column(String(50), nullable=True)

    # LED configuration
    led_count: Mapped[int] = mapped_column(Integer, nullable=True)
    segments: Mapped[int] = mapped_column(Integer, nullable=True)
    color_order: Mapped[str] = mapped_column(String(10), nullable=True)
    max_current_ma: Mapped[int] = mapped_column(Integer, nullable=True)

    # WLED specific
    wled_presets: Mapped[dict] = mapped_column(JSON, nullable=True)
    wled_palettes: Mapped[list] = mapped_column(JSON, nullable=True)

    # FPP specific
    fpp_mode: Mapped[str] = mapped_column(String(50), nullable=True)  # player/remote
    fpp_playlists: Mapped[list] = mapped_column(JSON, nullable=True)
    fpp_sequences: Mapped[list] = mapped_column(JSON, nullable=True)
    fpp_multisync_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Settings
    auto_discover: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_backup: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Metadata
    description: Mapped[str] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=True)
    meta_data: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Last sync
    last_seen: Mapped[str] = mapped_column(String(50), nullable=True)
    last_backup: Mapped[str] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<LEDDevice(id={self.id}, name={self.name}, type={self.device_type})>"

    @property
    def is_online(self) -> bool:
        """Check if device is online."""
        return self.status == LEDDeviceStatus.ONLINE

    @property
    def is_wled(self) -> bool:
        """Check if device is WLED."""
        return self.device_type == LEDDeviceType.WLED

    @property
    def is_fpp(self) -> bool:
        """Check if device is FPP."""
        return self.device_type == LEDDeviceType.FPP
