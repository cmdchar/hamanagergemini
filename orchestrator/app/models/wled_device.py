"""WLED device model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TableNameMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.server import Server


class WLEDDevice(Base, TableNameMixin, TimestampMixin):
    """WLED device model."""

    __tablename__ = "wled_devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Device info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False)
    mac_address: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)

    # Server association
    server_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Device details
    version: Mapped[Optional[str]] = mapped_column(String(50))
    led_count: Mapped[int] = mapped_column(Integer, default=0)
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    product: Mapped[Optional[str]] = mapped_column(String(100))

    # Status
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Current state
    current_preset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    brightness: Mapped[int] = mapped_column(Integer, default=128)
    is_on: Mapped[bool] = mapped_column(Boolean, default=False)

    # Configuration stored as JSON
    presets: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    segments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Sync settings
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    sync_group: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sync_master: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<WLEDDevice(id={self.id}, name={self.name}, ip={self.ip_address})>"
