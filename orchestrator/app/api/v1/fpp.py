"""Falcon Player device management API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.integrations.fpp import FPPIntegration
from app.models.fpp_device import FPPDevice, FPPPlaylist, FPPSequence
from app.models.user import User
from app.schemas.fpp import (
    FPPDeviceCreate,
    FPPDeviceResponse,
    FPPDeviceUpdate,
    FPPDiscoveryRequest,
    FPPDiscoveryResponse,
    FPPMultiSyncRequest,
    FPPMultiSyncResponse,
    FPPPlaylistControl,
    FPPPlaylistCreate,
    FPPPlaylistResponse,
    FPPPlaylistUpdate,
    FPPSequenceCreate,
    FPPSequenceResponse,
    FPPSequenceUpdate,
    FPPStatusResponse,
    FPPSyncRequest,
    FPPSyncResponse,
    FPPVolumeControl,
)

router = APIRouter(prefix="/fpp", tags=["fpp"])


def get_fpp_service(db: AsyncSession = Depends(get_db)) -> FPPIntegration:
    """Get FPP integration service."""
    return FPPIntegration(db)


# Device endpoints

@router.get("/devices", response_model=List[FPPDeviceResponse])
async def list_devices(
    skip: int = 0,
    limit: int = 100,
    is_online: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all FPP devices."""
    query = select(FPPDevice)

    if is_online is not None:
        query = query.where(FPPDevice.is_online == is_online)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    devices = list(result.scalars().all())

    return [
        FPPDeviceResponse(
            id=device.id,
            name=device.name,
            hostname=device.hostname,
            ip_address=device.ip_address,
            port=device.port,
            server_id=device.server_id,
            version=device.version,
            platform=device.platform,
            model=device.model,
            mode=device.mode,
            is_online=device.is_online,
            last_seen=device.last_seen,
            status=device.status,
            current_playlist=device.current_playlist,
            current_sequence=device.current_sequence,
            seconds_played=device.seconds_played,
            seconds_remaining=device.seconds_remaining,
            capabilities=device.capabilities,
            volume=device.volume,
            brightness=device.brightness,
            multisync_enabled=device.multisync_enabled,
            multisync_master=device.multisync_master,
            multisync_peers=device.multisync_peers,
            created_at=device.created_at,
            updated_at=device.updated_at,
        )
        for device in devices
    ]


