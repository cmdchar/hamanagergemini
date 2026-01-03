"""GitHub integration API endpoints."""

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.github import GitHubIntegration
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.github import (
    GitHubStatusResponse,
    GitHubRepoResponse,
    GitHubBranchResponse,
    GitHubWebhookResponse,
    LinkRepoRequest,
)
from app.utils.logging import logger

router = APIRouter(prefix="/github", tags=["github"])


class GitHubConfigRequest(BaseModel):
    """GitHub configuration request."""
    clientId: str
    clientSecret: str
    token: str
    webhookSecret: str


@router.get("/status", response_model=GitHubStatusResponse)
async def get_github_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get GitHub connection status.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        GitHubStatusResponse: GitHub connection status
    """
    try:
        github_service = GitHubIntegration(db)

        # Check if GitHub client is configured
        if not github_service.github_client:
            return GitHubStatusResponse(
                connected=False,
                username=None,
                email=None,
            )

        # Get authenticated user info
        try:
            user = github_service.github_client.get_user()
            return GitHubStatusResponse(
                connected=True,
                username=user.login,
                email=user.email,
            )
        except Exception as e:
            logger.error(f"Failed to get GitHub user: {e}")
            return GitHubStatusResponse(
                connected=False,
                username=None,
                email=None,
            )

    except Exception as e:
        logger.exception(f"Failed to get GitHub status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/repos", response_model=List[GitHubRepoResponse])
async def list_repositories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's GitHub repositories.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[GitHubRepoResponse]: List of repositories
    """
    try:
        github_service = GitHubIntegration(db)

        if not github_service.github_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub not connected",
            )

        # Get user's repositories
        user = github_service.github_client.get_user()
        repos = user.get_repos()

        repo_list = []
        for repo in repos:
            repo_list.append(
                GitHubRepoResponse(
                    id=str(repo.id),
                    name=repo.name,
                    full_name=repo.full_name,
                    description=repo.description or "",
                    private=repo.private,
                    clone_url=repo.clone_url,
                    default_branch=repo.default_branch,
                    updated_at=repo.updated_at.isoformat() if repo.updated_at else None,
                )
            )

        return repo_list

    except Exception as e:
        logger.exception(f"Failed to list repositories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/repos/{owner}/{repo}/branches", response_model=List[GitHubBranchResponse])
