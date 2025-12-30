"""WLED device management API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.integrations.wled import WLEDIntegration
from app.models.user import User
from app.models.wled_device import WLEDDevice
from app.schemas.wled import (
    WLEDBulkStateResponse,
    WLEDBulkStateUpdate,
    WLEDDeviceCreate,
    WLEDDeviceResponse,
    WLEDDeviceState,
    WLEDDeviceUpdate,
    WLEDDiscoveryRequest,
    WLEDDiscoveryResponse,
    WLEDSyncRequest,
    WLEDSyncResponse,
)

router = APIRouter(prefix="/wled", tags=["wled"])


def get_wled_service(db: AsyncSession = Depends(get_db)) -> WLEDIntegration:
    """Get WLED integration service."""
    return WLEDIntegration(db)


@router.get("/devices", response_model=List[WLEDDeviceResponse])
async def list_devices(
    skip: int = 0,
    limit: int = 100,
    sync_group: Optional[str] = None,
    is_online: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all WLED devices.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        sync_group: Filter by sync group
        is_online: Filter by online status
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[WLEDDeviceResponse]: List of WLED devices
    """
    query = select(WLEDDevice)

    if sync_group:
        query = query.where(WLEDDevice.sync_group == sync_group)
    if is_online is not None:
        query = query.where(WLEDDevice.is_online == is_online)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    devices = list(result.scalars().all())

    return [
        WLEDDeviceResponse(
            id=device.id,
            name=device.name,
            ip_address=device.ip_address,
            mac_address=device.mac_address,
            server_id=device.server_id,
            version=device.version,
            led_count=device.led_count,
            brand=device.brand,
            product=device.product,
            is_online=device.is_online,
            last_seen=device.last_seen,
            current_preset=device.current_preset,
            brightness=device.brightness,
            is_on=device.is_on,
            presets=device.presets,
            segments=device.segments,
            sync_enabled=device.sync_enabled,
            sync_group=device.sync_group,
            sync_master=device.sync_master,
            created_at=device.created_at,
            updated_at=device.updated_at,
        )
        for device in devices
    ]


