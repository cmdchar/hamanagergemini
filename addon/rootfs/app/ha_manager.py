"""Home Assistant management module."""

import asyncio
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict

from app.config import Config

logger = logging.getLogger(__name__)


class HAManager:
    """Manages Home Assistant operations."""

    def __init__(self, config: Config):
        """
        Initialize HA manager.

        Args:
            config: Application configuration
        """
        self.config = config
        self.ha_config_dir = Path(config.ha_config_dir)
        self.repo_config_dir = Path(config.config_path)

    async def validate_config(self) -> Dict:
        """
        Validate Home Assistant configuration.

        Returns:
            Dict: Validation result with success status and output
        """
        try:
            logger.info("Validating Home Assistant configuration...")

            # Try HA CLI command first (for HA OS)
            result = await asyncio.create_subprocess_exec(
                "ha", "core", "check",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.wait()

            if result.returncode == 0:
                logger.info("Configuration is valid")
                return {
                    "success": True,
                    "output": stdout.decode("utf-8") if stdout else "",
                    "method": "ha_cli",
                }
            elif result.returncode != 127:  # Command exists but failed
                logger.error(f"Configuration validation failed: {stderr.decode('utf-8') if stderr else ''}")
                return {
                    "success": False,
                    "output": stdout.decode("utf-8") if stdout else "",
                    "error": stderr.decode("utf-8") if stderr else "",
                    "method": "ha_cli",
                }

            # Try hass command for container/core installations
            result = await asyncio.create_subprocess_exec(
                "hass", "--script", "check_config", "-c", str(self.ha_config_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.wait()

            if result.returncode == 0:
                logger.info("Configuration is valid (hass)")
                return {
                    "success": True,
                    "output": stdout.decode("utf-8") if stdout else "",
                    "method": "hass_script",
                }
            else:
                logger.error(f"Configuration validation failed (hass): {stderr.decode('utf-8') if stderr else ''}")
                return {
                    "success": False,
                    "output": stdout.decode("utf-8") if stdout else "",
                    "error": stderr.decode("utf-8") if stderr else "",
                    "method": "hass_script",
                }

        except Exception as e:
            logger.exception(f"Validation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "exception",
            }

    async def sync_files(self) -> bool:
        """
        Synchronize files from repository to HA config directory.

        Returns:
            bool: True if successful
        """
        try:
            src_dir = self.repo_config_dir
            dst_dir = self.ha_config_dir

            if not src_dir.exists():
                logger.error(f"Source directory {src_dir} not found")
                return False

            logger.info(f"Syncing files from {src_dir} to {dst_dir}")

            # Exclude patterns
            exclude_patterns = [".git", "__pycache__", "*.pyc", ".gitignore"]

            # Sync files
            files_copied = 0
            for item in src_dir.rglob("*"):
                if item.is_file():
                    # Check if file should be excluded
                    if any(pattern in str(item) for pattern in exclude_patterns):
                        continue

                    # Calculate relative path
                    rel_path = item.relative_to(src_dir)
                    dst_file = dst_dir / rel_path

                    # Create parent directory if needed
                    dst_file.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    await asyncio.to_thread(shutil.copy2, item, dst_file)
                    files_copied += 1
                    logger.debug(f"Copied {item} -> {dst_file}")

            logger.info(f"File sync completed: {files_copied} files copied")

            return True

        except Exception as e:
            logger.exception(f"File sync error: {e}")
            return False

    async def restart_homeassistant(self) -> bool:
        """
        Restart Home Assistant.

        Returns:
            bool: True if successful
        """
        try:
            logger.info("Restarting Home Assistant...")

            # Try HA CLI restart
            result = await asyncio.create_subprocess_exec(
                "ha", "core", "restart",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await result.wait()

            if result.returncode == 0:
                logger.info("Restart command sent successfully")
                return True
            else:
                logger.error(f"Restart failed with code {result.returncode}")
                return False

        except Exception as e:
            logger.exception(f"Restart error: {e}")
            return False

    async def get_ha_version(self) -> str:
        """
        Get Home Assistant version.

        Returns:
            str: HA version or "unknown"
        """
        try:
            result = await asyncio.create_subprocess_exec(
                "ha", "core", "info",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await result.wait()

            if result.returncode == 0 and stdout:
                # Parse version from output
                import json

                data = json.loads(stdout.decode("utf-8"))
                return data.get("data", {}).get("version", "unknown")

            return "unknown"

        except Exception as e:
            logger.error(f"Failed to get HA version: {e}")
            return "unknown"
