"""Configuration management."""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Application configuration."""

    github_repo: str
    github_token: str
    github_branch: str
    server_id: str
    orchestrator_url: Optional[str]
    auto_sync: bool
    sync_interval: int
    config_path: str
    ha_config_dir: str = "/config"

    @classmethod
    def load(cls) -> "Config":
        """
        Load configuration from options.json or environment variables.

        Returns:
            Config: Configuration instance
        """
        options_file = Path("/data/options.json")

        if options_file.exists():
            logger.info("Loading configuration from options.json")
            with open(options_file) as f:
                data = json.load(f)
        else:
            logger.warning("Options file not found, using environment variables")
            data = {
                "github_repo": os.getenv("GITHUB_REPO", ""),
                "github_token": os.getenv("GITHUB_TOKEN", ""),
                "github_branch": os.getenv("GITHUB_BRANCH", "main"),
                "server_id": os.getenv("SERVER_ID", "unknown"),
                "orchestrator_url": os.getenv("ORCHESTRATOR_URL"),
                "auto_sync": os.getenv("AUTO_SYNC", "true").lower() == "true",
                "sync_interval": int(os.getenv("SYNC_INTERVAL", "300")),
                "config_path": os.getenv("CONFIG_PATH", "/data/ha-config"),
            }

        return cls(
            github_repo=data.get("github_repo", ""),
            github_token=data.get("github_token", ""),
            github_branch=data.get("github_branch", "main"),
            server_id=data.get("server_id", "unknown"),
            orchestrator_url=data.get("orchestrator_url"),
            auto_sync=data.get("auto_sync", True),
            sync_interval=data.get("sync_interval", 300),
            config_path=data.get("config_path", "/data/ha-config"),
        )

    @property
    def repo_url(self) -> str:
        """
        Get repository URL with authentication.

        Returns:
            str: Repository URL
        """
        if self.github_token:
            return f"https://{self.github_token}@github.com/{self.github_repo}.git"
        return f"https://github.com/{self.github_repo}.git"
