"""Git synchronization module."""

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Optional

import git

from app.config import Config

logger = logging.getLogger(__name__)


class GitSync:
    """Handles Git operations for configuration synchronization."""

    def __init__(self, config: Config):
        """
        Initialize Git sync.

        Args:
            config: Application configuration
        """
        self.config = config
        self.repo: Optional[git.Repo] = None
        self.repo_path = Path(config.config_path)

    async def sync(self) -> bool:
        """
        Synchronize repository (clone or pull).

        Returns:
            bool: True if successful
        """
        try:
            if self.repo_path.exists() and (self.repo_path / ".git").exists():
                return await self._pull()
            else:
                return await self._clone()
        except Exception as e:
            logger.exception(f"Git sync failed: {e}")
            return False

    async def _clone(self) -> bool:
        """
        Clone repository.

        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Cloning {self.config.github_repo} to {self.repo_path}")

            # Ensure parent directory exists
            self.repo_path.parent.mkdir(parents=True, exist_ok=True)

            # Remove existing directory if present
            if self.repo_path.exists():
                shutil.rmtree(self.repo_path)

            # Clone repository
            await asyncio.to_thread(
                git.Repo.clone_from,
                self.config.repo_url,
                str(self.repo_path),
                branch=self.config.github_branch,
                depth=1,  # Shallow clone
            )

            self.repo = git.Repo(self.repo_path)
            logger.info("Clone successful")

            return True

        except Exception as e:
            logger.exception(f"Clone failed: {e}")
            return False

    async def _pull(self) -> bool:
        """
        Pull latest changes.

        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Pulling latest changes from {self.config.github_repo}")

            self.repo = git.Repo(self.repo_path)
            origin = self.repo.remotes.origin

            # Fetch and pull
            await asyncio.to_thread(origin.fetch)
            await asyncio.to_thread(origin.pull, self.config.github_branch)

            logger.info("Pull successful")

            return True

        except Exception as e:
            logger.exception(f"Pull failed: {e}")
            return False

    def get_current_commit(self) -> Optional[str]:
        """
        Get current commit hash.

        Returns:
            Optional[str]: Commit hash or None
        """
        try:
            if self.repo:
                return self.repo.head.commit.hexsha[:7]
            return None
        except Exception as e:
            logger.error(f"Failed to get commit hash: {e}")
            return None

    def get_commit_info(self) -> dict:
        """
        Get current commit information.

        Returns:
            dict: Commit information
        """
        try:
            if not self.repo:
                return {}

            commit = self.repo.head.commit

            return {
                "hash": commit.hexsha[:7],
                "message": commit.message.strip(),
                "author": str(commit.author),
                "timestamp": commit.committed_datetime.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get commit info: {e}")
            return {}
