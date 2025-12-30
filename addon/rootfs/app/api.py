"""HTTP API endpoints."""

import asyncio
import logging
from typing import Optional

from aiohttp import web

from app.config import Config
from app.git_sync import GitSync
from app.ha_manager import HAManager
from app.orchestrator_client import OrchestratorClient

logger = logging.getLogger(__name__)


def create_app(
    git_sync: GitSync,
    ha_manager: HAManager,
    orchestrator_client: OrchestratorClient,
    config: Config,
) -> web.Application:
    """
    Create and configure the web application.

    Args:
        git_sync: Git sync instance
        ha_manager: HA manager instance
        orchestrator_client: Orchestrator client instance
        config: Configuration instance

    Returns:
        web.Application: Configured application
    """
    app = web.Application()

    # Store references
    app["git_sync"] = git_sync
    app["ha_manager"] = ha_manager
    app["orchestrator_client"] = orchestrator_client
    app["config"] = config

    # Setup routes
    app.router.add_get("/health", health_check)
    app.router.add_get("/api/status", get_status)
    app.router.add_post("/api/sync", trigger_sync)
    app.router.add_post("/api/deploy", deploy_config)
    app.router.add_post("/api/validate", validate_config)
    app.router.add_post("/api/webhook", github_webhook)

    return app


async def health_check(request: web.Request) -> web.Response:
    """
    Health check endpoint.

    Args:
        request: HTTP request

    Returns:
        web.Response: Health status
    """
    return web.json_response({"status": "healthy"})


async def get_status(request: web.Request) -> web.Response:
    """
    Get server status.

    Args:
        request: HTTP request

    Returns:
        web.Response: Server status
    """
    config: Config = request.app["config"]
    git_sync: GitSync = request.app["git_sync"]
    ha_manager: HAManager = request.app["ha_manager"]

    commit_info = git_sync.get_commit_info()
    ha_version = await ha_manager.get_ha_version()

    return web.json_response(
        {
            "server_id": config.server_id,
            "github_repo": config.github_repo,
            "github_branch": config.github_branch,
            "auto_sync": config.auto_sync,
            "sync_interval": config.sync_interval,
            "current_commit": commit_info.get("hash"),
            "commit_message": commit_info.get("message"),
            "ha_version": ha_version,
        }
    )


async def trigger_sync(request: web.Request) -> web.Response:
    """
    Trigger manual sync.

    Args:
        request: HTTP request

    Returns:
        web.Response: Sync result
    """
    logger.info("Manual sync triggered via API")

    git_sync: GitSync = request.app["git_sync"]
    ha_manager: HAManager = request.app["ha_manager"]
    orchestrator_client: OrchestratorClient = request.app["orchestrator_client"]

    try:
        # Notify orchestrator
        await orchestrator_client.notify_event("sync_started", {})

        # Pull from GitHub
        success = await git_sync.sync()

        if not success:
            await orchestrator_client.notify_event(
                "sync_failed", {"step": "git_pull"}
            )
            return web.json_response(
                {"success": False, "message": "Git sync failed", "step": "git_pull"},
                status=500,
            )

        # Sync files
        success = await ha_manager.sync_files()

        if not success:
            await orchestrator_client.notify_event(
                "sync_failed", {"step": "file_sync"}
            )
            return web.json_response(
                {"success": False, "message": "File sync failed", "step": "file_sync"},
                status=500,
            )

        # Validate configuration
        validation_result = await ha_manager.validate_config()

        if not validation_result["success"]:
            await orchestrator_client.notify_event(
                "sync_failed",
                {"step": "validation", "error": validation_result.get("error")},
            )
            return web.json_response(
                {
                    "success": False,
                    "message": "Configuration validation failed",
                    "step": "validation",
                    "error": validation_result.get("error"),
                },
                status=400,
            )

        # Restart Home Assistant
        success = await ha_manager.restart_homeassistant()

        if not success:
            await orchestrator_client.notify_event(
                "sync_failed", {"step": "restart"}
            )
            return web.json_response(
                {"success": False, "message": "Restart failed", "step": "restart"},
                status=500,
            )

        # Notify success
        await orchestrator_client.notify_event("sync_completed", {})

        return web.json_response(
            {"success": True, "message": "Sync completed successfully"}
        )

    except Exception as e:
        logger.exception(f"Sync error: {e}")
        await orchestrator_client.notify_event(
            "sync_failed", {"step": "unknown", "error": str(e)}
        )
        return web.json_response(
            {"success": False, "message": str(e)}, status=500
        )


