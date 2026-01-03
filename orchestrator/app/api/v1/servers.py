"""Server management API endpoints."""

from typing import List, Optional
import os
import shutil

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.server import Server
from app.models.user import User
from app.schemas.server import ServerCreate, ServerResponse, ServerUpdate
from app.utils.security import encrypt_value
from app.utils.ssh import get_usable_key_path, execute_ssh_command, list_remote_files, read_remote_file, write_remote_file
from pydantic import BaseModel

router = APIRouter(prefix="/servers", tags=["servers"])

class CommandRequest(BaseModel):
    command: str

class FileContentRequest(BaseModel):
    path: str
    content: str


def create_server_response(server: Server) -> ServerResponse:
    """Helper function to create ServerResponse from Server model."""
    ha_url = f"http{'s' if server.use_ssl else ''}://{server.host}:{server.port}"
    is_online = server.status == "online"

    return ServerResponse(
        id=server.id,
        name=server.name,
        host=server.host,
        ssh_host=server.ssh_host,
        ssh_port=server.ssh_port,
        ssh_user=server.ssh_user,
        ha_username=server.ha_username,
        github_repo=server.github_repo,
        github_branch=server.github_branch,
        port=server.port,
        config_path=server.config_path,
        backup_path=server.backup_path,
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
        url=ha_url,
        ha_url=ha_url,
        ha_version=server.version,
        is_online=is_online,
        last_check=server.updated_at.isoformat() if server.updated_at else None
    )


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
    return [create_server_response(server) for server in servers]


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

    ssh_key_passphrase_encrypted = None
    if server_data.ssh_key_passphrase:
        ssh_key_passphrase_encrypted = encrypt_value(server_data.ssh_key_passphrase)

    access_token_encrypted = None
    if server_data.access_token:
        access_token_encrypted = encrypt_value(server_data.access_token)

    ha_password_encrypted = None
    if server_data.ha_password:
        ha_password_encrypted = encrypt_value(server_data.ha_password)

    # Create server
    server = Server(
        name=server_data.name,
        host=server_data.host,
        ssh_host=server_data.ssh_host,
        ssh_port=server_data.ssh_port or 22,
        ssh_user=server_data.ssh_user,
        ssh_password=ssh_password_encrypted,
        ssh_key_path=server_data.ssh_key_path,
        ssh_key_passphrase=ssh_key_passphrase_encrypted,
        port=server_data.port or 8123,
        access_token=access_token_encrypted,
        api_key=server_data.api_key,
        ha_username=server_data.ha_username,
        ha_password=ha_password_encrypted,
        github_repo=server_data.github_repo,
        github_branch=server_data.github_branch,
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

    # Auto-sync configuration files from server (recursive)
    try:
        from app.models.ha_config import HaConfig

        synced_count = 0
        visited_paths = set()
        max_depth = 10

        # Files/directories to skip
        skip_patterns = {'.git', '.github', '__pycache__', '.vscode', '.idea', 'node_modules',
                        '.cache', '.claude', 'tts', '.storage', 'deps', 'tts'}

        async def sync_recursive(remote_path: str, depth: int = 0):
            """Recursively sync files from a directory."""
            nonlocal synced_count

            # Prevent infinite recursion
            if depth > max_depth:
                return

            # Normalize path and check if already visited
            normalized_path = remote_path.rstrip('/')
            if normalized_path in visited_paths:
                return
            visited_paths.add(normalized_path)

            try:
                files = await list_remote_files(server, remote_path)
            except Exception as e:
                return

            for file_info in files:
                file_name = file_info.get("name", "")
                file_path = file_info.get("path", "")

                # Skip . and .. entries
                if file_name in ('.', '..'):
                    continue

                # Skip unwanted files/dirs
                if file_name in skip_patterns or file_name.startswith('.'):
                    continue

                if file_info.get("is_dir"):
                    # Recursively sync subdirectory
                    await sync_recursive(file_path, depth + 1)
                else:
                    # Sync file
                    try:
                        content = await read_remote_file(server, file_path)

                        # Save to database
                        ha_config = HaConfig(
                            server_id=server.id,
                            path=file_path,
                            content=content,
                        )
                        db.add(ha_config)
                        synced_count += 1

                        # Commit in batches to avoid memory issues
                        if synced_count % 50 == 0:
                            await db.commit()
                    except Exception as e:
                        pass  # Skip files that can't be read

        # Start recursive sync from config_path
        await sync_recursive(server.config_path or '/config')

        # Final commit for remaining files
        await db.commit()
        print(f"✅ Auto-synced {synced_count} files from server {server.name}")
    except Exception as e:
        print(f"⚠️ Could not auto-sync files: {e}")

    return create_server_response(server)


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
    Test SSH and Home Assistant connection to a server.

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

    import asyncssh
    import aiohttp
    import time
    from app.utils.security import decrypt_value

    results = {
        "ssh": {"status": "not_tested", "message": ""},
        "ha": {"status": "not_tested", "message": ""},
        "overall_status": "failed"
    }

    # Test SSH connection
    if server.ssh_user:
        try:
            start_time = time.time()

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
                        results["ssh"] = {"status": "failed", "message": "Failed to decrypt SSH key passphrase. Please update server settings."}
                        return results
                
                real_key_path, real_passphrase = get_usable_key_path(server.ssh_key_path, passphrase)
                connect_kwargs["client_keys"] = [real_key_path]
                if real_passphrase:
                    connect_kwargs["passphrase"] = real_passphrase
            elif server.ssh_password:
                # Decrypt password if encrypted
                try:
                    password = decrypt_value(server.ssh_password) if server.ssh_password else None
                    connect_kwargs["password"] = password
                except Exception:
                    results["ssh"] = {"status": "failed", "message": "Failed to decrypt SSH password. Please update server settings."}
                    return results

            async with asyncssh.connect(**connect_kwargs) as conn:
                result = await conn.run("echo 'SSH OK'", check=True)
                latency = int((time.time() - start_time) * 1000)

                results["ssh"] = {
                    "status": "success",
                    "message": f"SSH connection successful (latency: {latency}ms)",
                    "latency_ms": latency
                }
        except Exception as e:
            results["ssh"] = {
                "status": "failed",
                "message": f"SSH connection failed: {str(e)}"
            }

    # Test Home Assistant API connection
    if server.access_token:
        try:
            start_time = time.time()
            # Use /api/config to get version information and verify full access
            url = f"http{'s' if server.use_ssl else ''}://{server.host}:{server.port}/api/config"

            # Decrypt access token if encrypted
            access_token = decrypt_value(server.access_token) if server.access_token else None

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    latency = int((time.time() - start_time) * 1000)

                    if response.status == 200:
                        data = await response.json()
                        results["ha"] = {
                            "status": "success",
                            "message": f"Home Assistant API connected (latency: {latency}ms)",
                            "latency_ms": latency,
                            "version": data.get("version", "unknown")
                        }

                        # Update server status and version
                        server.status = "online"
                        if "version" in data:
                            server.version = data["version"]
                        server.updated_at = func.now()
                        server.version = data.get("version")
                        await db.commit()
                    else:
                        results["ha"] = {
                            "status": "failed",
                            "message": f"Home Assistant API error: HTTP {response.status}"
                        }
        except Exception as e:
            results["ha"] = {
                "status": "failed",
                "message": f"Home Assistant connection failed: {str(e)}"
            }

    # Determine overall status
    ssh_ok = results["ssh"]["status"] == "success" or results["ssh"]["status"] == "not_tested"
    ha_ok = results["ha"]["status"] == "success" or results["ha"]["status"] == "not_tested"

    if ssh_ok and ha_ok and (results["ssh"]["status"] == "success" or results["ha"]["status"] == "success"):
        results["overall_status"] = "success"
        results["message"] = f"Successfully connected to {server.name}"
    else:
        results["overall_status"] = "failed"
        results["message"] = "Connection test failed"

    return results


@router.post("/{server_id}/upload-key", response_model=ServerResponse)
async def upload_ssh_key(
    server_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload SSH private key for a server.
    
    Args:
        server_id: Server ID
        file: SSH key file
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ServerResponse: Updated server
    """
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found",
        )
        
    # Create keys directory if it doesn't exist
    keys_dir = "/app/keys"
    os.makedirs(keys_dir, exist_ok=True)
    
    # Generate safe filename
    filename = f"{server_id}_{file.filename}"
    file_path = os.path.join(keys_dir, filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Set restrictive permissions (600) for SSH key
        os.chmod(file_path, 0o600)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save SSH key: {str(e)}",
        )
        
    # Update server ssh_key_path
    server.ssh_key_path = file_path
    await db.commit()
    await db.refresh(server)
    
    return create_server_response(server)


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

    return create_server_response(server)


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
    if server_data.ssh_key_passphrase is not None:
        server.ssh_key_passphrase = encrypt_value(server_data.ssh_key_passphrase)
    if server_data.ssh_key_path is not None:
        server.ssh_key_path = server_data.ssh_key_path
    if server_data.port is not None:
        server.port = server_data.port
    if server_data.access_token is not None:
        server.access_token = encrypt_value(server_data.access_token)
    if server_data.api_key is not None:
        server.api_key = server_data.api_key
    if server_data.ha_username is not None:
        server.ha_username = server_data.ha_username
    if server_data.ha_password is not None:
        server.ha_password = encrypt_value(server_data.ha_password)
    if server_data.github_repo is not None:
        server.github_repo = server_data.github_repo
    if server_data.github_branch is not None:
        server.github_branch = server_data.github_branch
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

    return create_server_response(server)


@router.get("/{server_id}/system-info")
async def get_system_info(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get system information from server via SSH."""
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server {server_id} not found")

    try:
        hostname_result = await execute_ssh_command(server, "hostname")
        hostname = hostname_result.get("stdout", "").strip() if hostname_result.get("success") else "Unknown"

        uptime_result = await execute_ssh_command(server, "uptime -p")
        uptime = uptime_result.get("stdout", "").strip() if uptime_result.get("success") else "Unknown"

        load_result = await execute_ssh_command(server, "cat /proc/loadavg | awk '{print $1, $2, $3}'")
        load_average = load_result.get("stdout", "").strip() if load_result.get("success") else "Unknown"

        mem_result = await execute_ssh_command(server, "free -h | grep Mem | awk '{print $3 \"/\" $2}'")
        memory_usage = mem_result.get("stdout", "").strip() if mem_result.get("success") else "Unknown"

        disk_result = await execute_ssh_command(server, "df -h / | tail -1 | awk '{print $3 \"/\" $2 \" (\" $5 \")\"}'")
        disk_usage = disk_result.get("stdout", "").strip() if disk_result.get("success") else "Unknown"

        cpu_result = await execute_ssh_command(server, "nproc")
        cpu_count = int(cpu_result.get("stdout", "0").strip()) if cpu_result.get("success") else 0

        return {
            "hostname": hostname,
            "uptime": uptime,
            "load_average": load_average,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "cpu_count": cpu_count,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get system info: {str(e)}")


@router.post("/{server_id}/ha/restart")
async def restart_home_assistant(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restart Home Assistant service on the server."""
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server {server_id} not found")

    try:
        commands = [
            "ha core restart",
            "systemctl restart home-assistant@homeassistant",
            "docker restart homeassistant",
        ]

        success = False
        last_error = None

        for cmd in commands:
            result_cmd = await execute_ssh_command(server, cmd)
            if result_cmd.get("success"):
                success = True
                break
            last_error = result_cmd.get("stderr", "Unknown error")

        if success:
            return {"status": "success", "message": "Home Assistant restart initiated"}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to restart: {last_error}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to restart: {str(e)}")


@router.post("/{server_id}/ha/check-config")
async def check_home_assistant_config(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check Home Assistant configuration validity."""
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server {server_id} not found")

    try:
        commands = [
            "ha core check",
            "hass --script check_config",
            "docker exec homeassistant python -m homeassistant --script check_config",
        ]

        valid = False
        errors = None
        output = None

        for cmd in commands:
            result_cmd = await execute_ssh_command(server, cmd)
            if result_cmd.get("success"):
                output = result_cmd.get("stdout", "")
                if "successful" in output.lower() or "valid" in output.lower():
                    valid = True
                elif "error" in output.lower() or "invalid" in output.lower():
                    valid = False
                    errors = output
                else:
                    valid = True
                break

        return {"valid": valid, "errors": errors, "output": output}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to check config: {str(e)}")
