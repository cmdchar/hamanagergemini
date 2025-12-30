"""Deployment engine for managing configuration deployments."""

import asyncio
from datetime import datetime
from typing import List, Optional

import asyncssh
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.backup import BackupManager
from app.core.validation import ConfigValidator
from app.models.deployment import Deployment, DeploymentResult, DeploymentStatus
from app.models.server import Server, ServerStatus
from app.models.snapshot import Snapshot
from app.utils.logging import logger

settings = get_settings()


class DeploymentEngine:
    """Engine for deploying configurations to Home Assistant servers."""

    def __init__(self, db: AsyncSession):
        """
        Initialize deployment engine.

        Args:
            db: Database session
        """
        self.db = db
        self.validator = ConfigValidator()
        self.backup_manager = BackupManager(db)

    async def deploy(
        self,
        deployment: Deployment,
        servers: Optional[List[Server]] = None,
    ) -> Deployment:
        """
        Execute deployment to servers.

        Args:
            deployment: Deployment object
            servers: Optional list of specific servers, otherwise uses deployment.target_servers

        Returns:
            Deployment: Updated deployment object
        """
        try:
            # Update deployment status
            deployment.status = DeploymentStatus.VALIDATING
            deployment.started_at = datetime.utcnow()
            await self.db.commit()

            # Get target servers
            if servers is None:
                servers = await self._get_target_servers(deployment)

            deployment.total_servers = len(servers)
            await self.db.commit()

            logger.info(
                f"Starting deployment {deployment.id} to {len(servers)} servers"
            )

            # Deploy to each server
            tasks = []
            for server in servers:
                task = self._deploy_to_server(deployment, server)
                tasks.append(task)

            # Execute deployments in parallel with concurrency limit
            semaphore = asyncio.Semaphore(settings.max_parallel_deployments)

            async def bounded_deploy(task):
                async with semaphore:
                    return await task

            results = await asyncio.gather(
                *[bounded_deploy(task) for task in tasks],
                return_exceptions=True,
            )

            # Count successes and failures
            successful = sum(
                1 for r in results if isinstance(r, DeploymentResult) and r.success
            )
            failed = len(results) - successful

            deployment.successful_servers = successful
            deployment.failed_servers = failed
            deployment.completed_at = datetime.utcnow()
            deployment.duration_seconds = int(
                (deployment.completed_at - deployment.started_at).total_seconds()
            )

            # Update final status
            if failed == 0:
                deployment.status = DeploymentStatus.SUCCESS
            elif successful == 0:
                deployment.status = DeploymentStatus.FAILED
            else:
                deployment.status = DeploymentStatus.SUCCESS  # Partial success

            await self.db.commit()

            logger.info(
                f"Deployment {deployment.id} completed: "
                f"{successful} successful, {failed} failed"
            )

            return deployment

        except Exception as e:
            logger.exception(f"Deployment {deployment.id} failed: {str(e)}")
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            deployment.completed_at = datetime.utcnow()
            if deployment.started_at:
                deployment.duration_seconds = int(
                    (deployment.completed_at - deployment.started_at).total_seconds()
                )
            await self.db.commit()
            raise

    async def _deploy_to_server(
        self,
        deployment: Deployment,
        server: Server,
    ) -> DeploymentResult:
        """
        Deploy configuration to a single server.

        Args:
            deployment: Deployment object
            server: Server to deploy to

        Returns:
            DeploymentResult: Deployment result
        """
        result = DeploymentResult(
            deployment_id=deployment.id,
            server_id=server.id,
            status=DeploymentStatus.PENDING,
            started_at=datetime.utcnow(),
        )
        self.db.add(result)
        await self.db.commit()

        try:
            logger.info(f"Deploying to server {server.name} ({server.id})")

            # Validate configuration if not skipped
            if not deployment.skip_validation and settings.validate_before_deploy:
                result.status = DeploymentStatus.VALIDATING
                await self.db.commit()

                validation_result = await self.validator.validate_config(server)
                result.validation_output = validation_result.get("output", "")

                if not validation_result.get("success", False):
                    raise Exception(f"Validation failed: {validation_result.get('error')}")

            # Create backup if not skipped
            snapshot = None
            if not deployment.skip_backup and settings.backup_before_deploy:
                result.status = DeploymentStatus.BACKING_UP
                await self.db.commit()

                snapshot = await self.backup_manager.create_backup(
                    server=server,
                    name=f"pre_deploy_{deployment.id}",
                    deployment_id=deployment.id,
                )
                result.backup_id = snapshot.id

            # Deploy configuration
            result.status = DeploymentStatus.DEPLOYING
            await self.db.commit()

            await self._copy_files_to_server(server, deployment)

            # Restart Home Assistant if configured
            if deployment.auto_restart:
                result.status = DeploymentStatus.RESTARTING
                await self.db.commit()

                await self._restart_home_assistant(server)

            # Mark as successful
            result.status = DeploymentStatus.SUCCESS
            result.success = True
            result.completed_at = datetime.utcnow()
            result.duration_seconds = int(
                (result.completed_at - result.started_at).total_seconds()
            )

            await self.db.commit()

            logger.info(f"Successfully deployed to server {server.name}")

            return result

        except Exception as e:
            logger.exception(f"Failed to deploy to server {server.name}: {str(e)}")
            result.status = DeploymentStatus.FAILED
            result.success = False
            result.error_message = str(e)
            result.completed_at = datetime.utcnow()
            if result.started_at:
                result.duration_seconds = int(
                    (result.completed_at - result.started_at).total_seconds()
                )
            await self.db.commit()
            return result

    async def _get_target_servers(self, deployment: Deployment) -> List[Server]:
        """
        Get target servers for deployment.

        Args:
            deployment: Deployment object

        Returns:
            List[Server]: List of target servers
        """
        if deployment.deploy_all:
            result = await self.db.execute(
                select(Server).where(Server.is_active == True)
            )
            return list(result.scalars().all())

        if deployment.target_servers:
            result = await self.db.execute(
                select(Server).where(
                    Server.id.in_(deployment.target_servers),
                    Server.is_active == True,
                )
            )
            return list(result.scalars().all())

        return []

    async def _copy_files_to_server(self, server: Server, deployment: Deployment) -> None:
        """
        Copy configuration files to server.

        Args:
            server: Server to copy files to
            deployment: Deployment object
        """
        # TODO: Implement actual file copying via SSH/SCP
        # This is a placeholder - should use git pull or rsync
        await asyncio.sleep(1)  # Simulate file copy
        logger.info(f"Files copied to {server.name}")

    async def _restart_home_assistant(self, server: Server) -> None:
        """
        Restart Home Assistant on server.

        Args:
            server: Server to restart
        """
        try:
            # Use SSH to restart Home Assistant
            async with asyncssh.connect(
                server.ssh_host or server.host,
                port=server.ssh_port or 22,
                username=server.ssh_user,
                client_keys=[server.ssh_key_path] if server.ssh_key_path else None,
                password=server.ssh_password,
                known_hosts=None,
            ) as conn:
                # Try supervisor restart first (for HA OS)
                result = await conn.run("ha core restart", check=False)
                if result.exit_status != 0:
                    # Try systemctl if supervisor not available
                    await conn.run("sudo systemctl restart home-assistant@homeassistant")

                logger.info(f"Home Assistant restarted on {server.name}")

        except Exception as e:
            logger.error(f"Failed to restart Home Assistant on {server.name}: {str(e)}")
            raise

    async def cancel_deployment(self, deployment_id: int) -> Deployment:
        """
        Cancel a running deployment.

        Args:
            deployment_id: Deployment ID

        Returns:
            Deployment: Cancelled deployment
        """
        result = await self.db.execute(
            select(Deployment).where(Deployment.id == deployment_id)
        )
        deployment = result.scalar_one_or_none()

        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        if deployment.is_complete:
            raise ValueError("Cannot cancel completed deployment")

        deployment.status = DeploymentStatus.CANCELLED
        deployment.completed_at = datetime.utcnow()
        if deployment.started_at:
            deployment.duration_seconds = int(
                (deployment.completed_at - deployment.started_at).total_seconds()
            )

        await self.db.commit()

        logger.info(f"Deployment {deployment_id} cancelled")

        return deployment
