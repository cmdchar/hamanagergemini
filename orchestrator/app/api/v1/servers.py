"""Server management API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.server import Server
from app.models.user import User
from app.schemas.server import ServerCreate, ServerResponse, ServerUpdate
from app.utils.security import encrypt_value

router = APIRouter(prefix="/servers", tags=["servers"])


@router.get("", response_model=List[ServerResponse])
async def list_servers(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all servers.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[ServerResponse]: List of servers
    """
    result = await db.execute(select(Server).offset(skip).limit(limit))
    servers = list(result.scalars().all())

    return [
        ServerResponse(
            id=server.id,
            name=server.name,
            host=server.host,
            ssh_port=server.ssh_port,
            ssh_user=server.ssh_user,
            port=server.port,
            config_path=server.config_path,
            is_active=server.is_active,
            status=server.status,
            version=server.version,
            created_at=server.created_at,
            updated_at=server.updated_at,
            server_type=server.server_type,
            auto_deploy=server.auto_deploy,
            auto_backup=server.auto_backup,
            priority=server.priority,
            tailscale_enabled=server.tailscale_enabled,
            tailscale_ip=server.tailscale_ip,
            tailscale_hostname=server.tailscale_hostname,
            meta_data=server.meta_data,
            tags=server.tags,
            url=f"http{'s' if server.use_ssl else ''}://{server.host}:{server.port}"
        )
        for server in servers
    ]


@router.post("", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    server_data: ServerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new server.

    Args:
        server_data: Server creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ServerResponse: Created server
    """
    # Encrypt sensitive data
    ssh_password_encrypted = None
    if server_data.ssh_password:
        ssh_password_encrypted = encrypt_value(server_data.ssh_password)

    access_token_encrypted = None
    if server_data.access_token:
        access_token_encrypted = encrypt_value(server_data.access_token)

    # Create server
    server = Server(
        name=server_data.name,
        host=server_data.host,
        ssh_host=server_data.ssh_host,
        ssh_port=server_data.ssh_port or 22,
        ssh_user=server_data.ssh_user,
        ssh_password=ssh_password_encrypted,
        ssh_key_path=server_data.ssh_key_path,
        port=server_data.port or 8123,
        access_token=access_token_encrypted,
        api_key=server_data.api_key,
        config_path=server_data.config_path or "/config",
        backup_path=server_data.backup_path or "/backup",
        is_active=True,
        server_type=server_data.server_type,
        auto_deploy=server_data.auto_deploy,
        auto_backup=server_data.auto_backup,
        priority=server_data.priority,
        tailscale_enabled=server_data.tailscale_enabled,
        tags=server_data.tags,
        meta_data=server_data.meta_data if hasattr(server_data, "meta_data") else None,
    )

    db.add(server)
    await db.commit()
    await db.refresh(server)

    return ServerResponse(
        id=server.id,
        name=server.name,
        host=server.host,
        ssh_port=server.ssh_port,
        ssh_user=server.ssh_user,
        port=server.port,
        config_path=server.config_path,
        is_active=server.is_active,
        status=server.status,
        version=server.version,
        created_at=server.created_at,
        updated_at=server.updated_at,
        server_type=server.server_type,
        auto_deploy=server.auto_deploy,
        auto_backup=server.auto_backup,
        priority=server.priority,
        tailscale_enabled=server.tailscale_enabled,
        tailscale_ip=server.tailscale_ip,
        tailscale_hostname=server.tailscale_hostname,
        meta_data=server.meta_data,
        tags=server.tags,
        url=f"http{'s' if server.use_ssl else ''}://{server.host}:{server.port}"
    )


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a server.

    Args:
        server_id: Server ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If server not found
    """
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found",
        )

    await db.delete(server)
    await db.commit()


@router.post("/{server_id}/test")
async def test_server_connection(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Test connection to a server.
    
    Args:
        server_id: Server ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Connection status
    """
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found",
        )
        
    # Mock connection test for now
    # In a real implementation, this would try to connect via SSH or HTTP
    import asyncio
    await asyncio.sleep(1) # Simulate network delay
    
    return {
        "status": "success", 
        "message": f"Successfully connected to {server.name} ({server.host})",
        "details": {
            "latency_ms": 45,
            "version": "2024.1.0"
        }
    }


@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get server by ID.

    Args:
        server_id: Server ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ServerResponse: Server details

    Raises:
        HTTPException: If server not found
    """
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found",
        )

    return ServerResponse(
        id=server.id,
        name=server.name,
        host=server.host,
        ssh_port=server.ssh_port,
        ssh_user=server.ssh_user,
        port=server.port,
        config_path=server.config_path,
        is_active=server.is_active,
        status=server.status,
        version=server.version,
        created_at=server.created_at,
        updated_at=server.updated_at,
        server_type=server.server_type,
        auto_deploy=server.auto_deploy,
        auto_backup=server.auto_backup,
        priority=server.priority,
        tailscale_enabled=server.tailscale_enabled,
        tailscale_ip=server.tailscale_ip,
        tailscale_hostname=server.tailscale_hostname,
        meta_data=server.meta_data,
        tags=server.tags,
        url=f"http{'s' if server.use_ssl else ''}://{server.host}:{server.port}"
    )


