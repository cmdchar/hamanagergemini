"""WLED schedule model."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TableNameMixin, TimestampMixin


class WLEDSchedule(Base, TableNameMixin, TimestampMixin):
    """WLED schedule model for automated light shows."""

    __tablename__ = "wled_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Schedule info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Target devices (either specific devices or sync group)
    device_ids: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)
    sync_group: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Cron schedule
    cron_expression: Mapped[str] = mapped_column(String(255), nullable=False)

    # Action to perform
    preset_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Schedule control
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Execution tracking
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        """String representation."""
        return f"<WLEDSchedule(id={self.id}, name={self.name}, cron={self.cron_expression})>"
