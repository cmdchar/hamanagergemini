"""ESPHome API endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.integrations.esphome import ESPHomeIntegration
from app.models.esphome_device import (
    ESPHomeDevice,
    ESPHomeFirmware,
    ESPHomeOTAUpdate,
)
from app.models.user import User
from app.schemas.esphome import (
    ESPHomeBulkUpdateRequest,
    ESPHomeBulkUpdateResponse,
    ESPHomeDeviceCreate,
    ESPHomeDeviceResponse,
    ESPHomeDeviceStatus,
    ESPHomeDeviceUpdate,
    ESPHomeDiscoveryRequest,
    ESPHomeDiscoveryResponse,
    ESPHomeFirmwareCreate,
    ESPHomeFirmwareResponse,
    ESPHomeLogResponse,
    ESPHomeOTAUpdateCreate,
    ESPHomeOTAUpdateResponse,
    ESPHomeStatistics,
)
from app.utils.logging import log_integration_event

router = APIRouter(prefix="/esphome", tags=["esphome"])
logger = logging.getLogger(__name__)


# Device endpoints
@router.post("/devices", response_model=ESPHomeDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    data: ESPHomeDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new ESPHome device."""
    try:
        device = ESPHomeDevice(**data.model_dump())
        db.add(device)
        await db.commit()
        await db.refresh(device)

        log_integration_event(
            "ESPHome",
            "device_created",
            True,
            {"device_id": device.id, "device_name": device.name},
        )

        return device
    except Exception as e:
        logger.exception(f"Failed to create device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create device",
        )