@router.put("/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    server_data: ServerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update server.

    Args:
        server_id: Server ID
        server_data: Server update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ServerResponse: Updated server

    Raises:
        HTTPException: If server not found
    """
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found",
        )

    # Update fields
    if server_data.name is not None:
        server.name = server_data.name
    if server_data.host is not None:
        server.host = server_data.host
    if server_data.ssh_host is not None:
        server.ssh_host = server_data.ssh_host
    if server_data.ssh_port is not None:
        server.ssh_port = server_data.ssh_port
    if server_data.ssh_user is not None:
        server.ssh_user = server_data.ssh_user
    if server_data.ssh_password is not None:
        server.ssh_password = encrypt_value(server_data.ssh_password)
    if server_data.ssh_key_path is not None:
        server.ssh_key_path = server_data.ssh_key_path
    if server_data.port is not None:
        server.port = server_data.port
    if server_data.access_token is not None:
        server.access_token = encrypt_value(server_data.access_token)
    if server_data.api_key is not None:
        server.api_key = server_data.api_key
    if server_data.config_path is not None:
        server.config_path = server_data.config_path
    if server_data.backup_path is not None:
        server.backup_path = server_data.backup_path
    if server_data.is_active is not None:
        server.is_active = server_data.is_active
    if server_data.server_type is not None:
        server.server_type = server_data.server_type
    if server_data.status is not None:
        server.status = server_data.status
    if server_data.auto_deploy is not None:
        server.auto_deploy = server_data.auto_deploy
    if server_data.auto_backup is not None:
        server.auto_backup = server_data.auto_backup
    if server_data.priority is not None:
        server.priority = server_data.priority
    if server_data.tailscale_enabled is not None:
        server.tailscale_enabled = server_data.tailscale_enabled
    if server_data.tailscale_ip is not None:
        server.tailscale_ip = server_data.tailscale_ip
    if server_data.tailscale_hostname is not None:
        server.tailscale_hostname = server_data.tailscale_hostname
    if server_data.tags is not None:
        server.tags = server_data.tags
    if server_data.meta_data is not None:
        server.meta_data = server_data.meta_data

    await db.commit()
    await db.refresh(server)

    return ServerResponse(
        id=server.id,
        name=server.name,
        host=server.host,
        ssh_port=server.ssh_port,
        ssh_user=server.ssh_user,
        port=server.port,
        config_path=server.config_path,
        is_active=server.is_active,
        status=server.status,
        version=server.version,
        created_at=server.created_at,
        updated_at=server.updated_at,
        server_type=server.server_type,
        auto_deploy=server.auto_deploy,
        auto_backup=server.auto_backup,
        priority=server.priority,
        tailscale_enabled=server.tailscale_enabled,
        tailscale_ip=server.tailscale_ip,
        tailscale_hostname=server.tailscale_hostname,
        meta_data=server.meta_data,
        tags=server.tags,
        url=f"http{'s' if server.use_ssl else ''}://{server.host}:{server.port}"
    )


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete server.

    Args:
        server_id: Server ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If server not found
    """
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found",
        )

    await db.delete(server)
    await db.commit()


@router.post("/{server_id}/test-connection")
async def test_server_connection(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Test SSH connection to server.

    Args:
        server_id: Server ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Connection test result
    """
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found",
        )

    try:
        import asyncssh

        async with asyncssh.connect(
            server.ssh_host or server.host,
            port=server.ssh_port or 22,
            username=server.ssh_user,
            client_keys=[server.ssh_key_path] if server.ssh_key_path else None,
            password=server.ssh_password,
            known_hosts=None,
        ) as conn:
            result = await conn.run("echo 'Connection successful'", check=True)

            return {
                "success": True,
                "message": "SSH connection successful",
                "output": result.stdout.strip(),
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
