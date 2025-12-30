"""Orchestrator communication client."""

import asyncio
import logging
import time
from typing import Dict, Optional

import aiohttp

from app.config import Config

logger = logging.getLogger(__name__)


class OrchestratorClient:
    """Client for communicating with the orchestrator."""

    def __init__(self, config: Config):
        """
        Initialize orchestrator client.

        Args:
            config: Application configuration
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """
        Get or create HTTP session.

        Returns:
            aiohttp.ClientSession: HTTP session
        """
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def notify_event(self, event: str, data: Optional[Dict] = None) -> bool:
        """
        Notify orchestrator about an event.

        Args:
            event: Event name
            data: Optional event data

        Returns:
            bool: True if successful
        """
        if not self.config.orchestrator_url:
            logger.debug("Orchestrator URL not configured, skipping notification")
            return False

        try:
            payload = {
                "server_id": self.config.server_id,
                "event": event,
                "timestamp": time.time(),
                "data": data or {},
            }

            session = await self.get_session()

            async with session.post(
                f"{self.config.orchestrator_url}/api/events",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    logger.debug(f"Notified orchestrator: {event}")
                    return True
                else:
                    logger.warning(
                        f"Orchestrator notification failed: {response.status}"
                    )
                    return False

        except asyncio.TimeoutError:
            logger.error(f"Orchestrator notification timeout: {event}")
            return False
        except Exception as e:
            logger.error(f"Failed to notify orchestrator: {e}")
            return False

    async def register_server(self) -> bool:
        """
        Register this server with the orchestrator.

        Returns:
            bool: True if successful
        """
        if not self.config.orchestrator_url:
            return False

        try:
            payload = {
                "server_id": self.config.server_id,
                "github_repo": self.config.github_repo,
                "github_branch": self.config.github_branch,
            }

            session = await self.get_session()

            async with session.post(
                f"{self.config.orchestrator_url}/api/servers/register",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status in (200, 201):
                    logger.info("Server registered with orchestrator")
                    return True
                else:
                    logger.warning(
                        f"Server registration failed: {response.status}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to register server: {e}")
            return False

    async def report_status(self, status: Dict) -> bool:
        """
        Report server status to orchestrator.

        Args:
            status: Status dictionary

        Returns:
            bool: True if successful
        """
        return await self.notify_event("status_update", status)

    async def get_deployment_config(self, deployment_id: int) -> Optional[Dict]:
        """
        Get deployment configuration from orchestrator.

        Args:
            deployment_id: Deployment ID

        Returns:
            Optional[Dict]: Deployment configuration or None
        """
        if not self.config.orchestrator_url:
            return None

        try:
            session = await self.get_session()

            async with session.get(
                f"{self.config.orchestrator_url}/api/deployments/{deployment_id}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(
                        f"Failed to get deployment config: {response.status}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Failed to get deployment config: {e}")
            return None
