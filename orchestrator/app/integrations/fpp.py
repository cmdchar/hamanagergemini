"""Falcon Player integration service."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from aiozeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.fpp_device import FPPDevice, FPPPlaylist, FPPSequence
from app.utils.logging import log_integration_event

settings = get_settings()
logger = logging.getLogger(__name__)


class FPPIntegration:
    """Service for Falcon Player integration."""

    def __init__(self, db: AsyncSession):
        """
        Initialize FPP integration.

        Args:
            db: Database session
        """
        self.db = db
        self.discovered_devices: Dict[str, dict] = {}

    async def discover_devices(self, timeout: int = 5) -> List[FPPDevice]:
        """
        Discover FPP devices on the network using mDNS.

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            List[FPPDevice]: Discovered devices
        """
        try:
            logger.info("Starting FPP device discovery...")

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
                            "hostname": info.server if info.server else name,
                            "ip": str(info.parsed_addresses()[0]) if info.parsed_addresses() else None,
                            "port": info.port,
                        }
                        if device_info["ip"]:
                            self.discovered_devices[device_info["ip"]] = device_info

            # Browse for FPP devices (they advertise as _http._tcp or _fpp._tcp)
            browser = ServiceBrowser(
                zeroconf, "_http._tcp.local.", handlers=[on_service_state_change]
            )

            # Wait for discovery
            await asyncio.sleep(timeout)

            await zeroconf.close()

            # Verify discovered devices are actually FPP
            fpp_devices = []
            for ip, info in self.discovered_devices.items():
                device_info = await self.get_device_info(ip)
                if device_info and self._is_fpp_device(device_info):
                    fpp_devices.append(await self._create_or_update_device(ip, device_info))

            log_integration_event(
                "FPP",
                "device_discovery",
                True,
                {"devices_found": len(fpp_devices)},
            )

            return fpp_devices

        except Exception as e:
            logger.exception(f"FPP discovery failed: {e}")
            log_integration_event("FPP", "device_discovery", False, {"error": str(e)})
            return []

    def _is_fpp_device(self, device_info: Dict) -> bool:
        """
        Check if device info indicates FPP device.

        Args:
            device_info: Device information dictionary

        Returns:
            bool: True if FPP device
        """
        return "fppd" in device_info or "version" in device_info

    async def get_device_info(self, ip_address: str, port: int = 80) -> Optional[Dict]:
        """
        Get device information from FPP API.

        Args:
            ip_address: Device IP address
            port: Device port (default 80)

        Returns:
            Optional[Dict]: Device info or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{ip_address}:{port}/api/system/info",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.debug(f"Failed to get device info from {ip_address}: {e}")
            return None

    async def get_device_status(self, ip_address: str, port: int = 80) -> Optional[Dict]:
        """
        Get current status from FPP device.

        Args:
            ip_address: Device IP address
            port: Device port

        Returns:
            Optional[Dict]: Device status or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{ip_address}:{port}/api/fppd/status",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Failed to get device status from {ip_address}: {e}")
            return None

    async def start_playlist(
        self, device_id: int, playlist_name: str, repeat: bool = False
    ) -> bool:
        """
        Start a playlist on FPP device.

        Args:
            device_id: Device ID
            playlist_name: Name of playlist to start
            repeat: Whether to repeat playlist

        Returns:
            bool: True if successful
        """
        device = await self._get_device(device_id)
        if not device:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{device.ip_address}:{device.port}/api/playlist/{playlist_name}/start",
                    params={"repeat": 1 if repeat else 0},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    success = response.status == 200
                    log_integration_event(
                        "FPP",
                        "start_playlist",
                        success,
                        {"device": device.name, "playlist": playlist_name},
                    )
                    return success
        except Exception as e:
            logger.error(f"Failed to start playlist on {device.name}: {e}")
            log_integration_event(
                "FPP", "start_playlist", False, {"device": device.name, "error": str(e)}
            )
            return False

    async def stop_playlist(self, device_id: int) -> bool:
        """
        Stop current playlist on FPP device.

        Args:
            device_id: Device ID

        Returns:
            bool: True if successful
        """
        device = await self._get_device(device_id)
        if not device:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{device.ip_address}:{device.port}/api/playlists/stop",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    success = response.status == 200
                    log_integration_event(
                        "FPP",
                        "stop_playlist",
                        success,
                        {"device": device.name},
                    )
                    return success
        except Exception as e:
            logger.error(f"Failed to stop playlist on {device.name}: {e}")
            return False

    async def get_playlists(self, device_id: int) -> List[Dict]:
        """
        Get all playlists from FPP device.

        Args:
            device_id: Device ID

        Returns:
            List[Dict]: List of playlists
        """
        device = await self._get_device(device_id)
        if not device:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{device.ip_address}:{device.port}/api/playlists",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return []
        except Exception as e:
            logger.error(f"Failed to get playlists from {device.name}: {e}")
            return []

    async def get_sequences(self, device_id: int) -> List[Dict]:
        """
        Get all sequences from FPP device.

        Args:
            device_id: Device ID

        Returns:
            List[Dict]: List of sequences
        """
        device = await self._get_device(device_id)
        if not device:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{device.ip_address}:{device.port}/api/sequence",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return []
        except Exception as e:
            logger.error(f"Failed to get sequences from {device.name}: {e}")
            return []

    async def set_volume(self, device_id: int, volume: int) -> bool:
        """
        Set device volume (0-100).

        Args:
            device_id: Device ID
            volume: Volume level (0-100)

        Returns:
            bool: True if successful
        """
        device = await self._get_device(device_id)
        if not device:
            return False

        volume = max(0, min(100, volume))

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://{device.ip_address}:{device.port}/api/system/volume",
                    json={"volume": volume},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        device.volume = volume
                        await self.db.commit()
                        return True
                    return False
        except Exception as e:
            logger.error(f"Failed to set volume on {device.name}: {e}")
            return False

    async def enable_multisync(
        self, master_id: int, peer_ids: List[int]
    ) -> bool:
        """
        Enable MultiSync across FPP devices.

        Args:
            master_id: Master device ID
            peer_ids: List of peer device IDs

        Returns:
            bool: True if successful
        """
        try:
            master = await self._get_device(master_id)
            if not master:
                return False

            # Get peer IPs
            peer_ips = []
            for peer_id in peer_ids:
                peer = await self._get_device(peer_id)
                if peer:
                    peer_ips.append(peer.ip_address)
                    peer.multisync_enabled = True
                    peer.multisync_master = False

            # Configure master
            master.multisync_enabled = True
            master.multisync_master = True
            master.multisync_peers = peer_ips

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://{master.ip_address}:{master.port}/api/configfile/MultiSync.json",
                    json={"peers": peer_ips},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    success = response.status == 200

            await self.db.commit()

            log_integration_event(
                "FPP",
                "enable_multisync",
                success,
                {"master": master.name, "peers": len(peer_ips)},
            )

            return success

        except Exception as e:
            logger.error(f"Failed to enable multisync: {e}")
            return False

    async def sync_playlists_to_db(self, device_id: int) -> int:
        """
        Sync playlists from FPP device to database.

        Args:
            device_id: Device ID

        Returns:
            int: Number of playlists synced
        """
        playlists = await self.get_playlists(device_id)
        synced_count = 0

        for playlist_data in playlists:
            # Check if playlist exists
            result = await self.db.execute(
                select(FPPPlaylist).where(
                    FPPPlaylist.device_id == device_id,
                    FPPPlaylist.name == playlist_data.get("name"),
                )
            )
            playlist = result.scalar_one_or_none()

            if playlist:
                # Update existing
                playlist.entries = playlist_data.get("entries", [])
            else:
                # Create new
                playlist = FPPPlaylist(
                    name=playlist_data.get("name"),
                    device_id=device_id,
                    entries=playlist_data.get("entries", []),
                )
                self.db.add(playlist)

            synced_count += 1

        await self.db.commit()
        return synced_count

    async def sync_sequences_to_db(self, device_id: int) -> int:
        """
        Sync sequences from FPP device to database.

        Args:
            device_id: Device ID

        Returns:
            int: Number of sequences synced
        """
        sequences = await self.get_sequences(device_id)
        synced_count = 0

        for seq_data in sequences:
            # Check if sequence exists
            result = await self.db.execute(
                select(FPPSequence).where(
                    FPPSequence.device_id == device_id,
                    FPPSequence.filename == seq_data.get("name"),
                )
            )
            sequence = result.scalar_one_or_none()

            if sequence:
                # Update existing
                sequence.duration = seq_data.get("duration", 0)
                sequence.file_size = seq_data.get("size", 0)
            else:
                # Create new
                sequence = FPPSequence(
                    name=seq_data.get("name", "").replace(".fseq", ""),
                    filename=seq_data.get("name"),
                    device_id=device_id,
                    duration=seq_data.get("duration", 0),
                    file_size=seq_data.get("size", 0),
                )
                self.db.add(sequence)

            synced_count += 1

        await self.db.commit()
        return synced_count

    async def _get_device(self, device_id: int) -> Optional[FPPDevice]:
        """Get device by ID."""
        result = await self.db.execute(
            select(FPPDevice).where(FPPDevice.id == device_id)
        )
        return result.scalar_one_or_none()

    async def _create_or_update_device(
        self, ip_address: str, device_info: Dict
    ) -> FPPDevice:
        """Create or update device in database."""
        hostname = device_info.get("HostName", ip_address)

        # Try to find existing device
        result = await self.db.execute(
            select(FPPDevice).where(FPPDevice.hostname == hostname)
        )
        device = result.scalar_one_or_none()

        if not device:
            result = await self.db.execute(
                select(FPPDevice).where(FPPDevice.ip_address == ip_address)
            )
            device = result.scalar_one_or_none()

        if device:
            # Update existing device
            device.ip_address = ip_address
            device.hostname = hostname
            device.name = device_info.get("HostDescription", hostname)
            device.version = device_info.get("Version")
            device.platform = device_info.get("Platform")
            device.model = device_info.get("Model")
            device.mode = device_info.get("Mode", "player")
            device.is_online = True
            device.last_seen = datetime.utcnow()
            device.capabilities = device_info
        else:
            # Create new device
            device = FPPDevice(
                name=device_info.get("HostDescription", hostname),
                hostname=hostname,
                ip_address=ip_address,
                port=80,
                version=device_info.get("Version"),
                platform=device_info.get("Platform"),
                model=device_info.get("Model"),
                mode=device_info.get("Mode", "player"),
                is_online=True,
                last_seen=datetime.utcnow(),
                capabilities=device_info,
            )
            self.db.add(device)

        await self.db.commit()
        await self.db.refresh(device)

        return device