@router.post("/devices", response_model=WLEDDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: WLEDDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new WLED device.

    Args:
        device_data: Device creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        WLEDDeviceResponse: Created device
    """
    device = WLEDDevice(
        name=device_data.name,
        ip_address=device_data.ip_address,
        mac_address=device_data.mac_address,
        server_id=device_data.server_id,
        version=device_data.version,
        led_count=device_data.led_count,
        brand=device_data.brand,
        product=device_data.product,
    )

    db.add(device)
    await db.commit()
    await db.refresh(device)

    return WLEDDeviceResponse(
        id=device.id,
        name=device.name,
        ip_address=device.ip_address,
        mac_address=device.mac_address,
        server_id=device.server_id,
        version=device.version,
        led_count=device.led_count,
        brand=device.brand,
        product=device.product,
        is_online=device.is_online,
        last_seen=device.last_seen,
        current_preset=device.current_preset,
        brightness=device.brightness,
        is_on=device.is_on,
        presets=device.presets,
        segments=device.segments,
        sync_enabled=device.sync_enabled,
        sync_group=device.sync_group,
        sync_master=device.sync_master,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


@router.get("/devices/{device_id}", response_model=WLEDDeviceResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get WLED device by ID.

    Args:
        device_id: Device ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        WLEDDeviceResponse: Device details

    Raises:
        HTTPException: If device not found
    """
    result = await db.execute(select(WLEDDevice).where(WLEDDevice.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WLED device {device_id} not found",
        )

    return WLEDDeviceResponse(
        id=device.id,
        name=device.name,
        ip_address=device.ip_address,
        mac_address=device.mac_address,
        server_id=device.server_id,
        version=device.version,
        led_count=device.led_count,
        brand=device.brand,
        product=device.product,
        is_online=device.is_online,
        last_seen=device.last_seen,
        current_preset=device.current_preset,
        brightness=device.brightness,
        is_on=device.is_on,
        presets=device.presets,
        segments=device.segments,
        sync_enabled=device.sync_enabled,
        sync_group=device.sync_group,
        sync_master=device.sync_master,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


@router.put("/devices/{device_id}", response_model=WLEDDeviceResponse)
async def update_device(
    device_id: int,
    device_data: WLEDDeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update WLED device.

    Args:
        device_id: Device ID
        device_data: Device update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        WLEDDeviceResponse: Updated device

    Raises:
        HTTPException: If device not found
    """
    result = await db.execute(select(WLEDDevice).where(WLEDDevice.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WLED device {device_id} not found",
        )

    # Update fields
    update_data = device_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    await db.commit()
    await db.refresh(device)

    return WLEDDeviceResponse(
        id=device.id,
        name=device.name,
        ip_address=device.ip_address,
        mac_address=device.mac_address,
        server_id=device.server_id,
        version=device.version,
        led_count=device.led_count,
        brand=device.brand,
        product=device.product,
        is_online=device.is_online,
        last_seen=device.last_seen,
        current_preset=device.current_preset,
        brightness=device.brightness,
        is_on=device.is_on,
        presets=device.presets,
        segments=device.segments,
        sync_enabled=device.sync_enabled,
        sync_group=device.sync_group,
        sync_master=device.sync_master,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete WLED device.

    Args:
        device_id: Device ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If device not found
    """
    result = await db.execute(select(WLEDDevice).where(WLEDDevice.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WLED device {device_id} not found",
        )

    await db.delete(device)
    await db.commit()


@router.post("/discover", response_model=WLEDDiscoveryResponse)
async def discover_devices(
    discovery_request: WLEDDiscoveryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    wled_service: WLEDIntegration = Depends(get_wled_service),
):
    """
    Discover WLED devices on the network using mDNS.

    Args:
        discovery_request: Discovery configuration
        background_tasks: Background task manager
        current_user: Current authenticated user
        wled_service: WLED integration service

    Returns:
        WLEDDiscoveryResponse: Discovery results
    """
    devices = await wled_service.discover_devices(timeout=discovery_request.timeout)

    return WLEDDiscoveryResponse(
        devices_found=len(devices),
        devices=[
            WLEDDeviceResponse(
                id=device.id,
                name=device.name,
                ip_address=device.ip_address,
                mac_address=device.mac_address,
                server_id=device.server_id,
                version=device.version,
                led_count=device.led_count,
                brand=device.brand,
                product=device.product,
                is_online=device.is_online,
                last_seen=device.last_seen,
                current_preset=device.current_preset,
                brightness=device.brightness,
                is_on=device.is_on,
                presets=device.presets,
                segments=device.segments,
                sync_enabled=device.sync_enabled,
                sync_group=device.sync_group,
                sync_master=device.sync_master,
                created_at=device.created_at,
                updated_at=device.updated_at,
            )
            for device in devices
        ],
    )


@router.get("/devices/{device_id}/state")
async def get_device_state(
    device_id: int,
    current_user: User = Depends(get_current_user),
    wled_service: WLEDIntegration = Depends(get_wled_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current state of WLED device.

    Args:
        device_id: Device ID
        current_user: Current authenticated user
        wled_service: WLED integration service
        db: Database session

    Returns:
        dict: Device state

    Raises:
        HTTPException: If device not found or unreachable
    """
    result = await db.execute(select(WLEDDevice).where(WLEDDevice.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WLED device {device_id} not found",
        )

    state = await wled_service.get_device_state(device.ip_address)

    if state is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not reach device at {device.ip_address}",
        )

    return state


@router.post("/devices/{device_id}/state")
async def set_device_state(
    device_id: int,
    state: WLEDDeviceState,
    current_user: User = Depends(get_current_user),
    wled_service: WLEDIntegration = Depends(get_wled_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Set state of WLED device.

    Args:
        device_id: Device ID
        state: State to set
        current_user: Current authenticated user
        wled_service: WLED integration service
        db: Database session

    Returns:
        dict: Success response

    Raises:
        HTTPException: If device not found or update failed
    """
    result = await db.execute(select(WLEDDevice).where(WLEDDevice.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WLED device {device_id} not found",
        )

    state_dict = state.model_dump(exclude_unset=True)
    success = await wled_service.set_device_state(device.ip_address, state_dict)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to update device at {device.ip_address}",
        )

    # Update database state
    if state.on is not None:
        device.is_on = state.on
    if state.bri is not None:
        device.brightness = state.bri
    if state.ps is not None and state.ps > 0:
        device.current_preset = state.ps

    await db.commit()

    return {"success": True, "message": "Device state updated"}


@router.post("/devices/{device_id}/on")
async def turn_on_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    wled_service: WLEDIntegration = Depends(get_wled_service),
):
    """
    Turn on WLED device.

    Args:
        device_id: Device ID
        current_user: Current authenticated user
        wled_service: WLED integration service

    Returns:
        dict: Success response

    Raises:
        HTTPException: If operation failed
    """
    success = await wled_service.turn_on(device_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to turn on device",
        )

    return {"success": True, "message": "Device turned on"}


@router.post("/devices/{device_id}/off")
async def turn_off_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    wled_service: WLEDIntegration = Depends(get_wled_service),
):
    """
    Turn off WLED device.

    Args:
        device_id: Device ID
        current_user: Current authenticated user
        wled_service: WLED integration service

    Returns:
        dict: Success response

    Raises:
        HTTPException: If operation failed
    """
    success = await wled_service.turn_off(device_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to turn off device",
        )

    return {"success": True, "message": "Device turned off"}


@router.post("/devices/{device_id}/brightness")
async def set_device_brightness(
    device_id: int,
    brightness: int,
    current_user: User = Depends(get_current_user),
    wled_service: WLEDIntegration = Depends(get_wled_service),
):
    """
    Set device brightness.

    Args:
        device_id: Device ID
        brightness: Brightness value (0-255)
        current_user: Current authenticated user
        wled_service: WLED integration service

    Returns:
        dict: Success response

    Raises:
        HTTPException: If operation failed
    """
    if not 0 <= brightness <= 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brightness must be between 0 and 255",
        )

    success = await wled_service.set_brightness(device_id, brightness)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to set brightness",
        )

    return {"success": True, "message": f"Brightness set to {brightness}"}


@router.post("/devices/{device_id}/preset")
async def set_device_preset(
    device_id: int,
    preset_id: int,
    current_user: User = Depends(get_current_user),
    wled_service: WLEDIntegration = Depends(get_wled_service),
):
    """
    Apply preset to device.

    Args:
        device_id: Device ID
        preset_id: Preset ID (1-250)
        current_user: Current authenticated user
        wled_service: WLED integration service

    Returns:
        dict: Success response

    Raises:
        HTTPException: If operation failed
    """
    if not 1 <= preset_id <= 250:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preset ID must be between 1 and 250",
        )

    success = await wled_service.set_preset(device_id, preset_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to apply preset",
        )

    return {"success": True, "message": f"Preset {preset_id} applied"}


@router.post("/sync", response_model=WLEDSyncResponse)
async def sync_devices(
    sync_request: WLEDSyncRequest,
    current_user: User = Depends(get_current_user),
    wled_service: WLEDIntegration = Depends(get_wled_service),
):
    """
    Enable sync for multiple devices.

    Args:
        sync_request: Sync configuration
        current_user: Current authenticated user
        wled_service: WLED integration service

    Returns:
        WLEDSyncResponse: Sync result

    Raises:
        HTTPException: If sync failed
    """
    success = await wled_service.sync_devices(
        sync_request.device_ids,
        sync_request.sync_group,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to sync devices",
        )

    return WLEDSyncResponse(
        success=True,
        message=f"Devices synced to group '{sync_request.sync_group}'",
        synced_devices=len(sync_request.device_ids),
        master_device_id=sync_request.device_ids[0],
    )


@router.post("/bulk-state", response_model=WLEDBulkStateResponse)
async def update_bulk_state(
    bulk_update: WLEDBulkStateUpdate,
    current_user: User = Depends(get_current_user),
    wled_service: WLEDIntegration = Depends(get_wled_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Apply state to multiple devices or a sync group.

    Args:
        bulk_update: Bulk state update configuration
        current_user: Current authenticated user
        wled_service: WLED integration service
        db: Database session

    Returns:
        WLEDBulkStateResponse: Bulk update result

    Raises:
        HTTPException: If neither device_ids nor sync_group provided
    """
    if not bulk_update.device_ids and not bulk_update.sync_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either device_ids or sync_group",
        )

    state_dict = bulk_update.state.model_dump(exclude_unset=True)

    if bulk_update.sync_group:
        # Apply to sync group
        devices_updated = await wled_service.apply_to_all_synced(
            bulk_update.sync_group,
            state_dict,
        )
    else:
        # Apply to specific devices
        devices_updated = 0
        for device_id in bulk_update.device_ids:
            result = await db.execute(select(WLEDDevice).where(WLEDDevice.id == device_id))
            device = result.scalar_one_or_none()

            if device:
                success = await wled_service.set_device_state(device.ip_address, state_dict)
                if success:
                    devices_updated += 1

    return WLEDBulkStateResponse(
        success=True,
        devices_updated=devices_updated,
        errors=[],
    )
