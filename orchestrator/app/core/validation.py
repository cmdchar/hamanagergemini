"""Configuration validation service."""

import asyncio
from typing import Dict, Optional

import asyncssh

from app.models.server import Server
from app.utils.logging import logger
from app.utils.security import decrypt_value


class ConfigValidator:
    """Service for validating Home Assistant configurations."""

    async def validate_config(self, server: Server) -> Dict:
        """
        Validate Home Assistant configuration on a server.

        Args:
            server: Server to validate configuration on

        Returns:
            Dict: Validation result with success status and output
        """
        try:
            logger.info(f"Validating configuration on server {server.name}")

            # Prepare connection arguments
            connect_kwargs = {
                "host": server.ssh_host or server.host,
                "port": server.ssh_port or 22,
                "username": server.ssh_user,
                "known_hosts": None,
            }

            if server.ssh_key_path:
                passphrase = None
                if server.ssh_key_passphrase:
                    try:
                        passphrase = decrypt_value(server.ssh_key_passphrase)
                    except Exception:
                        logger.error(f"Failed to decrypt SSH key passphrase for server {server.id}")
                        return {"success": False, "error": "Failed to decrypt SSH key passphrase. Please update server settings."}
                
                real_key_path, real_passphrase = get_usable_key_path(server.ssh_key_path, passphrase)
                connect_kwargs["client_keys"] = [real_key_path]
                if real_passphrase:
                    connect_kwargs["passphrase"] = real_passphrase
            elif server.ssh_password:
                try:
                    connect_kwargs["password"] = decrypt_value(server.ssh_password) if server.ssh_password else None
                except Exception:
                    logger.error(f"Failed to decrypt SSH password for server {server.id}")
                    return {"success": False, "error": "Failed to decrypt SSH password. Please update server settings."}

            # Connect to server via SSH
            async with asyncssh.connect(**connect_kwargs) as conn:
                # Try HA CLI command first (for HA OS)
                result = await conn.run("ha core check", check=False, timeout=120)

                if result.exit_status == 0:
                    return {
                        "success": True,
                        "output": result.stdout,
                        "method": "ha_cli",
                    }
                elif result.exit_status != 127:  # Command exists but failed
                    return {
                        "success": False,
                        "output": result.stdout,
                        "error": result.stderr,
                        "method": "ha_cli",
                    }

                # Try hass --script check_config for container/core installations
                result = await conn.run(
                    "hass --script check_config -c /config",
                    check=False,
                    timeout=120,
                )

                if result.exit_status == 0:
                    return {
                        "success": True,
                        "output": result.stdout,
                        "method": "hass_script",
                    }
                else:
                    return {
                        "success": False,
                        "output": result.stdout,
                        "error": result.stderr,
                        "method": "hass_script",
                    }

        except Exception as e:
            logger.exception(f"Failed to validate config on {server.name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "method": "exception",
            }

    async def validate_yaml_syntax(self, yaml_content: str) -> Dict:
        """
        Validate YAML syntax.

        Args:
            yaml_content: YAML content to validate

        Returns:
            Dict: Validation result
        """
        try:
            import yaml

            # Try to parse YAML
            yaml.safe_load(yaml_content)

            return {
                "success": True,
                "message": "YAML syntax is valid",
            }

        except yaml.YAMLError as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Invalid YAML syntax",
            }

    async def validate_automation(self, automation_yaml: str) -> Dict:
        """
        Validate automation YAML structure.

        Args:
            automation_yaml: Automation YAML content

        Returns:
            Dict: Validation result
        """
        try:
            import yaml

            # Parse YAML
            automation = yaml.safe_load(automation_yaml)

            # Check required fields
            if not isinstance(automation, dict):
                return {
                    "success": False,
                    "error": "Automation must be a dictionary",
                }

            required_fields = ["trigger", "action"]
            missing_fields = [
                field for field in required_fields if field not in automation
            ]

            if missing_fields:
                return {
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                }

            return {
                "success": True,
                "message": "Automation structure is valid",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def check_entity_exists(
        self, server: Server, entity_id: str
    ) -> Dict:
        """
        Check if an entity exists on a Home Assistant server.

        Args:
            server: Server to check
            entity_id: Entity ID to check

        Returns:
            Dict: Result with exists status
        """
        try:
            import httpx

            # Build HA API URL
            url = f"http://{server.host}:{server.ha_port or 8123}/api/states/{entity_id}"

            headers = {}
            if server.ha_token:
                headers["Authorization"] = f"Bearer {server.ha_token}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return {
                        "exists": True,
                        "entity": response.json(),
                    }
                elif response.status_code == 404:
                    return {
                        "exists": False,
                        "message": f"Entity {entity_id} not found",
                    }
                else:
                    return {
                        "exists": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                    }

        except Exception as e:
            logger.exception(f"Failed to check entity on {server.name}: {str(e)}")
            return {
                "exists": False,
                "error": str(e),
            }