async def deploy_config(request: web.Request) -> web.Response:
    """
    Deploy configuration.

    Args:
        request: HTTP request

    Returns:
        web.Response: Deployment result
    """
    try:
        data = await request.json()
        deployment_id = data.get("deployment_id")
        skip_validation = data.get("skip_validation", False)
        auto_restart = data.get("auto_restart", True)

        logger.info(f"Deployment {deployment_id} triggered via API")

        git_sync: GitSync = request.app["git_sync"]
        ha_manager: HAManager = request.app["ha_manager"]
        orchestrator_client: OrchestratorClient = request.app["orchestrator_client"]

        # Notify deployment started
        await orchestrator_client.notify_event(
            "deployment_started", {"deployment_id": deployment_id}
        )

        # Pull from GitHub
        success = await git_sync.sync()

        if not success:
            await orchestrator_client.notify_event(
                "deployment_failed",
                {"deployment_id": deployment_id, "step": "git_pull"},
            )
            return web.json_response(
                {"success": False, "message": "Git sync failed"}, status=500
            )

        # Sync files
        success = await ha_manager.sync_files()

        if not success:
            await orchestrator_client.notify_event(
                "deployment_failed",
                {"deployment_id": deployment_id, "step": "file_sync"},
            )
            return web.json_response(
                {"success": False, "message": "File sync failed"}, status=500
            )

        # Validate if not skipped
        if not skip_validation:
            validation_result = await ha_manager.validate_config()

            if not validation_result["success"]:
                await orchestrator_client.notify_event(
                    "deployment_failed",
                    {
                        "deployment_id": deployment_id,
                        "step": "validation",
                        "error": validation_result.get("error"),
                    },
                )
                return web.json_response(
                    {
                        "success": False,
                        "message": "Validation failed",
                        "error": validation_result.get("error"),
                    },
                    status=400,
                )

        # Restart if requested
        if auto_restart:
            success = await ha_manager.restart_homeassistant()

            if not success:
                await orchestrator_client.notify_event(
                    "deployment_failed",
                    {"deployment_id": deployment_id, "step": "restart"},
                )
                return web.json_response(
                    {"success": False, "message": "Restart failed"}, status=500
                )

        # Notify success
        await orchestrator_client.notify_event(
            "deployment_completed", {"deployment_id": deployment_id}
        )

        return web.json_response(
            {"success": True, "message": "Deployment completed successfully"}
        )

    except Exception as e:
        logger.exception(f"Deployment error: {e}")
        return web.json_response(
            {"success": False, "message": str(e)}, status=500
        )


async def validate_config(request: web.Request) -> web.Response:
    """
    Validate configuration.

    Args:
        request: HTTP request

    Returns:
        web.Response: Validation result
    """
    ha_manager: HAManager = request.app["ha_manager"]

    validation_result = await ha_manager.validate_config()

    return web.json_response(validation_result)


async def github_webhook(request: web.Request) -> web.Response:
    """
    Handle GitHub webhook.

    Args:
        request: HTTP request

    Returns:
        web.Response: Webhook response
    """
    try:
        payload = await request.json()
        config: Config = request.app["config"]

        logger.info("GitHub webhook received")

        # Check if push is on our branch
        ref = payload.get("ref", "")

        if ref == f"refs/heads/{config.github_branch}":
            logger.info("Push detected on tracked branch, triggering sync")

            # Trigger sync in background
            git_sync: GitSync = request.app["git_sync"]
            ha_manager: HAManager = request.app["ha_manager"]
            orchestrator_client: OrchestratorClient = request.app["orchestrator_client"]

            asyncio.create_task(
                _background_sync(git_sync, ha_manager, orchestrator_client)
            )

            return web.json_response({"status": "sync_started"})

        return web.json_response({"status": "ignored"})

    except Exception as e:
        logger.exception(f"Webhook error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def _background_sync(
    git_sync: GitSync,
    ha_manager: HAManager,
    orchestrator_client: OrchestratorClient,
):
    """
    Perform sync in background.

    Args:
        git_sync: Git sync instance
        ha_manager: HA manager instance
        orchestrator_client: Orchestrator client instance
    """
    try:
        await orchestrator_client.notify_event("sync_started", {"trigger": "webhook"})

        success = await git_sync.sync()
        if success:
            success = await ha_manager.sync_files()

        if success:
            validation_result = await ha_manager.validate_config()
            success = validation_result["success"]

        if success:
            await ha_manager.restart_homeassistant()
            await orchestrator_client.notify_event(
                "sync_completed", {"trigger": "webhook"}
            )
        else:
            await orchestrator_client.notify_event(
                "sync_failed", {"trigger": "webhook"}
            )

    except Exception as e:
        logger.exception(f"Background sync error: {e}")
        await orchestrator_client.notify_event(
            "sync_failed", {"trigger": "webhook", "error": str(e)}
        )