async def list_branches(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List branches in a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[GitHubBranchResponse]: List of branches
    """
    try:
        github_service = GitHubIntegration(db)

        result = await github_service.list_branches(owner, repo)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to list branches"),
            )

        return [
            GitHubBranchResponse(
                name=branch["name"],
                commit=branch["commit"],
                protected=branch["protected"],
            )
            for branch in result["branches"]
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list branches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/webhook", response_model=GitHubWebhookResponse)
async def get_webhook_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get webhook configuration.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        GitHubWebhookResponse: Webhook configuration
    """
    from app.config import settings

    # Return webhook configuration
    return GitHubWebhookResponse(
        enabled=bool(settings.github_webhook_secret),
        url=f"https://your-domain.com/api/v1/webhooks/github",  # TODO: Use actual domain
        secret=settings.github_webhook_secret or "",
        events=["push"],
    )


@router.post("/repos/{owner}/{repo}/webhook")
async def create_webhook(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create webhook for a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Webhook creation result
    """
    from app.config import settings

    try:
        github_service = GitHubIntegration(db)

        webhook_url = f"https://your-domain.com/api/v1/webhooks/github"  # TODO: Use actual domain

        result = await github_service.create_webhook(
            owner=owner,
            repo_name=repo,
            webhook_url=webhook_url,
            events=["push"],
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to create webhook"),
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/disconnect")
async def disconnect_github(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Disconnect GitHub integration.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Success message
    """
    # TODO: Remove GitHub token from user settings
    return {"message": "GitHub disconnected successfully"}


@router.post("/config")
async def save_github_config(
    config: GitHubConfigRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Save GitHub configuration to .env file.

    Args:
        config: GitHub configuration
        current_user: Current authenticated user

    Returns:
        dict: Success message
    """
    try:
        # Path to .env file (in project root, not in orchestrator/)
        env_file_path = "/app/../.env"

        # Read existing .env file if it exists
        env_vars = {}
        if os.path.exists(env_file_path):
            with open(env_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key] = value

        # Update with new GitHub config
        env_vars["NEXT_PUBLIC_GITHUB_CLIENT_ID"] = config.clientId
        env_vars["GITHUB_CLIENT_SECRET"] = config.clientSecret
        env_vars["GITHUB_TOKEN"] = config.token
        env_vars["GITHUB_WEBHOOK_SECRET"] = config.webhookSecret

        # Write back to .env file
        with open(env_file_path, "w") as f:
            # Write header comment
            f.write("# GitHub OAuth Configuration\n")
            f.write("# Generated by HA Config Manager\n\n")

            # Write GitHub vars first
            f.write("# GitHub Integration\n")
            f.write(f"NEXT_PUBLIC_GITHUB_CLIENT_ID={env_vars.get('NEXT_PUBLIC_GITHUB_CLIENT_ID', '')}\n")
            f.write(f"GITHUB_CLIENT_SECRET={env_vars.get('GITHUB_CLIENT_SECRET', '')}\n")
            f.write(f"GITHUB_TOKEN={env_vars.get('GITHUB_TOKEN', '')}\n")
            f.write(f"GITHUB_WEBHOOK_SECRET={env_vars.get('GITHUB_WEBHOOK_SECRET', '')}\n\n")

            # Write other existing vars
            f.write("# Other Configuration\n")
            for key, value in env_vars.items():
                if key not in ["NEXT_PUBLIC_GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "GITHUB_TOKEN", "GITHUB_WEBHOOK_SECRET"]:
                    f.write(f"{key}={value}\n")

        logger.info(f"GitHub configuration saved to {env_file_path}")

        return {
            "message": "Configuration saved successfully. Please restart Docker containers to apply changes.",
            "restart_command": "docker-compose restart"
        }

    except Exception as e:
        logger.exception(f"Failed to save GitHub configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save configuration: {str(e)}"
        )


@router.post("/servers/{server_id}/link")
async def link_repository_to_server(
    server_id: int,
    link_data: LinkRepoRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Link a GitHub repository to a server.

    Args:
        server_id: Server ID
        link_data: Repository link data
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Success message
    """
    try:
        from sqlalchemy import select
        from app.models.server import Server

        # Get server
        stmt = select(Server).where(Server.id == server_id)
        result = await db.execute(stmt)
        server = result.scalar_one_or_none()

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )

        # Update server with GitHub repo info
        server.github_repo = link_data.repo_url
        server.github_branch = link_data.branch

        await db.commit()
        await db.refresh(server)

        logger.info(f"Linked repository {link_data.repo_url} to server {server.name}")

        return {
            "message": "Repository linked successfully",
            "server_id": server.id,
            "repo_url": link_data.repo_url,
            "branch": link_data.branch,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to link repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/servers/{server_id}/unlink")
async def unlink_repository_from_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Unlink GitHub repository from a server.

    Args:
        server_id: Server ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Success message
    """
    try:
        from sqlalchemy import select
        from app.models.server import Server

        # Get server
        stmt = select(Server).where(Server.id == server_id)
        result = await db.execute(stmt)
        server = result.scalar_one_or_none()

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )

        # Remove GitHub repo info
        server.github_repo = None
        server.github_branch = None

        await db.commit()
        await db.refresh(server)

        logger.info(f"Unlinked repository from server {server.name}")

        return {
            "message": "Repository unlinked successfully",
            "server_id": server.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to unlink repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/servers/{server_id}/push")
async def push_to_github(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Push server configuration to GitHub.

    Args:
        server_id: Server ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Push result
    """
    try:
        from sqlalchemy import select
        from app.models.server import Server
        from app.services.github_deployment_service import GitHubDeploymentService

        # Get server
        stmt = select(Server).where(Server.id == server_id)
        result = await db.execute(stmt)
        server = result.scalar_one_or_none()

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )

        # Check if server is linked to GitHub
        if not server.github_repo or not server.github_branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Server is not linked to a GitHub repository"
            )

        # Execute push
        deployment_service = GitHubDeploymentService(db)
        result = await deployment_service.push_to_github(server)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to push to GitHub")
            )

        logger.info(f"Pushed configuration from server {server.name} to GitHub")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to push to GitHub: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/servers/{server_id}/pull")
