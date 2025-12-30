"""Snapshot model for backups."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TableNameMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.server import Server


class SnapshotType(str, enum.Enum):
    """Snapshot type enumeration."""

    MANUAL = "manual"
    AUTOMATIC = "automatic"
    PRE_DEPLOYMENT = "pre_deployment"
    SCHEDULED = "scheduled"


class SnapshotStatus(str, enum.Enum):
    """Snapshot status enumeration."""

    CREATING = "creating"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class Snapshot(Base, TableNameMixin, TimestampMixin):
    """Snapshot model for configuration backups."""

    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Relationships
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("servers.id"), nullable=False, index=True
    )
    server: Mapped["Server"] = relationship("Server", back_populates="snapshots")

    # Snapshot details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    snapshot_type: Mapped[SnapshotType] = mapped_column(
        Enum(SnapshotType), default=SnapshotType.MANUAL, nullable=False
    )
    status: Mapped[SnapshotStatus] = mapped_column(
        Enum(SnapshotStatus), default=SnapshotStatus.CREATING, nullable=False
    )

    # Storage
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=True)
    compressed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    encrypted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Content metadata
    file_count: Mapped[int] = mapped_column(Integer, nullable=True)
    includes_secrets: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    includes_database: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Versioning
    ha_version: Mapped[str] = mapped_column(String(50), nullable=True)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=True)

    # Associated deployment
    deployment_id: Mapped[int] = mapped_column(Integer, nullable=True)

    # Metadata
    meta_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=True)  # SHA256

    # Retention
    retention_days: Mapped[int] = mapped_column(Integer, nullable=True)
    auto_delete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Snapshot(id={self.id}, name={self.name}, server_id={self.server_id})>"

    @property
    def is_available(self) -> bool:
        """Check if snapshot is available for restore."""
        return self.status == SnapshotStatus.COMPLETED

    @property
    def size_mb(self) -> float:
        """Get size in megabytes."""
        if self.size_bytes is None:
            return 0.0
        return round(self.size_bytes / (1024 * 1024), 2)
