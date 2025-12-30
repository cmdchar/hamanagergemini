"""Main application module."""

import asyncio
import json
import logging
import os
import signal
from pathlib import Path
from threading import Thread

from aiohttp import web

from app.config import Config
from app.git_sync import GitSync
from app.ha_manager import HAManager
from app.orchestrator_client import OrchestratorClient
from app.api import create_app

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class HAConfigManager:
    """Main application class."""

    def __init__(self):
        """Initialize the manager."""
        self.config = Config.load()
        self.git_sync = GitSync(self.config)
        self.ha_manager = HAManager(self.config)
        self.orchestrator_client = OrchestratorClient(self.config)
        self.app = None
        self.runner = None
        self.shutdown_event = asyncio.Event()

    async def initial_sync(self):
        """Perform initial synchronization."""
        logger.info("Performing initial sync...")

        try:
            # Notify orchestrator
            await self.orchestrator_client.notify_event("startup", {"status": "starting"})

            # Clone or pull repository
            success = await self.git_sync.sync()

            if success:
                # Validate configuration
                validation_result = await self.ha_manager.validate_config()

                if validation_result["success"]:
                    logger.info("Initial sync completed successfully")
                    await self.orchestrator_client.notify_event(
                        "sync_completed", {"initial": True}
                    )
                else:
                    logger.error(f"Configuration validation failed: {validation_result.get('error')}")
                    await self.orchestrator_client.notify_event(
                        "sync_failed",
                        {"step": "validation", "error": validation_result.get("error")},
                    )
            else:
                logger.error("Initial sync failed")
                await self.orchestrator_client.notify_event(
                    "sync_failed", {"step": "git_sync"}
                )

        except Exception as e:
            logger.exception(f"Initial sync error: {e}")
            await self.orchestrator_client.notify_event(
                "sync_failed", {"step": "initial", "error": str(e)}
            )

    async def start_api_server(self):
        """Start the API server."""
        logger.info("Starting API server on port 8099...")

        self.app = create_app(
            self.git_sync, self.ha_manager, self.orchestrator_client, self.config
        )
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        site = web.TCPSite(self.runner, "0.0.0.0", 8099)
        await site.start()

        logger.info("API server started successfully")

    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("Shutting down...")

        # Notify orchestrator
        try:
            await self.orchestrator_client.notify_event("shutdown", {})
        except:
            pass

        # Cleanup API server
        if self.runner:
            await self.runner.cleanup()

        # Set shutdown event
        self.shutdown_event.set()

        logger.info("Shutdown complete")

    async def run(self):
        """Run the main application."""
        logger.info("=== HA Config Manager Add-on Starting ===")
        logger.info(f"Server ID: {self.config.server_id}")
        logger.info(f"GitHub Repo: {self.config.github_repo}")
        logger.info(f"Orchestrator URL: {self.config.orchestrator_url}")

        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

        try:
            # Start API server
            await self.start_api_server()

            # Perform initial sync
            await self.initial_sync()

            # Wait for shutdown signal
            await self.shutdown_event.wait()

        except Exception as e:
            logger.exception(f"Application error: {e}")
            raise


def main():
    """Main entry point."""
    manager = HAConfigManager()

    try:
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise
