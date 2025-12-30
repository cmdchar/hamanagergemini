"""Tailscale network management API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.integrations.tailscale import TailscaleIntegration
from app.models.tailscale import TailscaleACL, TailscaleDevice, TailscaleNetwork, TailscaleRoute
from app.models.user import User
from app.schemas.tailscale import (
    TailscaleACLCreate,
    TailscaleACLPolicy,
    TailscaleACLResponse,
    TailscaleACLUpdate,
    TailscaleDeviceAuthorize,
    TailscaleDeviceDelete,
    TailscaleDeviceResponse,
    TailscaleDeviceTags,
    TailscaleDNSConfig,
    TailscaleDNSResponse,
    TailscaleNetworkCreate,
    TailscaleNetworkResponse,
    TailscaleNetworkStats,
    TailscaleNetworkUpdate,
    TailscaleRouteCreate,
    TailscaleRouteEnable,
    TailscaleRouteResponse,
    TailscaleRouteUpdate,
    TailscaleSyncRequest,
    TailscaleSyncResponse,
)

router = APIRouter(prefix="/tailscale", tags=["tailscale"])


def get_tailscale_service(db: AsyncSession = Depends(get_db)) -> TailscaleIntegration:
    """Get Tailscale integration service."""
    return TailscaleIntegration(db)


# Network endpoints


@router.get("/networks", response_model=List[TailscaleNetworkResponse])
async def list_networks(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all Tailscale networks."""
    query = select(TailscaleNetwork).offset(skip).limit(limit)
    result = await db.execute(query)
    networks = list(result.scalars().all())

    return [
        TailscaleNetworkResponse(
            id=network.id,
            name=network.name,
            tailnet=network.tailnet,
            magic_dns_enabled=network.magic_dns_enabled,
            subnet_routing_enabled=network.subnet_routing_enabled,
            exit_node_enabled=network.exit_node_enabled,
            is_active=network.is_active,
            last_synced=network.last_synced,
            device_count=network.device_count,
            user_count=network.user_count,
            created_at=network.created_at,
            updated_at=network.updated_at,
        )
        for network in networks
    ]


@router.post("/networks", response_model=TailscaleNetworkResponse, status_code=status.HTTP_201_CREATED)
async def create_network(
    network_data: TailscaleNetworkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new Tailscale network."""
    network = TailscaleNetwork(
        name=network_data.name,
        tailnet=network_data.tailnet,
        api_key=network_data.api_key,  # TODO: Encrypt
        oauth_client_id=network_data.oauth_client_id,
        oauth_client_secret=network_data.oauth_client_secret,  # TODO: Encrypt
        magic_dns_enabled=network_data.magic_dns_enabled,
        subnet_routing_enabled=network_data.subnet_routing_enabled,
        exit_node_enabled=network_data.exit_node_enabled,
    )

    db.add(network)
    await db.commit()
    await db.refresh(network)

    return TailscaleNetworkResponse(
        id=network.id,
        name=network.name,
        tailnet=network.tailnet,
        magic_dns_enabled=network.magic_dns_enabled,
        subnet_routing_enabled=network.subnet_routing_enabled,
        exit_node_enabled=network.exit_node_enabled,
        is_active=network.is_active,
        last_synced=network.last_synced,
        device_count=network.device_count,
        user_count=network.user_count,
        created_at=network.created_at,
        updated_at=network.updated_at,
    )


@router.get("/networks/{network_id}", response_model=TailscaleNetworkResponse)
async def get_network(
    network_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get Tailscale network by ID."""
    result = await db.execute(select(TailscaleNetwork).where(TailscaleNetwork.id == network_id))
    network = result.scalar_one_or_none()

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tailscale network {network_id} not found",
        )

    return TailscaleNetworkResponse(
        id=network.id,
        name=network.name,
        tailnet=network.tailnet,
        magic_dns_enabled=network.magic_dns_enabled,
        subnet_routing_enabled=network.subnet_routing_enabled,
        exit_node_enabled=network.exit_node_enabled,
        is_active=network.is_active,
        last_synced=network.last_synced,
        device_count=network.device_count,
        user_count=network.user_count,
        created_at=network.created_at,
        updated_at=network.updated_at,
    )


@router.put("/networks/{network_id}", response_model=TailscaleNetworkResponse)
async def update_network(
    network_id: int,
    network_data: TailscaleNetworkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update Tailscale network."""
    result = await db.execute(select(TailscaleNetwork).where(TailscaleNetwork.id == network_id))
    network = result.scalar_one_or_none()

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tailscale network {network_id} not found",
        )

    # Update fields
    update_data = network_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(network, field, value)

    await db.commit()
    await db.refresh(network)

    return TailscaleNetworkResponse(
        id=network.id,
        name=network.name,
        tailnet=network.tailnet,
        magic_dns_enabled=network.magic_dns_enabled,
        subnet_routing_enabled=network.subnet_routing_enabled,
        exit_node_enabled=network.exit_node_enabled,
        is_active=network.is_active,
        last_synced=network.last_synced,
        device_count=network.device_count,
        user_count=network.user_count,
        created_at=network.created_at,
        updated_at=network.updated_at,
    )


@router.delete("/networks/{network_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_network(
    network_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete Tailscale network."""
    result = await db.execute(select(TailscaleNetwork).where(TailscaleNetwork.id == network_id))
    network = result.scalar_one_or_none()

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tailscale network {network_id} not found",
        )

    await db.delete(network)
    await db.commit()


# Device endpoints


@router.get("/devices", response_model=List[TailscaleDeviceResponse])
async def list_devices(
    network_id: Optional[int] = None,
    is_online: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all Tailscale devices."""
    query = select(TailscaleDevice)

    if network_id:
        query = query.where(TailscaleDevice.network_id == network_id)
    if is_online is not None:
        query = query.where(TailscaleDevice.is_online == is_online)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    devices = list(result.scalars().all())

    return [
        TailscaleDeviceResponse(
            id=device.id,
            network_id=device.network_id,
            server_id=device.server_id,
            device_id=device.device_id,
            node_id=device.node_id,
            hostname=device.hostname,
            name=device.name,
            tailscale_ip=device.tailscale_ip,
            ipv6_address=device.ipv6_address,
            dns_name=device.dns_name,
            os=device.os,
            os_version=device.os_version,
            client_version=device.client_version,
            user_email=device.user_email,
            user_display_name=device.user_display_name,
            is_online=device.is_online,
            last_seen=device.last_seen,
            expires=device.expires,
            is_exit_node=device.is_exit_node,
            is_subnet_router=device.is_subnet_router,
            advertised_routes=device.advertised_routes,
            allowed_ips=device.allowed_ips,
            tags=device.tags,
            created_at=device.created_at,
            updated_at=device.updated_at,
        )
        for device in devices
    ]


@router.post("/sync", response_model=TailscaleSyncResponse)
async def sync_devices(
    sync_request: TailscaleSyncRequest,
    current_user: User = Depends(get_current_user),
    tailscale_service: TailscaleIntegration = Depends(get_tailscale_service),
):
    """Sync devices from Tailscale API."""
    devices_synced = await tailscale_service.sync_devices(sync_request.network_id)

    return TailscaleSyncResponse(
        success=True,
        devices_synced=devices_synced,
        message=f"Synced {devices_synced} devices",
    )


@router.post("/devices/delete")
async def delete_device(
    delete_request: TailscaleDeviceDelete,
    current_user: User = Depends(get_current_user),
    tailscale_service: TailscaleIntegration = Depends(get_tailscale_service),
    db: AsyncSession = Depends(get_db),
):
    """Delete a device from Tailscale network."""
    # Get device to find network_id
    result = await db.execute(
        select(TailscaleDevice).where(TailscaleDevice.device_id == delete_request.device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    success = await tailscale_service.delete_device(device.network_id, delete_request.device_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to delete device",
        )

    return {"success": True, "message": "Device deleted"}


@router.post("/devices/authorize")
async def authorize_device(
    authorize_request: TailscaleDeviceAuthorize,
    current_user: User = Depends(get_current_user),
    tailscale_service: TailscaleIntegration = Depends(get_tailscale_service),
    db: AsyncSession = Depends(get_db),
):
    """Authorize a device in Tailscale network."""
    result = await db.execute(
        select(TailscaleDevice).where(TailscaleDevice.device_id == authorize_request.device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    success = await tailscale_service.authorize_device(device.network_id, authorize_request.device_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to authorize device",
        )

    return {"success": True, "message": "Device authorized"}


@router.post("/devices/tags")
async def set_device_tags(
    tags_request: TailscaleDeviceTags,
    current_user: User = Depends(get_current_user),
    tailscale_service: TailscaleIntegration = Depends(get_tailscale_service),
    db: AsyncSession = Depends(get_db),
):
    """Set tags for a device."""
    result = await db.execute(
        select(TailscaleDevice).where(TailscaleDevice.device_id == tags_request.device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    success = await tailscale_service.set_device_tags(
        device.network_id, tags_request.device_id, tags_request.tags
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to set device tags",
        )

    return {"success": True, "message": "Tags updated"}


@router.post("/routes/enable")
async def enable_route(
    route_request: TailscaleRouteEnable,
    current_user: User = Depends(get_current_user),
    tailscale_service: TailscaleIntegration = Depends(get_tailscale_service),
    db: AsyncSession = Depends(get_db),
):
    """Enable a subnet route on a device."""
    result = await db.execute(
        select(TailscaleDevice).where(TailscaleDevice.device_id == route_request.device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    success = await tailscale_service.enable_route(
        device.network_id, route_request.device_id, route_request.subnet
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to enable route",
        )

    return {"success": True, "message": "Route enabled"}


@router.get("/networks/{network_id}/acl")
async def get_acl(
    network_id: int,
    current_user: User = Depends(get_current_user),
    tailscale_service: TailscaleIntegration = Depends(get_tailscale_service),
):
    """Get ACL policy for network."""
    acl_policy = await tailscale_service.get_acl(network_id)

    if not acl_policy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to get ACL policy",
        )

    return acl_policy


@router.post("/networks/{network_id}/acl")
async def update_acl(
    network_id: int,
    acl_policy: TailscaleACLPolicy,
    current_user: User = Depends(get_current_user),
    tailscale_service: TailscaleIntegration = Depends(get_tailscale_service),
):
    """Update ACL policy for network."""
    success = await tailscale_service.update_acl(network_id, acl_policy.model_dump())

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to update ACL policy",
        )

    return {"success": True, "message": "ACL policy updated"}


@router.get("/networks/{network_id}/stats", response_model=TailscaleNetworkStats)
async def get_network_stats(
    network_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get network statistics."""
    # Count devices
    devices_result = await db.execute(
        select(TailscaleDevice).where(TailscaleDevice.network_id == network_id)
    )
    devices = list(devices_result.scalars().all())

    online_count = sum(1 for d in devices if d.is_online)
    offline_count = len(devices) - online_count
    exit_node_count = sum(1 for d in devices if d.is_exit_node)
    subnet_router_count = sum(1 for d in devices if d.is_subnet_router)

    # Count routes
    routes_result = await db.execute(
        select(TailscaleRoute).join(TailscaleDevice).where(TailscaleDevice.network_id == network_id)
    )
    routes = list(routes_result.scalars().all())
    enabled_routes = sum(1 for r in routes if r.is_enabled)

    return TailscaleNetworkStats(
        total_devices=len(devices),
        online_devices=online_count,
        offline_devices=offline_count,
        exit_nodes=exit_node_count,
        subnet_routers=subnet_router_count,
        total_routes=len(routes),
        enabled_routes=enabled_routes,
    )
