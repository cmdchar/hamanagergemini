"""WLED integration service."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
from aiozeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.wled_device import WLEDDevice
from app.utils.logging import log_integration_event

settings = get_settings()
logger = logging.getLogger(__name__)


class WLEDIntegration:
    """Service for WLED device integration."""

    def __init__(self, db: AsyncSession):
        """
        Initialize WLED integration.

        Args:
            db: Database session
        """
        self.db = db
        self.discovered_devices: Dict[str, dict] = {}

    async def discover_devices(self, timeout: int = 5) -> List[WLEDDevice]:
        """
        Discover WLED devices on the network using mDNS.

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            List[WLEDDevice]: Discovered devices
        """
        try:
            logger.info("Starting WLED device discovery...")

            # Use aiozeroconf for async mDNS discovery
            zeroconf = Zeroconf()

            def on_service_state_change(
                zeroconf: Zeroconf,
                service_type: str,
                name: str,
                state_change: ServiceStateChange,
            ) -> None:
                """Handle service state change."""
                if state_change is ServiceStateChange.Added:
                    info = zeroconf.get_service_info(service_type, name)
                    if info:
                        device_info = {
                            "name": name.replace("._http._tcp.local.", ""),
                            "ip": str(info.parsed_addresses()[0]) if info.parsed_addresses() else None,
                            "port": info.port,
                        }
                        if device_info["ip"]:
                            self.discovered_devices[device_info["ip"]] = device_info

            # Browse for WLED devices (they advertise as _http._tcp)
            browser = ServiceBrowser(
                zeroconf, "_http._tcp.local.", handlers=[on_service_state_change]
            )

            # Wait for discovery
            await asyncio.sleep(timeout)

            await zeroconf.close()

            # Verify discovered devices are actually WLED
            wled_devices = []
            for ip, info in self.discovered_devices.items():
                device_info = await self.get_device_info(ip)
                if device_info:
                    wled_devices.append(await self._create_or_update_device(ip, device_info))

            log_integration_event(
                "WLED",
                "device_discovery",
                True,
                {"devices_found": len(wled_devices)},
            )

            return wled_devices

        except Exception as e:
            logger.exception(f"WLED discovery failed: {e}")
            log_integration_event("WLED", "device_discovery", False, {"error": str(e)})
            return []

    async def get_device_info(self, ip_address: str) -> Optional[Dict]:
        """
        Get device information from WLED API.

        Args:
            ip_address: Device IP address

        Returns:
            Optional[Dict]: Device info or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{ip_address}/json/info",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.debug(f"Failed to get device info from {ip_address}: {e}")
            return None

    async def get_device_state(self, ip_address: str) -> Optional[Dict]:
        """
        Get current state from WLED device.

        Args:
            ip_address: Device IP address

        Returns:
            Optional[Dict]: Device state or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{ip_address}/json/state",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Failed to get device state from {ip_address}: {e}")
            return None

    async def set_device_state(
        self, ip_address: str, state: Dict
    ) -> bool:
        """
        Set device state via WLED API.

        Args:
            ip_address: Device IP address
            state: State to set

        Returns:
            bool: True if successful
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://{ip_address}/json/state",
                    json=state,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    success = response.status == 200
                    log_integration_event(
                        "WLED",
                        "set_state",
                        success,
                        {"ip": ip_address, "state": state},
                    )
                    return success
        except Exception as e:
            logger.error(f"Failed to set device state on {ip_address}: {e}")
            log_integration_event(
                "WLED", "set_state", False, {"ip": ip_address, "error": str(e)}
            )
            return False

    async def turn_on(self, device_id: int) -> bool:
        """
        Turn on a WLED device.

        Args:
            device_id: Device ID

        Returns:
            bool: True if successful
        """
        device = await self._get_device(device_id)
        if not device:
            return False

        return await self.set_device_state(device.ip_address, {"on": True})

    async def turn_off(self, device_id: int) -> bool:
        """
        Turn off a WLED device.

        Args:
            device_id: Device ID

        Returns:
            bool: True if successful
        """
        device = await self._get_device(device_id)
        if not device:
            return False

        return await self.set_device_state(device.ip_address, {"on": False})

    async def set_brightness(self, device_id: int, brightness: int) -> bool:
        """
        Set device brightness (0-255).

        Args:
            device_id: Device ID
            brightness: Brightness value (0-255)

        Returns:
            bool: True if successful
        """
        device = await self._get_device(device_id)
        if not device:
            return False

        return await self.set_device_state(
            device.ip_address, {"bri": max(0, min(255, brightness))}
        )

    async def set_preset(self, device_id: int, preset_id: int) -> bool:
        """
        Apply a preset to the device.

        Args:
            device_id: Device ID
            preset_id: Preset ID (1-250)

        Returns:
            bool: True if successful
        """
        device = await self._get_device(device_id)
        if not device:
            return False

        return await self.set_device_state(device.ip_address, {"ps": preset_id})

    async def sync_devices(
        self, device_ids: List[int], sync_group: str = "christmas"
    ) -> bool:
        """
        Enable sync for multiple devices.

        Args:
            device_ids: List of device IDs to sync
            sync_group: Sync group name

        Returns:
            bool: True if successful
        """
        try:
            # Update sync settings for all devices
            for device_id in device_ids:
                device = await self._get_device(device_id)
                if device:
                    device.sync_enabled = True
                    device.sync_group = sync_group
                    device.sync_master = device_id == device_ids[0]  # First is master

            await self.db.commit()

            log_integration_event(
                "WLED",
                "sync_enabled",
                True,
                {"devices": len(device_ids), "group": sync_group},
            )

            return True

        except Exception as e:
            logger.error(f"Failed to sync devices: {e}")
            return False

    async def apply_to_all_synced(
        self, sync_group: str, state: Dict
    ) -> int:
        """
        Apply state to all devices in a sync group.

        Args:
            sync_group: Sync group name
            state: State to apply

        Returns:
            int: Number of devices updated
        """
        try:
            result = await self.db.execute(
                select(WLEDDevice).where(
                    WLEDDevice.sync_enabled == True,
                    WLEDDevice.sync_group == sync_group,
                )
            )
            devices = list(result.scalars().all())

            # Apply state to all devices in parallel
            tasks = [
                self.set_device_state(device.ip_address, state) for device in devices
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = sum(1 for r in results if r is True)

            log_integration_event(
                "WLED",
                "apply_to_synced",
                True,
                {"group": sync_group, "devices": len(devices), "success": success_count},
            )

            return success_count

        except Exception as e:
            logger.error(f"Failed to apply state to synced devices: {e}")
            return 0

    async def _get_device(self, device_id: int) -> Optional[WLEDDevice]:
        """Get device by ID."""
        result = await self.db.execute(
            select(WLEDDevice).where(WLEDDevice.id == device_id)
        )
        return result.scalar_one_or_none()

    async def _create_or_update_device(
        self, ip_address: str, device_info: Dict
    ) -> WLEDDevice:
        """Create or update device in database."""
        mac = device_info.get("mac")

        # Try to find existing device
        if mac:
            result = await self.db.execute(
                select(WLEDDevice).where(WLEDDevice.mac_address == mac)
            )
            device = result.scalar_one_or_none()
        else:
            result = await self.db.execute(
                select(WLEDDevice).where(WLEDDevice.ip_address == ip_address)
            )
            device = result.scalar_one_or_none()

        if device:
            # Update existing device
            device.ip_address = ip_address
            device.name = device_info.get("name", device.name)
            device.version = device_info.get("ver")
            device.led_count = device_info.get("leds", {}).get("count", 0)
            device.brand = device_info.get("brand")
            device.product = device_info.get("product")
            device.is_online = True
            device.last_seen = datetime.utcnow()
        else:
            # Create new device
            device = WLEDDevice(
                name=device_info.get("name", f"WLED-{ip_address}"),
                ip_address=ip_address,
                mac_address=mac,
                version=device_info.get("ver"),
                led_count=device_info.get("leds", {}).get("count", 0),
                brand=device_info.get("brand"),
                product=device_info.get("product"),
                is_online=True,
                last_seen=datetime.utcnow(),
            )
            self.db.add(device)

        await self.db.commit()
        await self.db.refresh(device)

        return device
