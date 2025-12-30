"""ESPHome integration service."""

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional

import aiofiles
import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo, AsyncZeroconf

from app.models.esphome_device import (
    ESPHomeDevice,
    ESPHomeFirmware,
    ESPHomeLog,
    ESPHomeOTAUpdate,
)
from app.utils.logging import log_integration_event

logger = logging.getLogger(__name__)


class ESPHomeIntegration:
    """Service for ESPHome device integration."""

    def __init__(self, db: AsyncSession):
        """
        Initialize ESPHome integration.

        Args:
            db: Database session
        """
        self.db = db

    async def discover_devices(self, timeout: int = 10) -> List[Dict]:
        """
        Discover ESPHome devices on the network using mDNS.

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            List[Dict]: Discovered devices
        """
        discovered = []

        try:
            aiozc = AsyncZeroconf()

            class ESPHomeListener:
                def __init__(self):
                    self.devices = []

                def add_service(self, zc, service_type, name):
                    asyncio.ensure_future(self.async_add_service(zc, service_type, name))

                async def async_add_service(self, zc, service_type, name):
                    info = AsyncServiceInfo(service_type, name)
                    await info.async_request(zc, 3000)

                    if info:
                        # Parse ESPHome device info
                        addresses = [
                            f"{addr[0]}.{addr[1]}.{addr[2]}.{addr[3]}"
                            for addr in info.addresses
                        ]

                        device = {
                            "name": name.replace("._esphomelib._tcp.local.", ""),
                            "ip_address": addresses[0] if addresses else None,
                            "port": info.port,
                            "mac_address": info.properties.get(b"mac", b"").decode(),
                            "platform": info.properties.get(b"platform", b"").decode(),
                            "esphome_version": info.properties.get(b"version", b"").decode(),
                        }
                        self.devices.append(device)

                def remove_service(self, zc, service_type, name):
                    pass

                def update_service(self, zc, service_type, name):
                    pass

            listener = ESPHomeListener()
            browser = AsyncServiceBrowser(
                aiozc.zeroconf, "_esphomelib._tcp.local.", listener
            )

            # Wait for discovery
            await asyncio.sleep(timeout)
            await browser.async_cancel()
            await aiozc.async_close()

            discovered = listener.devices
            log_integration_event(
                "ESPHome",
                "device_discovery",
                True,
                {"discovered_count": len(discovered)},
            )

        except Exception as e:
            logger.exception(f"Failed to discover ESPHome devices: {e}")
            log_integration_event("ESPHome", "device_discovery", False, {"error": str(e)})

        return discovered

    async def sync_discovered_devices(self) -> int:
        """
        Discover and sync ESPHome devices to database.

        Returns:
            int: Number of devices synced
        """
        try:
            discovered = await self.discover_devices()
            synced = 0

            for device_data in discovered:
                # Check if device already exists
                result = await self.db.execute(
                    select(ESPHomeDevice).where(
                        ESPHomeDevice.ip_address == device_data["ip_address"]
                    )
                )
                device = result.scalar_one_or_none()

                if device:
                    # Update existing device
                    device.online = True
                    device.last_seen = datetime.utcnow()
                    device.esphome_version = device_data.get("esphome_version")
                else:
                    # Create new device
                    device = ESPHomeDevice(
                        name=device_data["name"],
                        ip_address=device_data["ip_address"],
                        port=device_data.get("port", 6053),
                        mac_address=device_data.get("mac_address"),
                        platform=device_data.get("platform"),
                        esphome_version=device_data.get("esphome_version"),
                        online=True,
                        last_seen=datetime.utcnow(),
                    )
                    self.db.add(device)

                synced += 1

            await self.db.commit()
            return synced

        except Exception as e:
            logger.exception(f"Failed to sync discovered devices: {e}")
            await self.db.rollback()
            return 0

    async def get_device_info(self, device_id: int) -> Optional[Dict]:
        """
        Get device information from ESPHome API.

        Args:
            device_id: Device ID

        Returns:
            Optional[Dict]: Device info
        """
        try:
            result = await self.db.execute(
                select(ESPHomeDevice).where(ESPHomeDevice.id == device_id)
            )
            device = result.scalar_one_or_none()

            if not device:
                return None

            async with aiohttp.ClientSession() as session:
                # ESPHome native API uses protobuf, but we can use web server endpoint if enabled
                async with session.get(
                    f"http://{device.ip_address}/text_sensor/esphome_version",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "version": data.get("state"),
                            "online": True,
                        }

        except Exception as e:
            logger.exception(f"Failed to get device info: {e}")
            return None

    async def check_device_status(self, device_id: int) -> bool:
        """
        Check if device is online.

        Args:
            device_id: Device ID

        Returns:
            bool: True if online
        """
        try:
            result = await self.db.execute(
                select(ESPHomeDevice).where(ESPHomeDevice.id == device_id)
            )
            device = result.scalar_one_or_none()

            if not device:
                return False

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{device.ip_address}:{device.port}/",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    online = response.status == 200

                    # Update device status
                    device.online = online
                    device.last_seen = datetime.utcnow() if online else device.last_seen
                    device.connection_status = "connected" if online else "disconnected"
                    await self.db.commit()

                    return online

        except Exception as e:
            logger.debug(f"Device offline or unreachable: {e}")
            # Update device as offline
            result = await self.db.execute(
                select(ESPHomeDevice).where(ESPHomeDevice.id == device_id)
            )
            device = result.scalar_one_or_none()
            if device:
                device.online = False
                device.connection_status = "disconnected"
                await self.db.commit()
            return False

    async def upload_firmware_ota(
        self, device_id: int, firmware_path: str, password: Optional[str] = None
    ) -> bool:
        """
        Upload firmware to device via OTA.

        Args:
            device_id: Device ID
            firmware_path: Path to firmware file
            password: OTA password

        Returns:
            bool: Success status
        """
        try:
            result = await self.db.execute(
                select(ESPHomeDevice).where(ESPHomeDevice.id == device_id)
            )
            device = result.scalar_one_or_none()

            if not device:
                logger.error(f"Device {device_id} not found")
                return False

            # Create OTA update record
            ota_update = ESPHomeOTAUpdate(
                device_id=device_id,
                from_version=device.firmware_version,
                to_version="updating",
                firmware_file=firmware_path,
                status="uploading",
                started_at=datetime.utcnow(),
                update_type="ota",
            )
            self.db.add(ota_update)
            await self.db.commit()
            await self.db.refresh(ota_update)

            # Read firmware file
            async with aiofiles.open(firmware_path, "rb") as f:
                firmware_data = await f.read()

            # Upload via HTTP POST to ESPHome OTA endpoint
            async with aiohttp.ClientSession() as session:
                headers = {}
                if password or device.ota_password:
                    headers["Authorization"] = f"Basic {password or device.ota_password}"

                async with session.post(
                    f"http://{device.ip_address}:{device.port}/update",
                    data=firmware_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=300),  # 5 minutes
                ) as response:
                    if response.status == 200:
                        # Update OTA record
                        ota_update.status = "installing"
                        ota_update.progress = 100
                        await self.db.commit()

                        # Wait for device to reboot and come back online
                        await asyncio.sleep(30)

                        # Check if device is back online
                        online = await self.check_device_status(device_id)

                        if online:
                            ota_update.status = "completed"
                            ota_update.success = True
                            ota_update.completed_at = datetime.utcnow()
                            ota_update.duration_seconds = int(
                                (
                                    ota_update.completed_at - ota_update.started_at
                                ).total_seconds()
                            )

                            log_integration_event(
                                "ESPHome",
                                "ota_update",
                                True,
                                {"device_id": device_id, "device_name": device.name},
                            )
                        else:
                            ota_update.status = "failed"
                            ota_update.error_message = "Device did not come back online"
                            log_integration_event(
                                "ESPHome",
                                "ota_update",
                                False,
                                {"device_id": device_id, "error": "Device offline after update"},
                            )

                        await self.db.commit()
                        return online
                    else:
                        error_text = await response.text()
                        ota_update.status = "failed"
                        ota_update.error_message = f"HTTP {response.status}: {error_text}"
                        ota_update.completed_at = datetime.utcnow()
                        await self.db.commit()

                        log_integration_event(
                            "ESPHome",
                            "ota_update",
                            False,
                            {"device_id": device_id, "error": error_text},
                        )
                        return False

        except Exception as e:
            logger.exception(f"Failed to upload firmware OTA: {e}")
            # Update OTA record
            if ota_update:
                ota_update.status = "failed"
                ota_update.error_message = str(e)
                ota_update.completed_at = datetime.utcnow()
                await self.db.commit()
            return False

    async def get_device_logs(
        self, device_id: int, limit: int = 100, level: Optional[str] = None
    ) -> List[ESPHomeLog]:
        """
        Get device logs.

        Args:
            device_id: Device ID
            limit: Maximum number of logs
            level: Filter by log level

        Returns:
            List[ESPHomeLog]: Device logs
        """
        try:
            query = select(ESPHomeLog).where(ESPHomeLog.device_id == device_id)

            if level:
                query = query.where(ESPHomeLog.level == level)

            query = query.order_by(ESPHomeLog.created_at.desc()).limit(limit)

            result = await self.db.execute(query)
            logs = list(result.scalars().all())

            return logs

        except Exception as e:
            logger.exception(f"Failed to get device logs: {e}")
            return []

    async def stream_device_logs(self, device_id: int):
        """
        Stream real-time logs from device.

        Args:
            device_id: Device ID

        Yields:
            str: Log lines
        """
        try:
            result = await self.db.execute(
                select(ESPHomeDevice).where(ESPHomeDevice.id == device_id)
            )
            device = result.scalar_one_or_none()

            if not device:
                return

            # Connect to ESPHome logs endpoint (websocket or HTTP streaming)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{device.ip_address}:{device.port}/logs",
                    timeout=aiohttp.ClientTimeout(total=None),
                ) as response:
                    async for line in response.content:
                        if line:
                            log_line = line.decode().strip()
                            yield log_line

                            # Parse and store log
                            # Simple parsing - ESPHome logs format: [LEVEL][component] message
                            # This would need more sophisticated parsing in production
                            await self._store_log(device_id, log_line)

        except Exception as e:
            logger.exception(f"Failed to stream device logs: {e}")

    async def _store_log(self, device_id: int, log_line: str):
        """
        Parse and store log line.

        Args:
            device_id: Device ID
            log_line: Raw log line
        """
        try:
            # Simple log parsing (production would use regex)
            level = "info"
            message = log_line
            component = None

            if "[" in log_line:
                parts = log_line.split("]", 2)
                if len(parts) >= 2:
                    level = parts[0].strip("[").lower()
                    if len(parts) >= 3:
                        component = parts[1].strip("[")
                        message = parts[2].strip()

            log = ESPHomeLog(
                device_id=device_id,
                level=level,
                message=message,
                component=component,
                device_timestamp=datetime.utcnow(),
            )
            self.db.add(log)
            await self.db.commit()

        except Exception as e:
            logger.debug(f"Failed to store log: {e}")

    async def get_update_history(self, device_id: int) -> List[ESPHomeOTAUpdate]:
        """
        Get OTA update history for device.

        Args:
            device_id: Device ID

        Returns:
            List[ESPHomeOTAUpdate]: Update history
        """
        try:
            result = await self.db.execute(
                select(ESPHomeOTAUpdate)
                .where(ESPHomeOTAUpdate.device_id == device_id)
                .order_by(ESPHomeOTAUpdate.created_at.desc())
            )
            updates = list(result.scalars().all())
            return updates

        except Exception as e:
            logger.exception(f"Failed to get update history: {e}")
            return []

    async def validate_firmware(self, firmware_path: str) -> Optional[Dict]:
        """
        Validate firmware file.

        Args:
            firmware_path: Path to firmware file

        Returns:
            Optional[Dict]: Firmware metadata
        """
        try:
            async with aiofiles.open(firmware_path, "rb") as f:
                content = await f.read()

            # Calculate hash
            file_hash = hashlib.sha256(content).hexdigest()
            file_size = len(content)

            # Basic validation - check file size
            if file_size < 1024:  # Less than 1KB is suspicious
                return None

            return {
                "file_hash": file_hash,
                "file_size": file_size,
                "valid": True,
            }

        except Exception as e:
            logger.exception(f"Failed to validate firmware: {e}")
            return None

    async def create_firmware_record(
        self,
        name: str,
        version: str,
        platform: str,
        file_path: str,
        esphome_version: str,
        **kwargs,
    ) -> Optional[ESPHomeFirmware]:
        """
        Create firmware record in database.

        Args:
            name: Firmware name
            version: Firmware version
            platform: Platform (esp32, esp8266)
            file_path: Path to firmware file
            esphome_version: ESPHome version used
            **kwargs: Additional fields

        Returns:
            Optional[ESPHomeFirmware]: Created firmware record
        """
        try:
            # Validate firmware
            validation = await self.validate_firmware(file_path)
            if not validation:
                return None

            firmware = ESPHomeFirmware(
                name=name,
                version=version,
                platform=platform,
                file_path=file_path,
                file_size=validation["file_size"],
                file_hash=validation["file_hash"],
                esphome_version=esphome_version,
                build_date=datetime.utcnow(),
                **kwargs,
            )

            self.db.add(firmware)
            await self.db.commit()
            await self.db.refresh(firmware)

            return firmware

        except Exception as e:
            logger.exception(f"Failed to create firmware record: {e}")
            await self.db.rollback()
            return None
