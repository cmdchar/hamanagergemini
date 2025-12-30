"""Tailscale integration service."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.tailscale import TailscaleACL, TailscaleDevice, TailscaleNetwork, TailscaleRoute
from app.utils.logging import log_integration_event

settings = get_settings()
logger = logging.getLogger(__name__)


class TailscaleIntegration:
    """Service for Tailscale VPN integration."""

    API_BASE_URL = "https://api.tailscale.com/api/v2"

    def __init__(self, db: AsyncSession):
        """
        Initialize Tailscale integration.

        Args:
            db: Database session
        """
        self.db = db

    async def get_network(self, network_id: int) -> Optional[TailscaleNetwork]:
        """Get network by ID."""
        result = await self.db.execute(
            select(TailscaleNetwork).where(TailscaleNetwork.id == network_id)
        )
        return result.scalar_one_or_none()

    async def list_devices(self, network_id: int) -> List[Dict]:
        """
        List all devices in Tailscale network.

        Args:
            network_id: Network ID

        Returns:
            List[Dict]: List of devices
        """
        network = await self.get_network(network_id)
        if not network:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {network.api_key}"}
                async with session.get(
                    f"{self.API_BASE_URL}/tailnet/{network.tailnet}/devices",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("devices", [])
                    else:
                        logger.error(f"Failed to list devices: {response.status}")
                        return []
        except Exception as e:
            logger.exception(f"Failed to list Tailscale devices: {e}")
            return []

    async def sync_devices(self, network_id: int) -> int:
        """
        Sync devices from Tailscale API to database.

        Args:
            network_id: Network ID

        Returns:
            int: Number of devices synced
        """
        try:
            devices_data = await self.list_devices(network_id)
            synced_count = 0

            for device_data in devices_data:
                # Check if device exists
                device_id = device_data.get("id")
                result = await self.db.execute(
                    select(TailscaleDevice).where(TailscaleDevice.device_id == device_id)
                )
                device = result.scalar_one_or_none()

                # Extract addresses
                addresses = device_data.get("addresses", [])
                tailscale_ip = next((addr for addr in addresses if addr.startswith("100.")), "")
                ipv6_address = next((addr for addr in addresses if ":" in addr), None)

                if device:
                    # Update existing device
                    device.hostname = device_data.get("hostname", "")
                    device.name = device_data.get("name", device_data.get("hostname", ""))
                    device.tailscale_ip = tailscale_ip
                    device.ipv6_address = ipv6_address
                    device.dns_name = device_data.get("dnsName")
                    device.os = device_data.get("os")
                    device.os_version = device_data.get("osVersion")
                    device.client_version = device_data.get("clientVersion")
                    device.user_email = device_data.get("user")
                    device.user_display_name = device_data.get("userName")
                    device.is_online = not device_data.get("offline", False)
                    device.last_seen = (
                        datetime.fromisoformat(device_data["lastSeen"].replace("Z", "+00:00"))
                        if device_data.get("lastSeen")
                        else None
                    )
                    device.expires = (
                        datetime.fromisoformat(device_data["expires"].replace("Z", "+00:00"))
                        if device_data.get("expires")
                        else None
                    )
                    device.is_exit_node = device_data.get("isExitNode", False)
                    device.advertised_routes = device_data.get("advertisedRoutes", [])
                    device.allowed_ips = device_data.get("allowedIPs", [])
                    device.tags = device_data.get("tags", [])
                    device.raw_data = device_data
                else:
                    # Create new device
                    device = TailscaleDevice(
                        network_id=network_id,
                        device_id=device_id,
                        node_id=device_data.get("nodeId", device_id),
                        hostname=device_data.get("hostname", ""),
                        name=device_data.get("name", device_data.get("hostname", "")),
                        tailscale_ip=tailscale_ip,
                        ipv6_address=ipv6_address,
                        dns_name=device_data.get("dnsName"),
                        os=device_data.get("os"),
                        os_version=device_data.get("osVersion"),
                        client_version=device_data.get("clientVersion"),
                        user_email=device_data.get("user"),
                        user_display_name=device_data.get("userName"),
                        is_online=not device_data.get("offline", False),
                        last_seen=(
                            datetime.fromisoformat(device_data["lastSeen"].replace("Z", "+00:00"))
                            if device_data.get("lastSeen")
                            else None
                        ),
                        expires=(
                            datetime.fromisoformat(device_data["expires"].replace("Z", "+00:00"))
                            if device_data.get("expires")
                            else None
                        ),
                        is_exit_node=device_data.get("isExitNode", False),
                        advertised_routes=device_data.get("advertisedRoutes", []),
                        allowed_ips=device_data.get("allowedIPs", []),
                        tags=device_data.get("tags", []),
                        raw_data=device_data,
                    )
                    self.db.add(device)

                synced_count += 1

            # Update network
            network = await self.get_network(network_id)
            if network:
                network.last_synced = datetime.utcnow()
                network.device_count = synced_count

            await self.db.commit()

            log_integration_event(
                "Tailscale",
                "sync_devices",
                True,
                {"network_id": network_id, "devices_synced": synced_count},
            )

            return synced_count

        except Exception as e:
            logger.exception(f"Failed to sync Tailscale devices: {e}")
            log_integration_event(
                "Tailscale",
                "sync_devices",
                False,
                {"network_id": network_id, "error": str(e)},
            )
            return 0

    async def delete_device(self, network_id: int, device_id: str) -> bool:
        """
        Delete a device from Tailscale network.

        Args:
            network_id: Network ID
            device_id: Tailscale device ID

        Returns:
            bool: True if successful
        """
        network = await self.get_network(network_id)
        if not network:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {network.api_key}"}
                async with session.delete(
                    f"{self.API_BASE_URL}/device/{device_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    success = response.status == 200

                    log_integration_event(
                        "Tailscale",
                        "delete_device",
                        success,
                        {"network_id": network_id, "device_id": device_id},
                    )

                    return success
        except Exception as e:
            logger.exception(f"Failed to delete Tailscale device: {e}")
            return False

    async def authorize_device(self, network_id: int, device_id: str) -> bool:
        """
        Authorize a device in Tailscale network.

        Args:
            network_id: Network ID
            device_id: Tailscale device ID

        Returns:
            bool: True if successful
        """
        network = await self.get_network(network_id)
        if not network:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {network.api_key}"}
                async with session.post(
                    f"{self.API_BASE_URL}/device/{device_id}/authorized",
                    headers=headers,
                    json={"authorized": True},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    success = response.status == 200

                    log_integration_event(
                        "Tailscale",
                        "authorize_device",
                        success,
                        {"network_id": network_id, "device_id": device_id},
                    )

                    return success
        except Exception as e:
            logger.exception(f"Failed to authorize Tailscale device: {e}")
            return False

    async def set_device_tags(self, network_id: int, device_id: str, tags: List[str]) -> bool:
        """
        Set tags for a device.

        Args:
            network_id: Network ID
            device_id: Tailscale device ID
            tags: List of tags

        Returns:
            bool: True if successful
        """
        network = await self.get_network(network_id)
        if not network:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {network.api_key}"}
                async with session.post(
                    f"{self.API_BASE_URL}/device/{device_id}/tags",
                    headers=headers,
                    json={"tags": tags},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    success = response.status == 200

                    log_integration_event(
                        "Tailscale",
                        "set_device_tags",
                        success,
                        {"network_id": network_id, "device_id": device_id, "tags": tags},
                    )

                    return success
        except Exception as e:
            logger.exception(f"Failed to set Tailscale device tags: {e}")
            return False

    async def enable_route(self, network_id: int, device_id: str, subnet: str) -> bool:
        """
        Enable a subnet route on a device.

        Args:
            network_id: Network ID
            device_id: Tailscale device ID
            subnet: Subnet in CIDR notation

        Returns:
            bool: True if successful
        """
        network = await self.get_network(network_id)
        if not network:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {network.api_key}"}
                async with session.post(
                    f"{self.API_BASE_URL}/device/{device_id}/routes",
                    headers=headers,
                    json={"routes": [subnet]},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    success = response.status == 200

                    log_integration_event(
                        "Tailscale",
                        "enable_route",
                        success,
                        {"network_id": network_id, "device_id": device_id, "subnet": subnet},
                    )

                    return success
        except Exception as e:
            logger.exception(f"Failed to enable Tailscale route: {e}")
            return False

    async def get_acl(self, network_id: int) -> Optional[Dict]:
        """
        Get ACL policy for network.

        Args:
            network_id: Network ID

        Returns:
            Optional[Dict]: ACL policy or None
        """
        network = await self.get_network(network_id)
        if not network:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {network.api_key}"}
                async with session.get(
                    f"{self.API_BASE_URL}/tailnet/{network.tailnet}/acl",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.exception(f"Failed to get Tailscale ACL: {e}")
            return None

    async def update_acl(self, network_id: int, acl_policy: Dict) -> bool:
        """
        Update ACL policy for network.

        Args:
            network_id: Network ID
            acl_policy: ACL policy dictionary

        Returns:
            bool: True if successful
        """
        network = await self.get_network(network_id)
        if not network:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {network.api_key}",
                    "Content-Type": "application/json",
                }
                async with session.post(
                    f"{self.API_BASE_URL}/tailnet/{network.tailnet}/acl",
                    headers=headers,
                    json=acl_policy,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    success = response.status == 200

                    log_integration_event(
                        "Tailscale",
                        "update_acl",
                        success,
                        {"network_id": network_id},
                    )

                    return success
        except Exception as e:
            logger.exception(f"Failed to update Tailscale ACL: {e}")
            return False

    async def get_dns_nameservers(self, network_id: int) -> Optional[Dict]:
        """
        Get DNS nameservers for network.

        Args:
            network_id: Network ID

        Returns:
            Optional[Dict]: DNS configuration or None
        """
        network = await self.get_network(network_id)
        if not network:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {network.api_key}"}
                async with session.get(
                    f"{self.API_BASE_URL}/tailnet/{network.tailnet}/dns/nameservers",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.exception(f"Failed to get Tailscale DNS: {e}")
            return None

    async def set_dns_nameservers(self, network_id: int, nameservers: List[str]) -> bool:
        """
        Set DNS nameservers for network.

        Args:
            network_id: Network ID
            nameservers: List of DNS server IPs

        Returns:
            bool: True if successful
        """
        network = await self.get_network(network_id)
        if not network:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {network.api_key}",
                    "Content-Type": "application/json",
                }
                async with session.post(
                    f"{self.API_BASE_URL}/tailnet/{network.tailnet}/dns/nameservers",
                    headers=headers,
                    json={"dns": nameservers},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    success = response.status == 200

                    log_integration_event(
                        "Tailscale",
                        "set_dns_nameservers",
                        success,
                        {"network_id": network_id, "nameservers": nameservers},
                    )

                    return success
        except Exception as e:
            logger.exception(f"Failed to set Tailscale DNS: {e}")
            return False
