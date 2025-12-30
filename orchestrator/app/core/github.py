"""GitHub integration for managing configuration repositories."""

import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from git import Repo
from github import Github
from github.GithubException import GithubException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.server import Server
from app.utils.logging import logger

settings = get_settings()


class GitHubIntegration:
    """Service for integrating with GitHub repositories."""

    def __init__(self, db: AsyncSession):
        """
        Initialize GitHub integration.

        Args:
            db: Database session
        """
        self.db = db
        self.github_client = self._get_github_client()

    def _get_github_client(self) -> Optional[Github]:
        """
        Get GitHub API client.

        Returns:
            Optional[Github]: GitHub client or None if not configured
        """
        if settings.github_token:
            return Github(settings.github_token)
        else:
            logger.warning("GitHub token not configured")
            return None

    async def clone_repository(
        self, repo_url: str, branch: str = "main", target_dir: Optional[Path] = None
    ) -> Path:
        """
        Clone a GitHub repository.

        Args:
            repo_url: Repository URL
            branch: Branch name
            target_dir: Optional target directory

        Returns:
            Path: Path to cloned repository
        """
        try:
            if target_dir is None:
                temp_dir = tempfile.mkdtemp(prefix="ha_config_")
                target_dir = Path(temp_dir)

            logger.info(f"Cloning repository {repo_url} (branch: {branch})")

            # Clone repository
            await asyncio.to_thread(
                Repo.clone_from,
                repo_url,
                str(target_dir),
                branch=branch,
                depth=1,  # Shallow clone for faster performance
            )

            logger.info(f"Repository cloned to {target_dir}")

            return target_dir

        except Exception as e:
            logger.exception(f"Failed to clone repository {repo_url}: {str(e)}")
            raise

    async def pull_latest_changes(self, repo_path: Path, branch: str = "main") -> dict:
        """
        Pull latest changes from a repository.

        Args:
            repo_path: Path to local repository
            branch: Branch name

        Returns:
            dict: Pull result with commit information
        """
        try:
            logger.info(f"Pulling latest changes from {repo_path}")

            repo = Repo(str(repo_path))

            # Fetch latest changes
            origin = repo.remotes.origin
            await asyncio.to_thread(origin.fetch)

            # Get current commit before pull
            old_commit = repo.head.commit.hexsha

            # Pull changes
            await asyncio.to_thread(origin.pull, branch)

            # Get new commit after pull
            new_commit = repo.head.commit.hexsha

            # Check if there were changes
            has_changes = old_commit != new_commit

            result = {
                "success": True,
                "has_changes": has_changes,
                "old_commit": old_commit[:7],
                "new_commit": new_commit[:7],
                "commit_message": repo.head.commit.message.strip() if has_changes else None,
                "author": str(repo.head.commit.author) if has_changes else None,
            }

            logger.info(
                f"Pull completed. Changes: {has_changes}, Commit: {result['new_commit']}"
            )

            return result

        except Exception as e:
            logger.exception(f"Failed to pull changes from {repo_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_commit_diff(
        self, repo_path: Path, commit1: str, commit2: str = "HEAD"
    ) -> dict:
        """
        Get diff between two commits.

        Args:
            repo_path: Path to local repository
            commit1: First commit hash
            commit2: Second commit hash (defaults to HEAD)

        Returns:
            dict: Diff information
        """
        try:
            repo = Repo(str(repo_path))

            commit_a = repo.commit(commit1)
            commit_b = repo.commit(commit2)

            # Get diff
            diff_index = commit_a.diff(commit_b)

            # Collect changed files
            changed_files = []
            for diff_item in diff_index:
                changed_files.append(
                    {
                        "path": diff_item.a_path or diff_item.b_path,
                        "change_type": diff_item.change_type,
                        "diff": diff_item.diff.decode("utf-8", errors="ignore")
                        if diff_item.diff
                        else None,
                    }
                )

            return {
                "success": True,
                "commit_a": commit1,
                "commit_b": commit2,
                "files_changed": len(changed_files),
                "changed_files": changed_files,
            }

        except Exception as e:
            logger.exception(f"Failed to get diff: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_repository_info(self, owner: str, repo_name: str) -> dict:
        """
        Get repository information from GitHub API.

        Args:
            owner: Repository owner
            repo_name: Repository name

        Returns:
            dict: Repository information
        """
        if not self.github_client:
            return {
                "success": False,
                "error": "GitHub client not configured",
            }

        try:
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")

            return {
                "success": True,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "default_branch": repo.default_branch,
                "private": repo.private,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "size": repo.size,
            }

        except GithubException as e:
            logger.error(f"Failed to get repository info: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def list_branches(self, owner: str, repo_name: str) -> dict:
        """
        List branches in a repository.

        Args:
            owner: Repository owner
            repo_name: Repository name

        Returns:
            dict: List of branches
        """
        if not self.github_client:
            return {
                "success": False,
                "error": "GitHub client not configured",
            }

        try:
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            branches = repo.get_branches()

            branch_list = [
                {
                    "name": branch.name,
                    "commit": branch.commit.sha[:7],
                    "protected": branch.protected,
                }
                for branch in branches
            ]

            return {
                "success": True,
                "branches": branch_list,
            }

        except GithubException as e:
            logger.error(f"Failed to list branches: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def create_webhook(
        self, owner: str, repo_name: str, webhook_url: str, events: Optional[List[str]] = None
    ) -> dict:
        """
        Create a webhook in a GitHub repository.

        Args:
            owner: Repository owner
            repo_name: Repository name
            webhook_url: URL to send webhook events to
            events: List of events to subscribe to (defaults to ['push'])

        Returns:
            dict: Webhook creation result
        """
        if not self.github_client:
            return {
                "success": False,
                "error": "GitHub client not configured",
            }

        try:
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")

            config = {
                "url": webhook_url,
                "content_type": "json",
            }

            if settings.github_webhook_secret:
                config["secret"] = settings.github_webhook_secret

            webhook = repo.create_hook(
                name="web",
                config=config,
                events=events or ["push"],
                active=True,
            )

            logger.info(f"Created webhook for {owner}/{repo_name}: {webhook.id}")

            return {
                "success": True,
                "webhook_id": webhook.id,
                "url": webhook_url,
                "events": webhook.events,
            }

        except GithubException as e:
            logger.error(f"Failed to create webhook: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def verify_webhook_signature(
        self, payload: bytes, signature: str
    ) -> bool:
        """
        Verify GitHub webhook signature.

        Args:
            payload: Raw webhook payload
            signature: Signature from X-Hub-Signature-256 header

        Returns:
            bool: True if signature is valid
        """
        import hashlib
        import hmac

        if not settings.github_webhook_secret:
            logger.warning("GitHub webhook secret not configured")
            return True  # Allow if no secret configured

        # Calculate expected signature
        secret = settings.github_webhook_secret.encode("utf-8")
        expected_signature = (
            "sha256="
            + hmac.new(secret, payload, hashlib.sha256).hexdigest()
        )

        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)

    async def get_file_content(
        self, owner: str, repo_name: str, file_path: str, branch: str = "main"
    ) -> dict:
        """
        Get content of a file from GitHub repository.

        Args:
            owner: Repository owner
            repo_name: Repository name
            file_path: Path to file in repository
            branch: Branch name

        Returns:
            dict: File content
        """
        if not self.github_client:
            return {
                "success": False,
                "error": "GitHub client not configured",
            }

        try:
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            content = repo.get_contents(file_path, ref=branch)

            return {
                "success": True,
                "content": content.decoded_content.decode("utf-8"),
                "sha": content.sha,
                "size": content.size,
            }

        except GithubException as e:
            logger.error(f"Failed to get file content: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