async def pull_from_github(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Pull configuration from GitHub to server.

    Args:
        server_id: Server ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Pull result
    """
    try:
        from sqlalchemy import select
        from app.models.server import Server
        from app.services.github_deployment_service import GitHubDeploymentService

        # Get server
        stmt = select(Server).where(Server.id == server_id)
        result = await db.execute(stmt)
        server = result.scalar_one_or_none()

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )

        # Check if server is linked to GitHub
        if not server.github_repo or not server.github_branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Server is not linked to a GitHub repository"
            )

        # Execute pull
        deployment_service = GitHubDeploymentService(db)
        result = await deployment_service.pull_from_github(server)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to pull from GitHub")
            )

        logger.info(f"Pulled configuration from GitHub to server {server.name}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to pull from GitHub: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/servers/{server_id}/files")
async def list_repository_files(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List files in server's linked GitHub repository.

    Args:
        server_id: Server ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Repository files and metadata
    """
    try:
        from sqlalchemy import select
        from app.models.server import Server

        # Get server
        stmt = select(Server).where(Server.id == server_id)
        result = await db.execute(stmt)
        server = result.scalar_one_or_none()

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )

        # Check if server is linked to GitHub
        if not server.github_repo or not server.github_branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Server is not linked to a GitHub repository"
            )

        # Get GitHub integration
        github_service = GitHubIntegration(db)
        if not github_service.github_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub integration not configured"
            )

        # Parse repository info
        # Format: "owner/repo" or "https://github.com/owner/repo"
        repo_full_name = server.github_repo
        if "github.com" in repo_full_name:
            # Extract owner/repo from URL
            parts = repo_full_name.rstrip("/").replace(".git", "").split("/")
            repo_full_name = f"{parts[-2]}/{parts[-1]}"

        # Get repository
        try:
            repo = github_service.github_client.get_repo(repo_full_name)
        except Exception as e:
            logger.error(f"Failed to get repository {repo_full_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository not found: {repo_full_name}"
            )

        # Get branch
        try:
            branch = repo.get_branch(server.github_branch)
        except Exception as e:
            logger.error(f"Failed to get branch {server.github_branch}: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Branch not found: {server.github_branch}"
            )

        # Get files in root directory
        try:
            contents = repo.get_contents("", ref=server.github_branch)

            files = []
            for content in contents:
                file_info = {
                    "name": content.name,
                    "path": content.path,
                    "type": content.type,  # "file" or "dir"
                    "size": content.size if content.type == "file" else 0,
                    "sha": content.sha,
                    "download_url": content.download_url if content.type == "file" else None,
                }
                files.append(file_info)

            # Sort: directories first, then files alphabetically
            files.sort(key=lambda x: (x["type"] != "dir", x["name"]))

            return {
                "repository": repo_full_name,
                "branch": server.github_branch,
                "commit_sha": branch.commit.sha[:7],
                "commit_message": branch.commit.commit.message.strip(),
                "files": files,
                "total_files": len([f for f in files if f["type"] == "file"]),
                "total_dirs": len([f for f in files if f["type"] == "dir"]),
            }

        except Exception as e:
            logger.error(f"Failed to get repository contents: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list repository files: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list repository files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
