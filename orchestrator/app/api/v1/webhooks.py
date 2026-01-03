"""Webhook endpoints for GitHub integration."""

from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.github import GitHubIntegration
from app.db.session import get_db
from app.models.server import Server
from app.services.github_deployment_service import GitHubDeploymentService
from app.utils.logging import logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github")
async def github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive GitHub webhook events.

    Args:
        request: HTTP request
        db: Database session

    Returns:
        dict: Webhook processing result
    """
    try:
        # Get payload and signature
        payload = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")
        event_type = request.headers.get("X-GitHub-Event", "")

        logger.info(f"Received GitHub webhook: event={event_type}")

        # Verify webhook signature
        github_service = GitHubIntegration(db)
        if not await github_service.verify_webhook_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

        # Parse JSON payload
        import json
        data = json.loads(payload.decode("utf-8"))

        # Handle push event
        if event_type == "push":
            return await _handle_push_event(data, db)

        # Handle ping event
        elif event_type == "ping":
            logger.info("Webhook ping received")
            return {"message": "pong"}

        # Unsupported event
        else:
            logger.info(f"Ignoring unsupported event: {event_type}")
            return {"message": f"Event {event_type} ignored"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to process webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def _handle_push_event(data: dict, db: AsyncSession) -> dict:
    """
    Handle GitHub push event.

    Args:
        data: Webhook payload
        db: Database session

    Returns:
        dict: Processing result
    """
    try:
        # Extract repository info
        repo_full_name = data.get("repository", {}).get("full_name")
        branch = data.get("ref", "").replace("refs/heads/", "")
        commits = data.get("commits", [])

        logger.info(f"Push event: repo={repo_full_name}, branch={branch}, commits={len(commits)}")

        if not repo_full_name or not branch:
            return {"message": "Missing repository or branch information"}

        # Find servers linked to this repository and branch
        stmt = select(Server).where(
            Server.github_repo.like(f"%{repo_full_name}%"),
            Server.github_branch == branch,
            Server.auto_deploy == True
        )
        result = await db.execute(stmt)
        servers = list(result.scalars().all())

        if not servers:
            logger.info(f"No servers with auto-deploy enabled for {repo_full_name}:{branch}")
            return {
                "message": "No servers with auto-deploy enabled",
                "repository": repo_full_name,
                "branch": branch,
            }

        # Deploy to each server
        deployment_service = GitHubDeploymentService(db)
        deployment_results = []

        for server in servers:
            logger.info(f"Auto-deploying to server: {server.name}")

            try:
                result = await deployment_service.pull_from_github(server)
                deployment_results.append({
                    "server_id": server.id,
                    "server_name": server.name,
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "files_synced": result.get("files_synced", 0),
                })

                if result.get("success"):
                    logger.info(f"Successfully deployed to {server.name}")
                else:
                    logger.error(f"Failed to deploy to {server.name}: {result.get('error')}")

            except Exception as e:
                logger.exception(f"Error deploying to {server.name}: {e}")
                deployment_results.append({
                    "server_id": server.id,
                    "server_name": server.name,
                    "success": False,
                    "error": str(e),
                })

        return {
            "message": f"Processed push event for {len(servers)} server(s)",
            "repository": repo_full_name,
            "branch": branch,
            "commits_count": len(commits),
            "deployments": deployment_results,
        }

    except Exception as e:
        logger.exception(f"Failed to handle push event: {e}")
        return {
            "success": False,
            "error": str(e),
        }
