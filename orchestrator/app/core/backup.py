"""Backup and snapshot management service."""

import asyncio
import json
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import asyncssh
from minio import Minio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.server import Server
from app.models.snapshot import Snapshot, SnapshotStatus
from app.utils.logging import logger

settings = get_settings()


class BackupManager:
    """Manager for creating and restoring backups."""

    def __init__(self, db: AsyncSession):
        """
        Initialize backup manager.

        Args:
            db: Database session
        """
        self.db = db
        self.minio_client = self._get_minio_client()

    def _get_minio_client(self) -> Optional[Minio]:
        """
        Get MinIO client for backup storage.

        Returns:
            Optional[Minio]: MinIO client or None if not configured
        """
        try:
            client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            )

            # Ensure bucket exists
            if not client.bucket_exists(settings.minio_bucket):
                client.make_bucket(settings.minio_bucket)
                logger.info(f"Created MinIO bucket: {settings.minio_bucket}")

            return client
        except Exception as e:
            logger.warning(f"MinIO client not available: {e}")
            return None

    async def create_backup(
        self,
        server: Server,
        name: Optional[str] = None,
        deployment_id: Optional[int] = None,
    ) -> Snapshot:
        """
        Create a backup snapshot of a server's configuration.

        Args:
            server: Server to backup
            name: Optional backup name
            deployment_id: Optional deployment ID

        Returns:
            Snapshot: Created snapshot
        """
        snapshot = Snapshot(
            server_id=server.id,
            name=name or f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            status=SnapshotStatus.CREATING,
            deployment_id=deployment_id,
            created_by=None,  # TODO: Add user_id from context
        )

        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)

        try:
            logger.info(f"Creating backup for server {server.name}")

            # Create temporary directory for backup
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                backup_path = temp_path / f"{snapshot.name}.tar.gz"

                # Connect to server and download configuration
                async with asyncssh.connect(
                    server.ssh_host or server.host,
                    port=server.ssh_port or 22,
                    username=server.ssh_user,
                    client_keys=[server.ssh_key_path] if server.ssh_key_path else None,
                    password=server.ssh_password,
                    known_hosts=None,
                ) as conn:
                    # Create SFTP client
                    async with conn.start_sftp_client() as sftp:
                        # Determine config directory
                        config_dir = server.config_path or "/config"

                        # Download configuration files
                        local_config_dir = temp_path / "config"
                        local_config_dir.mkdir(exist_ok=True)

                        await sftp.get(
                            config_dir,
                            str(local_config_dir),
                            recurse=True,
                            preserve=True,
                        )

                        logger.info(f"Downloaded config from {server.name}")

                # Create tar.gz archive
                with tarfile.open(backup_path, "w:gz") as tar:
                    tar.add(local_config_dir, arcname="config")

                # Get backup size
                snapshot.size_bytes = backup_path.stat().st_size

                # Upload to MinIO if available
                if self.minio_client:
                    object_name = f"snapshots/{server.id}/{snapshot.name}.tar.gz"

                    self.minio_client.fput_object(
                        settings.minio_bucket,
                        object_name,
                        str(backup_path),
                    )

                    snapshot.storage_path = f"s3://{settings.minio_bucket}/{object_name}"
                    logger.info(f"Uploaded backup to MinIO: {object_name}")
                else:
                    # Store locally if MinIO not available
                    local_storage = Path("/backups") / str(server.id)
                    local_storage.mkdir(parents=True, exist_ok=True)

                    import shutil

                    final_path = local_storage / f"{snapshot.name}.tar.gz"
                    shutil.copy(backup_path, final_path)

                    snapshot.storage_path = str(final_path)
                    logger.info(f"Stored backup locally: {final_path}")

            # Mark snapshot as complete
            snapshot.status = SnapshotStatus.COMPLETED
            snapshot.completed_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(snapshot)

            logger.info(
                f"Backup created successfully for {server.name}: {snapshot.name}"
            )

            return snapshot

        except Exception as e:
            logger.exception(f"Failed to create backup for {server.name}: {str(e)}")
            snapshot.status = SnapshotStatus.FAILED
            snapshot.error_message = str(e)
            await self.db.commit()
            raise

    async def restore_backup(self, snapshot_id: int) -> bool:
        """
        Restore a backup snapshot to a server.

        Args:
            snapshot_id: Snapshot ID to restore

        Returns:
            bool: True if successful
        """
        result = await self.db.execute(
            select(Snapshot).where(Snapshot.id == snapshot_id)
        )
        snapshot = result.scalar_one_or_none()

        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        if snapshot.status != SnapshotStatus.COMPLETED:
            raise ValueError("Can only restore completed snapshots")

        # Get server
        result = await self.db.execute(
            select(Server).where(Server.id == snapshot.server_id)
        )
        server = result.scalar_one_or_none()

        if not server:
            raise ValueError(f"Server {snapshot.server_id} not found")

        try:
            logger.info(f"Restoring backup {snapshot.name} to server {server.name}")

            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                backup_path = temp_path / f"{snapshot.name}.tar.gz"

                # Download backup from storage
                if snapshot.storage_path.startswith("s3://"):
                    # Download from MinIO
                    object_name = snapshot.storage_path.replace(
                        f"s3://{settings.minio_bucket}/", ""
                    )
                    self.minio_client.fget_object(
                        settings.minio_bucket,
                        object_name,
                        str(backup_path),
                    )
                else:
                    # Copy from local storage
                    import shutil

                    shutil.copy(snapshot.storage_path, backup_path)

                # Extract backup
                extract_dir = temp_path / "extracted"
                extract_dir.mkdir(exist_ok=True)

                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(extract_dir)

                config_dir = extract_dir / "config"

                # Connect to server and upload configuration
                async with asyncssh.connect(
                    server.ssh_host or server.host,
                    port=server.ssh_port or 22,
                    username=server.ssh_user,
                    client_keys=[server.ssh_key_path] if server.ssh_key_path else None,
                    password=server.ssh_password,
                    known_hosts=None,
                ) as conn:
                    # Create SFTP client
                    async with conn.start_sftp_client() as sftp:
                        # Determine config directory
                        remote_config_dir = server.config_path or "/config"

                        # Backup current config first
                        await conn.run(
                            f"mv {remote_config_dir} {remote_config_dir}.bak"
                        )

                        # Upload restored config
                        await sftp.put(
                            str(config_dir),
                            remote_config_dir,
                            recurse=True,
                            preserve=True,
                        )

                        logger.info(f"Restored config to {server.name}")

            logger.info(f"Backup restored successfully: {snapshot.name}")

            return True

        except Exception as e:
            logger.exception(f"Failed to restore backup: {str(e)}")
            raise

    async def delete_snapshot(self, snapshot_id: int) -> bool:
        """
        Delete a snapshot.

        Args:
            snapshot_id: Snapshot ID to delete

        Returns:
            bool: True if successful
        """
        result = await self.db.execute(
            select(Snapshot).where(Snapshot.id == snapshot_id)
        )
        snapshot = result.scalar_one_or_none()

        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        try:
            # Delete from storage
            if snapshot.storage_path:
                if snapshot.storage_path.startswith("s3://"):
                    # Delete from MinIO
                    object_name = snapshot.storage_path.replace(
                        f"s3://{settings.minio_bucket}/", ""
                    )
                    self.minio_client.remove_object(
                        settings.minio_bucket, object_name
                    )
                else:
                    # Delete local file
                    Path(snapshot.storage_path).unlink(missing_ok=True)

            # Delete from database
            await self.db.delete(snapshot)
            await self.db.commit()

            logger.info(f"Snapshot deleted: {snapshot.name}")

            return True

        except Exception as e:
            logger.exception(f"Failed to delete snapshot: {str(e)}")
            raise

    async def list_snapshots(
        self, server_id: Optional[int] = None
    ) -> list[Snapshot]:
        """
        List snapshots.

        Args:
            server_id: Optional server ID to filter by

        Returns:
            list[Snapshot]: List of snapshots
        """
        query = select(Snapshot).order_by(Snapshot.created_at.desc())

        if server_id:
            query = query.where(Snapshot.server_id == server_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())
