"""Rollback service for reverting failed deployments."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.backup import BackupManager
from app.models.deployment import Deployment, DeploymentStatus
from app.models.server import Server
from app.models.snapshot import Snapshot
from app.utils.logging import logger


class RollbackService:
    """Service for rolling back failed or problematic deployments."""

    def __init__(self, db: AsyncSession):
        """
        Initialize rollback service.

        Args:
            db: Database session
        """
        self.db = db
        self.backup_manager = BackupManager(db)

    async def rollback_deployment(
        self, deployment_id: int, reason: Optional[str] = None
    ) -> bool:
        """
        Rollback a deployment to the previous snapshot.

        Args:
            deployment_id: Deployment ID to rollback
            reason: Optional reason for rollback

        Returns:
            bool: True if successful
        """
        try:
            # Get deployment
            result = await self.db.execute(
                select(Deployment).where(Deployment.id == deployment_id)
            )
            deployment = result.scalar_one_or_none()

            if not deployment:
                raise ValueError(f"Deployment {deployment_id} not found")

            logger.info(f"Starting rollback for deployment {deployment_id}")

            # Get snapshots created for this deployment
            result = await self.db.execute(
                select(Snapshot)
                .where(Snapshot.deployment_id == deployment_id)
                .order_by(Snapshot.created_at.asc())
            )
            snapshots = list(result.scalars().all())

            if not snapshots:
                raise ValueError(
                    f"No snapshots found for deployment {deployment_id}"
                )

            # Rollback each snapshot
            rollback_count = 0
            failed_count = 0

            for snapshot in snapshots:
                try:
                    await self.backup_manager.restore_backup(snapshot.id)
                    rollback_count += 1
                    logger.info(
                        f"Rolled back snapshot {snapshot.id} for server {snapshot.server_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to rollback snapshot {snapshot.id}: {str(e)}"
                    )
                    failed_count += 1

            # Update deployment status
            deployment.status = DeploymentStatus.ROLLED_BACK

            await self.db.commit()

            success = failed_count == 0
            logger.info(
                f"Rollback completed for deployment {deployment_id}: "
                f"{rollback_count} successful, {failed_count} failed"
            )

            return success

        except Exception as e:
            logger.exception(f"Rollback failed for deployment {deployment_id}: {str(e)}")
            raise

    async def rollback_server_to_snapshot(
        self, server_id: int, snapshot_id: int
    ) -> bool:
        """
        Rollback a specific server to a specific snapshot.

        Args:
            server_id: Server ID
            snapshot_id: Snapshot ID to restore

        Returns:
            bool: True if successful
        """
        try:
            # Verify server exists
            result = await self.db.execute(
                select(Server).where(Server.id == server_id)
            )
            server = result.scalar_one_or_none()

            if not server:
                raise ValueError(f"Server {server_id} not found")

            # Verify snapshot belongs to this server
            result = await self.db.execute(
                select(Snapshot).where(
                    Snapshot.id == snapshot_id, Snapshot.server_id == server_id
                )
            )
            snapshot = result.scalar_one_or_none()

            if not snapshot:
                raise ValueError(
                    f"Snapshot {snapshot_id} not found or doesn't belong to server {server_id}"
                )

            logger.info(
                f"Rolling back server {server.name} to snapshot {snapshot.name}"
            )

            # Restore snapshot
            await self.backup_manager.restore_backup(snapshot_id)

            logger.info(
                f"Successfully rolled back server {server.name} to snapshot {snapshot.name}"
            )

            return True

        except Exception as e:
            logger.exception(
                f"Failed to rollback server {server_id} to snapshot {snapshot_id}: {str(e)}"
            )
            raise

    async def get_latest_snapshot(self, server_id: int) -> Optional[Snapshot]:
        """
        Get the latest completed snapshot for a server.

        Args:
            server_id: Server ID

        Returns:
            Optional[Snapshot]: Latest snapshot or None
        """
        from app.models.snapshot import SnapshotStatus

        result = await self.db.execute(
            select(Snapshot)
            .where(
                Snapshot.server_id == server_id,
                Snapshot.status == SnapshotStatus.COMPLETED,
            )
            .order_by(Snapshot.created_at.desc())
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def auto_rollback_if_needed(
        self, deployment_id: int, error_message: Optional[str] = None
    ) -> bool:
        """
        Automatically rollback a deployment if it failed.

        Args:
            deployment_id: Deployment ID
            error_message: Optional error message

        Returns:
            bool: True if rollback was performed
        """
        try:
            # Get deployment
            result = await self.db.execute(
                select(Deployment).where(Deployment.id == deployment_id)
            )
            deployment = result.scalar_one_or_none()

            if not deployment:
                logger.warning(f"Deployment {deployment_id} not found for auto-rollback")
                return False

            # Check if deployment failed
            if deployment.status != DeploymentStatus.FAILED:
                logger.info(
                    f"Deployment {deployment_id} did not fail, skipping auto-rollback"
                )
                return False

            # Check if auto-rollback is enabled
            if not deployment.auto_rollback:
                logger.info(
                    f"Auto-rollback disabled for deployment {deployment_id}"
                )
                return False

            logger.info(
                f"Auto-rollback triggered for failed deployment {deployment_id}"
            )

            # Perform rollback
            reason = f"Auto-rollback due to deployment failure"
            if error_message:
                reason += f": {error_message}"

            await self.rollback_deployment(deployment_id, reason)

            return True

        except Exception as e:
            logger.exception(f"Auto-rollback failed for deployment {deployment_id}: {str(e)}")
            return False

    async def verify_rollback(self, server_id: int, snapshot_id: int) -> dict:
        """
        Verify that a rollback was successful by comparing checksums or file counts.

        Args:
            server_id: Server ID
            snapshot_id: Snapshot ID that was restored

        Returns:
            dict: Verification results
        """
        try:
            # Get server and snapshot
            result = await self.db.execute(
                select(Server).where(Server.id == server_id)
            )
            server = result.scalar_one_or_none()

            result = await self.db.execute(
                select(Snapshot).where(Snapshot.id == snapshot_id)
            )
            snapshot = result.scalar_one_or_none()

            if not server or not snapshot:
                return {
                    "success": False,
                    "error": "Server or snapshot not found",
                }

            # TODO: Implement actual verification logic
            # This could include:
            # 1. Comparing file checksums
            # 2. Counting files
            # 3. Verifying specific critical files exist
            # 4. Running HA config check

            logger.info(
                f"Verifying rollback for server {server.name} to snapshot {snapshot.name}"
            )

            return {
                "success": True,
                "message": "Rollback verification not yet implemented",
                "server_id": server_id,
                "snapshot_id": snapshot_id,
            }

        except Exception as e:
            logger.exception(f"Rollback verification failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
