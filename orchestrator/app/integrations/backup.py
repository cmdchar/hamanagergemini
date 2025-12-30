"""Backup and restore integration service."""

import asyncio
import gzip
import hashlib
import json
import logging
import os
import shutil
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backup import (
    Backup,
    BackupRestore,
    BackupSchedule,
    NodeREDConfig,
    Zigbee2MQTTConfig,
)
from app.utils.logging import log_integration_event

logger = logging.getLogger(__name__)


class BackupService:
    """Service for backup and restore operations."""

    def __init__(self, db: AsyncSession, storage_base_path: str = "/var/backups/ha-config-manager"):
        """
        Initialize backup service.

        Args:
            db: Database session
            storage_base_path: Base path for storing backups
        """
        self.db = db
        self.storage_base_path = Path(storage_base_path)
        self.storage_base_path.mkdir(parents=True, exist_ok=True)

    async def create_nodered_backup(
        self, config_id: int, name: Optional[str] = None, description: Optional[str] = None
    ) -> Optional[Backup]:
        """
        Create backup of Node-RED flows.

        Args:
            config_id: Node-RED configuration ID
            name: Backup name
            description: Backup description

        Returns:
            Optional[Backup]: Created backup record
        """
        try:
            # Get Node-RED configuration
            result = await self.db.execute(
                select(NodeREDConfig).where(NodeREDConfig.id == config_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                logger.error(f"Node-RED config {config_id} not found")
                return None

            # Create backup directory
            backup_dir = self.storage_base_path / "nodered" / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup flows file
            flows_backup_path = backup_dir / "flows.json"

            # Check if flows file exists
            flows_file = Path(config.flows_file)
            if not flows_file.exists():
                logger.error(f"Flows file not found: {config.flows_file}")
                return None

            # Copy flows file
            shutil.copy2(flows_file, flows_backup_path)

            # Backup settings if exists
            if config.settings_file and Path(config.settings_file).exists():
                settings_backup_path = backup_dir / "settings.js"
                shutil.copy2(config.settings_file, settings_backup_path)

            # Parse flows to get metadata
            async with aiofiles.open(flows_backup_path, "r") as f:
                flows_content = await f.read()
                flows_data = json.loads(flows_content)

            flows_count = len([f for f in flows_data if f.get("type") == "tab"])
            nodes_count = len(flows_data)

            # Create compressed archive
            archive_path = backup_dir.parent / f"{backup_dir.name}.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(backup_dir, arcname=backup_dir.name)

            # Clean up uncompressed directory
            shutil.rmtree(backup_dir)

            # Calculate file hash
            file_hash = await self._calculate_file_hash(archive_path)
            file_size = archive_path.stat().st_size

            # Create backup record
            backup = Backup(
                name=name or f"Node-RED Backup {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                description=description,
                backup_type="nodered",
                storage_path=str(archive_path),
                file_size=file_size,
                file_hash=file_hash,
                compression="gzip",
                source_host=config.base_url,
                source_path=config.flows_file,
                source_version=config.version,
                backup_date=datetime.utcnow(),
                status="completed",
                verified=True,
                items_count=flows_count,
                content_summary={
                    "flows_count": flows_count,
                    "nodes_count": nodes_count,
                },
            )

            self.db.add(backup)
            await self.db.commit()
            await self.db.refresh(backup)

            # Update config last backup time
            config.last_backup = datetime.utcnow()
            config.flows_count = flows_count
            config.nodes_count = nodes_count
            await self.db.commit()

            log_integration_event(
                "Backup",
                "nodered_backup_created",
                True,
                {"backup_id": backup.id, "config_id": config_id},
            )

            return backup

        except Exception as e:
            logger.exception(f"Failed to create Node-RED backup: {e}")
            log_integration_event(
                "Backup", "nodered_backup_created", False, {"error": str(e)}
            )
            return None

    async def create_zigbee2mqtt_backup(
        self, config_id: int, name: Optional[str] = None, description: Optional[str] = None
    ) -> Optional[Backup]:
        """
        Create backup of Zigbee2MQTT configuration.

        Args:
            config_id: Zigbee2MQTT configuration ID
            name: Backup name
            description: Backup description

        Returns:
            Optional[Backup]: Created backup record
        """
        try:
            # Get Zigbee2MQTT configuration
            result = await self.db.execute(
                select(Zigbee2MQTTConfig).where(Zigbee2MQTTConfig.id == config_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                logger.error(f"Zigbee2MQTT config {config_id} not found")
                return None

            # Create backup directory
            backup_dir = self.storage_base_path / "zigbee2mqtt" / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup configuration file
            if Path(config.config_file).exists():
                shutil.copy2(config.config_file, backup_dir / "configuration.yaml")

            # Backup devices file
            devices_count = 0
            if config.devices_file and Path(config.devices_file).exists():
                shutil.copy2(config.devices_file, backup_dir / "devices.yaml")
                # Count devices
                async with aiofiles.open(config.devices_file, "r") as f:
                    devices_content = await f.read()
                    # Simple count - would need YAML parsing for accuracy
                    devices_count = devices_content.count("friendly_name:")

            # Backup groups file
            groups_count = 0
            if config.groups_file and Path(config.groups_file).exists():
                shutil.copy2(config.groups_file, backup_dir / "groups.yaml")
                async with aiofiles.open(config.groups_file, "r") as f:
                    groups_content = await f.read()
                    groups_count = groups_content.count("friendly_name:")

            # Backup coordinator backup if exists
            if config.coordinator_backup and Path(config.coordinator_backup).exists():
                shutil.copy2(
                    config.coordinator_backup,
                    backup_dir / Path(config.coordinator_backup).name,
                )

            # Create compressed archive
            archive_path = backup_dir.parent / f"{backup_dir.name}.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(backup_dir, arcname=backup_dir.name)

            # Clean up uncompressed directory
            shutil.rmtree(backup_dir)

            # Calculate file hash
            file_hash = await self._calculate_file_hash(archive_path)
            file_size = archive_path.stat().st_size

            # Create backup record
            backup = Backup(
                name=name or f"Zigbee2MQTT Backup {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                description=description,
                backup_type="zigbee2mqtt",
                storage_path=str(archive_path),
                file_size=file_size,
                file_hash=file_hash,
                compression="gzip",
                source_host=config.mqtt_server,
                source_path=config.data_dir,
                source_version=config.version,
                backup_date=datetime.utcnow(),
                status="completed",
                verified=True,
                items_count=devices_count + groups_count,
                content_summary={
                    "devices_count": devices_count,
                    "groups_count": groups_count,
                    "coordinator_backup": config.coordinator_backup is not None,
                },
            )

            self.db.add(backup)
            await self.db.commit()
            await self.db.refresh(backup)

            # Update config last backup time
            config.last_backup = datetime.utcnow()
            config.devices_count = devices_count
            config.groups_count = groups_count
            await self.db.commit()

            log_integration_event(
                "Backup",
                "zigbee2mqtt_backup_created",
                True,
                {"backup_id": backup.id, "config_id": config_id},
            )

            return backup

        except Exception as e:
            logger.exception(f"Failed to create Zigbee2MQTT backup: {e}")
            log_integration_event(
                "Backup", "zigbee2mqtt_backup_created", False, {"error": str(e)}
            )
            return None

    async def restore_backup(
        self,
        backup_id: int,
        target_host: str,
        target_path: str,
        overwrite: bool = False,
        create_backup_before: bool = True,
    ) -> Optional[BackupRestore]:
        """
        Restore a backup.

        Args:
            backup_id: Backup ID to restore
            target_host: Target host
            target_path: Target path to restore to
            overwrite: Overwrite existing files
            create_backup_before: Create backup before restoring

        Returns:
            Optional[BackupRestore]: Restore operation record
        """
        try:
            # Get backup
            result = await self.db.execute(
                select(Backup).where(Backup.id == backup_id)
            )
            backup = result.scalar_one_or_none()

            if not backup:
                logger.error(f"Backup {backup_id} not found")
                return None

            # Create restore record
            restore = BackupRestore(
                backup_id=backup_id,
                target_host=target_host,
                target_path=target_path,
                overwrite_existing=overwrite,
                create_backup_before=create_backup_before,
                status="in_progress",
                started_at=datetime.utcnow(),
            )
            self.db.add(restore)
            await self.db.commit()
            await self.db.refresh(restore)

            # Create backup before restore if requested
            rollback_backup_id = None
            if create_backup_before and Path(target_path).exists():
                # Create a backup of current state for rollback
                # This would need to be implemented based on backup type
                pass

            # Extract archive
            archive_path = Path(backup.storage_path)
            if not archive_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup.storage_path}")

            extract_dir = Path(target_path).parent / f"restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            extract_dir.mkdir(parents=True, exist_ok=True)

            # Extract based on compression
            if backup.compression == "gzip":
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(extract_dir)
            else:
                raise ValueError(f"Unsupported compression: {backup.compression}")

            # Move files to target location
            extracted_content = list(extract_dir.iterdir())
            if len(extracted_content) == 1 and extracted_content[0].is_dir():
                source_dir = extracted_content[0]
            else:
                source_dir = extract_dir

            # Copy files to target
            items_restored = 0
            items_failed = 0

            for item in source_dir.iterdir():
                try:
                    target_item = Path(target_path) / item.name
                    if target_item.exists() and not overwrite:
                        logger.warning(f"Skipping existing file: {target_item}")
                        items_failed += 1
                        continue

                    if item.is_file():
                        shutil.copy2(item, target_item)
                    else:
                        shutil.copytree(item, target_item, dirs_exist_ok=overwrite)

                    items_restored += 1
                except Exception as e:
                    logger.error(f"Failed to restore {item}: {e}")
                    items_failed += 1

            # Clean up extraction directory
            shutil.rmtree(extract_dir)

            # Update restore record
            restore.status = "completed"
            restore.success = items_failed == 0
            restore.completed_at = datetime.utcnow()
            restore.duration_seconds = int(
                (restore.completed_at - restore.started_at).total_seconds()
            )
            restore.items_restored = items_restored
            restore.items_failed = items_failed
            restore.rollback_backup_id = rollback_backup_id
            restore.can_rollback = rollback_backup_id is not None

            await self.db.commit()

            log_integration_event(
                "Backup",
                "backup_restored",
                restore.success,
                {
                    "backup_id": backup_id,
                    "restore_id": restore.id,
                    "items_restored": items_restored,
                },
            )

            return restore

        except Exception as e:
            logger.exception(f"Failed to restore backup: {e}")
            # Update restore record with error
            if restore:
                restore.status = "failed"
                restore.error_message = str(e)
                restore.completed_at = datetime.utcnow()
                await self.db.commit()
            return None

    async def cleanup_old_backups(
        self, retention_days: Optional[int] = None, max_backups: Optional[int] = None
    ) -> int:
        """
        Clean up old backups based on retention policy.

        Args:
            retention_days: Delete backups older than N days
            max_backups: Keep only N most recent backups

        Returns:
            int: Number of backups deleted
        """
        try:
            deleted_count = 0

            # Delete backups older than retention period
            if retention_days:
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                result = await self.db.execute(
                    select(Backup).where(
                        Backup.backup_date < cutoff_date,
                        Backup.retention_days.is_not(None),
                        Backup.retention_days <= retention_days,
                    )
                )
                old_backups = list(result.scalars().all())

                for backup in old_backups:
                    # Delete file
                    try:
                        Path(backup.storage_path).unlink(missing_ok=True)
                    except Exception as e:
                        logger.error(f"Failed to delete backup file: {e}")

                    # Delete record
                    await self.db.delete(backup)
                    deleted_count += 1

            # Keep only max_backups most recent
            if max_backups:
                # Get backups ordered by date
                result = await self.db.execute(
                    select(Backup).order_by(Backup.backup_date.desc())
                )
                all_backups = list(result.scalars().all())

                if len(all_backups) > max_backups:
                    backups_to_delete = all_backups[max_backups:]
                    for backup in backups_to_delete:
                        try:
                            Path(backup.storage_path).unlink(missing_ok=True)
                        except Exception as e:
                            logger.error(f"Failed to delete backup file: {e}")

                        await self.db.delete(backup)
                        deleted_count += 1

            await self.db.commit()

            log_integration_event(
                "Backup",
                "cleanup_completed",
                True,
                {"deleted_count": deleted_count},
            )

            return deleted_count

        except Exception as e:
            logger.exception(f"Failed to cleanup old backups: {e}")
            return 0

    async def verify_backup(self, backup_id: int) -> bool:
        """
        Verify backup integrity by checking file hash.

        Args:
            backup_id: Backup ID

        Returns:
            bool: True if backup is valid
        """
        try:
            result = await self.db.execute(
                select(Backup).where(Backup.id == backup_id)
            )
            backup = result.scalar_one_or_none()

            if not backup:
                return False

            # Check if file exists
            if not Path(backup.storage_path).exists():
                logger.error(f"Backup file not found: {backup.storage_path}")
                return False

            # Calculate current hash
            current_hash = await self._calculate_file_hash(Path(backup.storage_path))

            # Compare with stored hash
            if current_hash == backup.file_hash:
                backup.verified = True
                await self.db.commit()
                return True
            else:
                logger.error(f"Backup hash mismatch for backup {backup_id}")
                return False

        except Exception as e:
            logger.exception(f"Failed to verify backup: {e}")
            return False

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of file.

        Args:
            file_path: Path to file

        Returns:
            str: SHA256 hash
        """
        sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def get_backup_info(self, backup_id: int) -> Optional[Dict]:
        """
        Get detailed backup information.

        Args:
            backup_id: Backup ID

        Returns:
            Optional[Dict]: Backup details
        """
        try:
            result = await self.db.execute(
                select(Backup).where(Backup.id == backup_id)
            )
            backup = result.scalar_one_or_none()

            if not backup:
                return None

            return {
                "id": backup.id,
                "name": backup.name,
                "type": backup.backup_type,
                "size": backup.file_size,
                "date": backup.backup_date,
                "verified": backup.verified,
                "items_count": backup.items_count,
                "content_summary": backup.content_summary,
            }

        except Exception as e:
            logger.exception(f"Failed to get backup info: {e}")
            return None
