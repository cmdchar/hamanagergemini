"""GitHub deployment service for syncing HA configurations."""

import asyncio
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from git import Repo, Actor
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.github import GitHubIntegration
from app.models.server import Server
from app.utils.logging import logger
from app.utils.ssh import execute_ssh_command, list_remote_files, read_remote_file

settings = get_settings()


class GitHubDeploymentService:
    """Service for managing GitHub-based deployments."""

    def __init__(self, db: AsyncSession):
        """Initialize service."""
        self.db = db
        self.github_integration = GitHubIntegration(db)

    async def push_to_github(
        self, server: Server, commit_message: Optional[str] = None
    ) -> Dict:
        """
        Push server configuration to GitHub.

        Args:
            server: Server instance with github_repo and github_branch
            commit_message: Optional custom commit message

        Returns:
            dict: Push result with success status and details
        """
        if not server.github_repo or not server.github_branch:
            return {
                "success": False,
                "error": "Server is not linked to a GitHub repository",
            }

        temp_dir = None
        try:
            # Create temporary directory for repo
            temp_dir = Path(tempfile.mkdtemp(prefix="ha_push_"))
            logger.info(f"Created temp directory: {temp_dir}")

            # Parse repository info
            repo_info = self._parse_repo_url(server.github_repo)
            if not repo_info:
                return {
                    "success": False,
                    "error": "Invalid repository URL format",
                }

            # Clone repository
            clone_url = self._build_clone_url(
                repo_info["owner"], repo_info["repo"]
            )
            logger.info(f"Cloning repository: {clone_url}")

            repo = await asyncio.to_thread(
                Repo.clone_from,
                clone_url,
                str(temp_dir),
                branch=server.github_branch,
            )

            # Download config files from server
            logger.info(f"Downloading files from server {server.name}")
            download_result = await self._download_server_config(
                server, temp_dir
            )

            if not download_result["success"]:
                return download_result

            # Check if there are changes
            if not repo.is_dirty(untracked_files=True):
                logger.info("No changes to commit")
                return {
                    "success": True,
                    "message": "No changes to push",
                    "files_changed": 0,
                }

            # Stage all changes
            repo.git.add(A=True)

            # Create commit
            if not commit_message:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_message = f"Update HA config from {server.name} - {timestamp}"

            # Set commit author
            author = Actor("HA Config Manager", "noreply@haconfig.local")
            repo.index.commit(commit_message, author=author, committer=author)

            # Count changed files
            files_changed = len(repo.head.commit.stats.files)
            commit_sha = repo.head.commit.hexsha[:7]

            # Push to GitHub
            logger.info(f"Pushing to GitHub: {server.github_branch}")
            origin = repo.remotes.origin
            await asyncio.to_thread(origin.push, server.github_branch)

            logger.info(
                f"Successfully pushed {files_changed} files to GitHub (commit: {commit_sha})"
            )

            return {
                "success": True,
                "message": f"Pushed {files_changed} files to GitHub",
                "files_changed": files_changed,
                "commit_sha": commit_sha,
                "commit_message": commit_message,
            }

        except Exception as e:
            logger.exception(f"Failed to push to GitHub: {e}")
            return {
                "success": False,
                "error": str(e),
            }

        finally:
            # Cleanup temp directory
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory: {e}")

    async def pull_from_github(self, server: Server) -> Dict:
        """
        Pull configuration from GitHub to server.

        Args:
            server: Server instance with github_repo and github_branch

        Returns:
            dict: Pull result with success status and details
        """
        if not server.github_repo or not server.github_branch:
            return {
                "success": False,
                "error": "Server is not linked to a GitHub repository",
            }

        temp_dir = None
        try:
            # Create temporary directory for repo
            temp_dir = Path(tempfile.mkdtemp(prefix="ha_pull_"))
            logger.info(f"Created temp directory: {temp_dir}")

            # Parse repository info
            repo_info = self._parse_repo_url(server.github_repo)
            if not repo_info:
                return {
                    "success": False,
                    "error": "Invalid repository URL format",
                }

            # Clone repository
            clone_url = self._build_clone_url(
                repo_info["owner"], repo_info["repo"]
            )
            logger.info(f"Cloning repository: {clone_url}")

            repo = await asyncio.to_thread(
                Repo.clone_from,
                clone_url,
                str(temp_dir),
                branch=server.github_branch,
                depth=1,  # Shallow clone
            )

            commit_sha = repo.head.commit.hexsha[:7]
            commit_message = repo.head.commit.message.strip()

            # Upload config files to server
            logger.info(f"Uploading files to server {server.name}")
            upload_result = await self._upload_to_server(server, temp_dir)

            if not upload_result["success"]:
                return upload_result

            logger.info(
                f"Successfully pulled from GitHub (commit: {commit_sha})"
            )

            return {
                "success": True,
                "message": f"Pulled configuration from GitHub",
                "files_synced": upload_result.get("files_synced", 0),
                "commit_sha": commit_sha,
                "commit_message": commit_message,
            }

        except Exception as e:
            logger.exception(f"Failed to pull from GitHub: {e}")
            return {
                "success": False,
                "error": str(e),
            }

        finally:
            # Cleanup temp directory
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory: {e}")

    async def _download_server_config(
        self, server: Server, target_dir: Path
    ) -> Dict:
        """
        Download configuration files from server via SSH.

        Args:
            server: Server instance
            target_dir: Local directory to download files to

        Returns:
            dict: Download result
        """
        visited_paths = set()
        max_depth = 10

        async def download_recursive(remote_path: str, local_dir: Path, depth: int = 0):
            """Recursively download files from a directory."""
            nonlocal files_downloaded

            # Prevent infinite recursion
            if depth > max_depth:
                logger.warning(f"Max recursion depth reached at {remote_path}")
                return

            # Normalize path and check if already visited
            normalized_path = remote_path.rstrip('/')
            if normalized_path in visited_paths:
                logger.debug(f"Skipping already visited path: {normalized_path}")
                return
            visited_paths.add(normalized_path)

            try:
                files = await list_remote_files(server, remote_path)
            except Exception as e:
                logger.warning(f"Failed to list directory {remote_path}: {e}")
                return

            for file_info in files:
                file_name = file_info["name"]
                file_path = file_info["path"]

                # Skip . and .. entries
                if file_name in ('.', '..'):
                    continue

                # Skip certain files/dirs
                if self._should_skip_file(file_name):
                    continue

                if file_info["is_dir"]:
                    # Create local directory
                    local_subdir = local_dir / file_name
                    local_subdir.mkdir(parents=True, exist_ok=True)

                    # Recursively download subdirectory
                    await download_recursive(file_path, local_subdir, depth + 1)
                else:
                    # Download file
                    try:
                        content = await read_remote_file(server, file_path)
                        local_path = local_dir / file_name
                        local_path.write_text(content, encoding="utf-8")
                        files_downloaded += 1
                        logger.debug(f"Downloaded: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to read {file_path}: {e}")
                        continue

        try:
            files_downloaded = 0

            # Start recursive download from config path
            await download_recursive(server.config_path, target_dir)

            logger.info(f"Downloaded {files_downloaded} files from server")

            return {
                "success": True,
                "files_downloaded": files_downloaded,
            }

        except Exception as e:
            logger.exception(f"Failed to download server config: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _upload_to_server(self, server: Server, source_dir: Path) -> Dict:
        """
        Upload configuration files to server via SSH.

        Args:
            server: Server instance
            source_dir: Local directory with files to upload

        Returns:
            dict: Upload result
        """
        max_depth = 10

        async def upload_recursive(local_dir: Path, remote_base: str, depth: int = 0):
            """Recursively upload files to a directory."""
            nonlocal files_synced

            # Prevent infinite recursion
            if depth > max_depth:
                logger.warning(f"Max recursion depth reached at {local_dir}")
                return

            for local_path in local_dir.iterdir():
                # Skip symlinks to prevent loops
                if local_path.is_symlink():
                    continue

                if self._should_skip_file(local_path.name):
                    continue

                if local_path.is_dir():
                    # Create remote directory and upload recursively
                    remote_subdir = f"{remote_base}/{local_path.name}"
                    await upload_recursive(local_path, remote_subdir, depth + 1)
                else:
                    # Upload file
                    try:
                        content = local_path.read_text(encoding="utf-8")
                        remote_path = f"{remote_base}/{local_path.name}"
                        await write_remote_file(server, remote_path, content)
                        files_synced += 1
                        logger.debug(f"Uploaded: {remote_path}")
                    except Exception as e:
                        logger.warning(f"Failed to upload {local_path}: {e}")
                        continue

        try:
            from app.utils.ssh import write_remote_file

            files_synced = 0

            # Start recursive upload
            await upload_recursive(source_dir, server.config_path)

            logger.info(f"Synced {files_synced} files to server")

            return {
                "success": True,
                "files_synced": files_synced,
            }

        except Exception as e:
            logger.exception(f"Failed to upload to server: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _parse_repo_url(self, repo_url: str) -> Optional[Dict[str, str]]:
        """
        Parse repository URL to extract owner and repo name.

        Args:
            repo_url: Repository URL or owner/repo format

        Returns:
            dict: {owner, repo} or None if invalid
        """
        try:
            # Handle owner/repo format
            if "/" in repo_url and not repo_url.startswith("http"):
                parts = repo_url.split("/")
                return {"owner": parts[0], "repo": parts[1]}

            # Handle full URL format
            if "github.com" in repo_url:
                # Remove .git suffix if present
                repo_url = repo_url.rstrip("/").replace(".git", "")
                parts = repo_url.split("/")
                return {"owner": parts[-2], "repo": parts[-1]}

            return None

        except Exception as e:
            logger.error(f"Failed to parse repo URL: {e}")
            return None

    def _build_clone_url(self, owner: str, repo: str) -> str:
        """
        Build authenticated clone URL using GitHub token.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            str: Clone URL with authentication
        """
        if settings.github_token:
            return f"https://{settings.github_token}@github.com/{owner}/{repo}.git"
        else:
            return f"https://github.com/{owner}/{repo}.git"

    def _should_skip_file(self, filename: str) -> bool:
        """
        Check if file should be skipped during sync.

        Args:
            filename: File name to check

        Returns:
            bool: True if file should be skipped
        """
        skip_patterns = [
            # Sensitive files
            "secrets.yaml",
            "secrets.yml",
            # Database files
            ".db",
            ".db-shm",
            ".db-wal",
            ".sqlite",
            "home-assistant_v2.db",
            # Logs
            ".log",
            "home-assistant.log",
            "OZW_Log.txt",
            # Temporary files
            ".pid",
            ".pyc",
            # HA metadata
            ".HA_VERSION",
            ".uuid",
            ".cloud",
            # Directories (will be matched as filenames)
            ".storage",
            "deps",
            "tts",
        ]

        for pattern in skip_patterns:
            if filename.endswith(pattern) or filename == pattern:
                return True

        return False