@router.get("/devices", response_model=List[ESPHomeDeviceResponse])
async def list_devices(
    skip: int = 0,
    limit: int = 100,
    online_only: bool = False,
    platform: Optional[str] = None,
    server_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List ESPHome devices."""
    try:
        query = select(ESPHomeDevice)

        if online_only:
            query = query.where(ESPHomeDevice.online == True)

        if platform:
            query = query.where(ESPHomeDevice.platform == platform)

        if server_id:
            query = query.where(ESPHomeDevice.server_id == server_id)

        query = query.order_by(ESPHomeDevice.name).offset(skip).limit(limit)

        result = await db.execute(query)
        devices = list(result.scalars().all())

        return devices
    except Exception as e:
        logger.exception(f"Failed to list devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list devices",
        )


@router.get("/devices/{device_id}", response_model=ESPHomeDeviceResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get device by ID."""
    try:
        result = await db.execute(
            select(ESPHomeDevice).where(ESPHomeDevice.id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        return device
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device",
        )


@router.patch("/devices/{device_id}", response_model=ESPHomeDeviceResponse)
async def update_device(
    device_id: int,
    data: ESPHomeDeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update device."""
    try:
        result = await db.execute(
            select(ESPHomeDevice).where(ESPHomeDevice.id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)

        await db.commit()
        await db.refresh(device)

        return device
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device",
        )


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete device."""
    try:
        result = await db.execute(
            select(ESPHomeDevice).where(ESPHomeDevice.id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        await db.delete(device)
        await db.commit()

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete device",
        )


# Discovery endpoints
@router.post("/discover", response_model=ESPHomeDiscoveryResponse)
async def discover_devices(
    data: ESPHomeDiscoveryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Discover ESPHome devices on network."""
    try:
        integration = ESPHomeIntegration(db)
        devices = await integration.discover_devices(timeout=data.timeout)

        return ESPHomeDiscoveryResponse(
            devices=devices,
            count=len(devices),
        )
    except Exception as e:
        logger.exception(f"Failed to discover devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to discover devices",
        )


@router.post("/discover/sync")
async def sync_discovered_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Discover and sync devices to database."""
    try:
        integration = ESPHomeIntegration(db)
        synced = await integration.sync_discovered_devices()

        return {"synced": synced, "message": f"Synced {synced} devices"}
    except Exception as e:
        logger.exception(f"Failed to sync devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync devices",
        )


# Device status endpoints
@router.get("/devices/{device_id}/status", response_model=ESPHomeDeviceStatus)
async def check_device_status(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check device online status."""
    try:
        integration = ESPHomeIntegration(db)
        online = await integration.check_device_status(device_id)

        result = await db.execute(
            select(ESPHomeDevice).where(ESPHomeDevice.id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        return ESPHomeDeviceStatus(
            device_id=device_id,
            online=online,
            last_seen=device.last_seen,
            connection_status=device.connection_status or "unknown",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to check device status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check device status",
        )


# OTA update endpoints
@router.post("/devices/{device_id}/ota", response_model=ESPHomeOTAUpdateResponse)
async def upload_firmware_ota(
    device_id: int,
    file: UploadFile = File(...),
    password: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload firmware to device via OTA."""
    try:
        # Save uploaded file temporarily
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            integration = ESPHomeIntegration(db)
            success = await integration.upload_firmware_ota(device_id, tmp_path, password)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="OTA update failed",
                )

            # Get the latest update record
            result = await db.execute(
                select(ESPHomeOTAUpdate)
                .where(ESPHomeOTAUpdate.device_id == device_id)
                .order_by(ESPHomeOTAUpdate.created_at.desc())
            )
            update = result.scalar_one_or_none()

            return update

        finally:
            # Clean up temp file
            os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to upload firmware: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload firmware",
        )


@router.get("/devices/{device_id}/updates", response_model=List[ESPHomeOTAUpdateResponse])
async def get_update_history(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get OTA update history for device."""
    try:
        integration = ESPHomeIntegration(db)
        updates = await integration.get_update_history(device_id)

        return updates
    except Exception as e:
        logger.exception(f"Failed to get update history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get update history",
        )


@router.post("/bulk-update", response_model=ESPHomeBulkUpdateResponse)
async def bulk_update_devices(
    data: ESPHomeBulkUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Perform bulk OTA update on multiple devices."""
    try:
        integration = ESPHomeIntegration(db)
        started = []
        failed = []
        errors = {}

        for device_id in data.device_ids:
            try:
                success = await integration.upload_firmware_ota(
                    device_id, data.firmware_file, data.password
                )
                if success:
                    started.append(device_id)
                else:
                    failed.append(device_id)
                    errors[device_id] = "Update failed"
            except Exception as e:
                failed.append(device_id)
                errors[device_id] = str(e)

            # If sequential, wait for completion before next device
            if data.sequential and device_id != data.device_ids[-1]:
                import asyncio
                await asyncio.sleep(60)  # Wait for device to reboot

        return ESPHomeBulkUpdateResponse(
            total=len(data.device_ids),
            started=started,
            failed=failed,
            errors=errors,
        )
    except Exception as e:
        logger.exception(f"Failed to perform bulk update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk update",
        )


# Log endpoints
@router.get("/devices/{device_id}/logs", response_model=List[ESPHomeLogResponse])
async def get_device_logs(
    device_id: int,
    limit: int = 100,
    level: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get device logs."""
    try:
        integration = ESPHomeIntegration(db)
        logs = await integration.get_device_logs(device_id, limit, level)

        return logs
    except Exception as e:
        logger.exception(f"Failed to get device logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device logs",
        )


@router.get("/devices/{device_id}/logs/stream")
async def stream_device_logs(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream real-time device logs."""
    try:
        integration = ESPHomeIntegration(db)

        async def log_generator():
            async for log_line in integration.stream_device_logs(device_id):
                yield f"data: {log_line}\n\n"

        return StreamingResponse(log_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.exception(f"Failed to stream logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stream logs",
        )


# Firmware endpoints
@router.post("/firmwares", response_model=ESPHomeFirmwareResponse, status_code=status.HTTP_201_CREATED)
async def create_firmware(
    data: ESPHomeFirmwareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create firmware record."""
    try:
        integration = ESPHomeIntegration(db)
        firmware = await integration.create_firmware_record(**data.model_dump())

        if not firmware:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid firmware file",
            )

        return firmware
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create firmware: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create firmware",
        )


@router.get("/firmwares", response_model=List[ESPHomeFirmwareResponse])
async def list_firmwares(
    skip: int = 0,
    limit: int = 50,
    platform: Optional[str] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List available firmwares."""
    try:
        query = select(ESPHomeFirmware)

        if platform:
            query = query.where(ESPHomeFirmware.platform == platform)

        if active_only:
            query = query.where(ESPHomeFirmware.is_active == True)

        query = query.order_by(ESPHomeFirmware.build_date.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        firmwares = list(result.scalars().all())

        return firmwares
    except Exception as e:
        logger.exception(f"Failed to list firmwares: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list firmwares",
        )


# Statistics endpoints
@router.get("/statistics", response_model=ESPHomeStatistics)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get ESPHome statistics."""
    try:
        # Device counts
        total_devices = await db.scalar(select(func.count(ESPHomeDevice.id)))
        online_devices = await db.scalar(
            select(func.count(ESPHomeDevice.id)).where(ESPHomeDevice.online == True)
        )

        # Devices by platform
        platform_result = await db.execute(
            select(ESPHomeDevice.platform, func.count(ESPHomeDevice.id))
            .group_by(ESPHomeDevice.platform)
        )
        devices_by_platform = {row[0] or "unknown": row[1] for row in platform_result}

        # Update counts
        total_updates = await db.scalar(select(func.count(ESPHomeOTAUpdate.id)))
        successful_updates = await db.scalar(
            select(func.count(ESPHomeOTAUpdate.id)).where(ESPHomeOTAUpdate.success == True)
        )

        # Average update time
        avg_time = await db.scalar(
            select(func.avg(ESPHomeOTAUpdate.duration_seconds)).where(
                ESPHomeOTAUpdate.success == True
            )
        )

        return ESPHomeStatistics(
            total_devices=total_devices or 0,
            online_devices=online_devices or 0,
            offline_devices=(total_devices or 0) - (online_devices or 0),
            devices_by_platform=devices_by_platform,
            total_updates=total_updates or 0,
            successful_updates=successful_updates or 0,
            failed_updates=(total_updates or 0) - (successful_updates or 0),
            average_update_time=float(avg_time) if avg_time else None,
        )
    except Exception as e:
        logger.exception(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics",
        )
