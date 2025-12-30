"""Backup models for Node-RED and Zigbee2MQTT."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TableNameMixin, TimestampMixin


class Backup(Base, TableNameMixin, TimestampMixin):
    """Backup model for various integrations."""

    __tablename__ = "backups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Server/Deployment association
    server_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("servers.id"), nullable=True
    )
    deployment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("deployments.id"), nullable=True
    )

    # Backup information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    backup_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # nodered, zigbee2mqtt, ha_config, full, etc.

    # Storage information
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)  # Local path or S3 URL
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Bytes
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # SHA256 hash
    compression: Mapped[str] = mapped_column(
        String(20), default="gzip"
    )  # gzip, zip, tar, none

    # Backup source
    source_host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_version: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Version of Node-RED/Zigbee2MQTT

    # Backup metadata
    backup_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    retention_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Auto-delete after N days
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="completed"
    )  # pending, in_progress, completed, failed
    verified: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # Hash verified after backup
    encrypted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Backup contents metadata
    items_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Number of flows, devices, etc.
    content_summary: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Summary of what was backed up

    # Automatic backup
    is_automatic: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("backup_schedules.id"), nullable=True
    )

    # Tags and metadata
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Backup(id={self.id}, type={self.backup_type}, name={self.name})>"


class BackupSchedule(Base, TableNameMixin, TimestampMixin):
    """Backup schedule model."""

    __tablename__ = "backup_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Association
    server_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("servers.id"), nullable=True
    )
    deployment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("deployments.id"), nullable=True
    )

    # Schedule information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    backup_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # nodered, zigbee2mqtt, etc.

    # Schedule configuration
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    cron_expression: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "0 2 * * *" for daily at 2 AM
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")

    # Retention policy
    retention_days: Mapped[int] = mapped_column(Integer, default=30)
    max_backups: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Keep only N most recent

    # Execution tracking
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)

    # Storage configuration
    storage_location: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Base path for backups
    compression: Mapped[str] = mapped_column(String(20), default="gzip")
    encrypt: Mapped[bool] = mapped_column(Boolean, default=False)

    # Notification settings
    notify_on_success: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_on_failure: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_emails: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Metadata
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<BackupSchedule(id={self.id}, name={self.name}, type={self.backup_type})>"


class BackupRestore(Base, TableNameMixin, TimestampMixin):
    """Backup restore operation model."""

    __tablename__ = "backup_restores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Backup reference
    backup_id: Mapped[int] = mapped_column(Integer, ForeignKey("backups.id"), nullable=False)

    # Restore target
    server_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("servers.id"), nullable=True
    )
    deployment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("deployments.id"), nullable=True
    )
    target_host: Mapped[str] = mapped_column(String(255), nullable=False)
    target_path: Mapped[str] = mapped_column(Text, nullable=False)

    # Restore options
    overwrite_existing: Mapped[bool] = mapped_column(Boolean, default=False)
    create_backup_before: Mapped[bool] = mapped_column(
        Boolean, default=True
    )  # Backup current before restore
    restore_all: Mapped[bool] = mapped_column(
        Boolean, default=True
    )  # Or selective restore
    selected_items: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # Specific flows/devices to restore

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending, in_progress, completed, failed, rolled_back
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Result
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    items_restored: Mapped[int] = mapped_column(Integer, default=0)
    items_failed: Mapped[int] = mapped_column(Integer, default=0)

    # Rollback
    rollback_backup_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Backup created before restore
    can_rollback: Mapped[bool] = mapped_column(Boolean, default=False)
    rolled_back: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    restore_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<BackupRestore(id={self.id}, backup_id={self.backup_id}, status={self.status})>"


class NodeREDConfig(Base, TableNameMixin, TimestampMixin):
    """Node-RED configuration tracking."""

    __tablename__ = "nodered_configs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Server association
    server_id: Mapped[int] = mapped_column(Integer, ForeignKey("servers.id"), nullable=False)

    # Node-RED instance info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Encrypted
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # File paths
    flows_file: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Path to flows.json
    settings_file: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_dir: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_backup: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    flows_count: Mapped[int] = mapped_column(Integer, default=0)
    nodes_count: Mapped[int] = mapped_column(Integer, default=0)

    # Auto-backup settings
    auto_backup_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    backup_on_deploy: Mapped[bool] = mapped_column(
        Boolean, default=True
    )  # Backup when flows are deployed

    # Metadata
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<NodeREDConfig(id={self.id}, name={self.name})>"


class Zigbee2MQTTConfig(Base, TableNameMixin, TimestampMixin):
    """Zigbee2MQTT configuration tracking."""

    __tablename__ = "zigbee2mqtt_configs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Server association
    server_id: Mapped[int] = mapped_column(Integer, ForeignKey("servers.id"), nullable=False)

    # Zigbee2MQTT instance info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mqtt_server: Mapped[str] = mapped_column(String(255), nullable=False)
    mqtt_base_topic: Mapped[str] = mapped_column(String(100), default="zigbee2mqtt")
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # File paths
    data_dir: Mapped[str] = mapped_column(Text, nullable=False)  # Zigbee2MQTT data directory
    config_file: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # configuration.yaml
    devices_file: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # devices.yaml
    groups_file: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # groups.yaml
    coordinator_backup: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Coordinator backup file

    # Status
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_backup: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    devices_count: Mapped[int] = mapped_column(Integer, default=0)
    groups_count: Mapped[int] = mapped_column(Integer, default=0)

    # Auto-backup settings
    auto_backup_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    backup_coordinator: Mapped[bool] = mapped_column(
        Boolean, default=True
    )  # Include Zigbee coordinator backup

    # Metadata
    coordinator_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # e.g., "ConBee II", "CC2652"
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Zigbee2MQTTConfig(id={self.id}, name={self.name})>"