@router.post("/devices", response_model=FPPDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: FPPDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new FPP device."""
    device = FPPDevice(
        name=device_data.name,
        hostname=device_data.hostname,
        ip_address=device_data.ip_address,
        port=device_data.port,
        server_id=device_data.server_id,
        version=device_data.version,
        platform=device_data.platform,
        model=device_data.model,
        mode=device_data.mode,
    )

    db.add(device)
    await db.commit()
    await db.refresh(device)

    return FPPDeviceResponse(
        id=device.id,
        name=device.name,
        hostname=device.hostname,
        ip_address=device.ip_address,
        port=device.port,
        server_id=device.server_id,
        version=device.version,
        platform=device.platform,
        model=device.model,
        mode=device.mode,
        is_online=device.is_online,
        last_seen=device.last_seen,
        status=device.status,
        current_playlist=device.current_playlist,
        current_sequence=device.current_sequence,
        seconds_played=device.seconds_played,
        seconds_remaining=device.seconds_remaining,
        capabilities=device.capabilities,
        volume=device.volume,
        brightness=device.brightness,
        multisync_enabled=device.multisync_enabled,
        multisync_master=device.multisync_master,
        multisync_peers=device.multisync_peers,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


@router.get("/devices/{device_id}", response_model=FPPDeviceResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get FPP device by ID."""
    result = await db.execute(select(FPPDevice).where(FPPDevice.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FPP device {device_id} not found",
        )

    return FPPDeviceResponse(
        id=device.id,
        name=device.name,
        hostname=device.hostname,
        ip_address=device.ip_address,
        port=device.port,
        server_id=device.server_id,
        version=device.version,
        platform=device.platform,
        model=device.model,
        mode=device.mode,
        is_online=device.is_online,
        last_seen=device.last_seen,
        status=device.status,
        current_playlist=device.current_playlist,
        current_sequence=device.current_sequence,
        seconds_played=device.seconds_played,
        seconds_remaining=device.seconds_remaining,
        capabilities=device.capabilities,
        volume=device.volume,
        brightness=device.brightness,
        multisync_enabled=device.multisync_enabled,
        multisync_master=device.multisync_master,
        multisync_peers=device.multisync_peers,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


@router.put("/devices/{device_id}", response_model=FPPDeviceResponse)
async def update_device(
    device_id: int,
    device_data: FPPDeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update FPP device."""
    result = await db.execute(select(FPPDevice).where(FPPDevice.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FPP device {device_id} not found",
        )

    # Update fields
    update_data = device_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    await db.commit()
    await db.refresh(device)

    return FPPDeviceResponse(
        id=device.id,
        name=device.name,
        hostname=device.hostname,
        ip_address=device.ip_address,
        port=device.port,
        server_id=device.server_id,
        version=device.version,
        platform=device.platform,
        model=device.model,
        mode=device.mode,
        is_online=device.is_online,
        last_seen=device.last_seen,
        status=device.status,
        current_playlist=device.current_playlist,
        current_sequence=device.current_sequence,
        seconds_played=device.seconds_played,
        seconds_remaining=device.seconds_remaining,
        capabilities=device.capabilities,
        volume=device.volume,
        brightness=device.brightness,
        multisync_enabled=device.multisync_enabled,
        multisync_master=device.multisync_master,
        multisync_peers=device.multisync_peers,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete FPP device."""
    result = await db.execute(select(FPPDevice).where(FPPDevice.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FPP device {device_id} not found",
        )

    await db.delete(device)
    await db.commit()


@router.post("/discover", response_model=FPPDiscoveryResponse)
async def discover_devices(
    discovery_request: FPPDiscoveryRequest,
    current_user: User = Depends(get_current_user),
    fpp_service: FPPIntegration = Depends(get_fpp_service),
):
    """Discover FPP devices on the network using mDNS."""
    devices = await fpp_service.discover_devices(timeout=discovery_request.timeout)

    return FPPDiscoveryResponse(
        devices_found=len(devices),
        devices=[
            FPPDeviceResponse(
                id=device.id,
                name=device.name,
                hostname=device.hostname,
                ip_address=device.ip_address,
                port=device.port,
                server_id=device.server_id,
                version=device.version,
                platform=device.platform,
                model=device.model,
                mode=device.mode,
                is_online=device.is_online,
                last_seen=device.last_seen,
                status=device.status,
                current_playlist=device.current_playlist,
                current_sequence=device.current_sequence,
                seconds_played=device.seconds_played,
                seconds_remaining=device.seconds_remaining,
                capabilities=device.capabilities,
                volume=device.volume,
                brightness=device.brightness,
                multisync_enabled=device.multisync_enabled,
                multisync_master=device.multisync_master,
                multisync_peers=device.multisync_peers,
                created_at=device.created_at,
                updated_at=device.updated_at,
            )
            for device in devices
        ],
    )


@router.get("/devices/{device_id}/status", response_model=FPPStatusResponse)
async def get_device_status(
    device_id: int,
    current_user: User = Depends(get_current_user),
    fpp_service: FPPIntegration = Depends(get_fpp_service),
    db: AsyncSession = Depends(get_db),
):
    """Get current status of FPP device."""
    result = await db.execute(select(FPPDevice).where(FPPDevice.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FPP device {device_id} not found",
        )

    status_data = await fpp_service.get_device_status(device.ip_address, device.port)

    if status_data is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not reach device at {device.ip_address}",
        )

    return FPPStatusResponse(
        status=status_data.get("status_name", "unknown"),
        current_playlist=status_data.get("current_playlist"),
        current_sequence=status_data.get("current_sequence"),
        seconds_played=status_data.get("seconds_played", 0),
        seconds_remaining=status_data.get("seconds_remaining", 0),
        volume=status_data.get("volume", device.volume),
    )


@router.post("/devices/{device_id}/playlist/start")
async def start_playlist(
    device_id: int,
    playlist_control: FPPPlaylistControl,
    current_user: User = Depends(get_current_user),
    fpp_service: FPPIntegration = Depends(get_fpp_service),
):
    """Start a playlist on FPP device."""
    success = await fpp_service.start_playlist(
        device_id, playlist_control.playlist_name, playlist_control.repeat
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to start playlist",
        )

    return {"success": True, "message": "Playlist started"}


@router.post("/devices/{device_id}/playlist/stop")
async def stop_playlist(
    device_id: int,
    current_user: User = Depends(get_current_user),
    fpp_service: FPPIntegration = Depends(get_fpp_service),
):
    """Stop current playlist on FPP device."""
    success = await fpp_service.stop_playlist(device_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to stop playlist",
        )

    return {"success": True, "message": "Playlist stopped"}


@router.post("/devices/{device_id}/volume")
async def set_volume(
    device_id: int,
    volume_control: FPPVolumeControl,
    current_user: User = Depends(get_current_user),
    fpp_service: FPPIntegration = Depends(get_fpp_service),
):
    """Set device volume (0-100)."""
    success = await fpp_service.set_volume(device_id, volume_control.volume)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to set volume",
        )

    return {"success": True, "message": f"Volume set to {volume_control.volume}"}


@router.post("/multisync", response_model=FPPMultiSyncResponse)
async def enable_multisync(
    multisync_request: FPPMultiSyncRequest,
    current_user: User = Depends(get_current_user),
    fpp_service: FPPIntegration = Depends(get_fpp_service),
):
    """Enable MultiSync across FPP devices."""
    success = await fpp_service.enable_multisync(
        multisync_request.master_device_id,
        multisync_request.peer_device_ids,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to enable MultiSync",
        )

    return FPPMultiSyncResponse(
        success=True,
        message="MultiSync enabled",
        master_device_id=multisync_request.master_device_id,
        peer_count=len(multisync_request.peer_device_ids),
    )


@router.post("/sync", response_model=FPPSyncResponse)
async def sync_device_data(
    sync_request: FPPSyncRequest,
    current_user: User = Depends(get_current_user),
    fpp_service: FPPIntegration = Depends(get_fpp_service),
):
    """Sync playlists and sequences from FPP device to database."""
    playlists_synced = 0
    sequences_synced = 0

    if sync_request.sync_playlists:
        playlists_synced = await fpp_service.sync_playlists_to_db(sync_request.device_id)

    if sync_request.sync_sequences:
        sequences_synced = await fpp_service.sync_sequences_to_db(sync_request.device_id)

    return FPPSyncResponse(
        success=True,
        playlists_synced=playlists_synced,
        sequences_synced=sequences_synced,
    )


# Playlist endpoints

@router.get("/playlists", response_model=List[FPPPlaylistResponse])
async def list_playlists(
    device_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all FPP playlists."""
    query = select(FPPPlaylist)

    if device_id:
        query = query.where(FPPPlaylist.device_id == device_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    playlists = list(result.scalars().all())

    return [
        FPPPlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            device_id=playlist.device_id,
            entries=playlist.entries,
            repeat=playlist.repeat,
            shuffle=playlist.shuffle,
            priority=playlist.priority,
            last_played=playlist.last_played,
            play_count=playlist.play_count,
            created_at=playlist.created_at,
            updated_at=playlist.updated_at,
        )
        for playlist in playlists
    ]


@router.post("/playlists", response_model=FPPPlaylistResponse, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    playlist_data: FPPPlaylistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new FPP playlist."""
    playlist = FPPPlaylist(
        name=playlist_data.name,
        description=playlist_data.description,
        device_id=playlist_data.device_id,
        entries=playlist_data.entries,
        repeat=playlist_data.repeat,
        shuffle=playlist_data.shuffle,
        priority=playlist_data.priority,
    )

    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)

    return FPPPlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        device_id=playlist.device_id,
        entries=playlist.entries,
        repeat=playlist.repeat,
        shuffle=playlist.shuffle,
        priority=playlist.priority,
        last_played=playlist.last_played,
        play_count=playlist.play_count,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
    )


# Sequence endpoints

@router.get("/sequences", response_model=List[FPPSequenceResponse])
async def list_sequences(
    device_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all FPP sequences."""
    query = select(FPPSequence)

    if device_id:
        query = query.where(FPPSequence.device_id == device_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    sequences = list(result.scalars().all())

    return [
        FPPSequenceResponse(
            id=sequence.id,
            name=sequence.name,
            filename=sequence.filename,
            device_id=sequence.device_id,
            duration=sequence.duration,
            channel_count=sequence.channel_count,
            frame_count=sequence.frame_count,
            file_size=sequence.file_size,
            media_filename=sequence.media_filename,
            uploaded_at=sequence.uploaded_at,
            last_played=sequence.last_played,
            play_count=sequence.play_count,
            created_at=sequence.created_at,
            updated_at=sequence.updated_at,
        )
        for sequence in sequences
    ]
