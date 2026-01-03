from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.session import get_db
from app.models.server import Server
from app.models.ha_config import HaConfig
from app.schemas.ha_config import HaConfigResponse, HaConfigUpdate
from app.utils.security import decrypt_value
from app.utils.ssh import get_usable_key_path
from typing import List
import asyncssh
import logging
import uuid

router = APIRouter(prefix="/ha-config", tags=["ha-config"])
logger = logging.getLogger(__name__)

async def sync_ha_config_task(server_id: int, db: AsyncSession):
    """Background task to sync HA configuration files."""
    try:
        # Get server details (need a new session or careful session management)
        # Since db session might be closed, we should ideally handle this better.
        # But BackgroundTasks in FastAPI run after the response is sent, so the session dependency is tricky.
        # Usually better to use a new session context manager.
        pass 
    except Exception as e:
        logger.error(f"Error in background sync task: {e}")

# For simplicity, I'll make it a direct async call for now, not a background task, 
# or I'll handle the session properly within the endpoint.

@router.post("/servers/{server_id}/sync-config", response_model=List[HaConfigResponse])
async def sync_ha_config(
    server_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Sync configuration files from the Home Assistant server."""
    # 1. Get Server
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # 2. Prepare SSH connection
    connect_kwargs = {
        "host": server.ssh_host or server.host,
        "port": server.ssh_port or 22,
        "username": server.ssh_user,
        "known_hosts": None
    }
    
    if server.ssh_key_path:
        passphrase = None
        if server.ssh_key_passphrase:
            try:
                passphrase = decrypt_value(server.ssh_key_passphrase)
            except Exception:
                logger.warning(f"Failed to decrypt SSH key passphrase for server {server.id}")
        
        real_key_path, real_passphrase = get_usable_key_path(server.ssh_key_path, passphrase)
        connect_kwargs["client_keys"] = [real_key_path]
        if real_passphrase:
            connect_kwargs["passphrase"] = real_passphrase
    elif server.ssh_password:
        try:
            connect_kwargs["password"] = decrypt_value(server.ssh_password) if server.ssh_password else None
        except Exception:
            logger.warning(f"Failed to decrypt SSH password for server {server.id}")
            connect_kwargs["password"] = None
    
    synced_files = []

    try:
        async with asyncssh.connect(**connect_kwargs) as conn:
            # 3. Find YAML files in /config
            # We use 'find' to get relative paths. Assuming /config is the base.
            # We'll limit to depth 5 to explore subfolders while avoiding node_modules and other deep trees
            # and filter for yaml/json/conf
            # -L flag follows symlinks (needed because /config -> /homeassistant)
            cmd = "find -L /config -maxdepth 5 -type f \\( -name '*.yaml' -o -name '*.json' -o -name '*.conf' \\)"
            result = await conn.run(cmd)
            
            if result.exit_status != 0:
                logger.error(f"Error listing files: {result.stderr}")
                raise HTTPException(status_code=500, detail=f"Error listing files: {result.stderr}")
            
            file_paths = result.stdout.strip().split('\n')
            file_paths = [p for p in file_paths if p.strip()]
            
            # 4. Read each file and update DB
            for file_path in file_paths:
                # Read content
                cat_res = await conn.run(f"cat '{file_path}'")
                if cat_res.exit_status != 0:
                    logger.warning(f"Could not read {file_path}: {cat_res.stderr}")
                    continue
                
                content = cat_res.stdout
                
                # Check if exists
                existing_res = await db.execute(
                    select(HaConfig).where(
                        HaConfig.server_id == server_id,
                        HaConfig.path == file_path
                    )
                )
                existing = existing_res.scalar_one_or_none()
                
                if existing:
                    existing.content = content
                    synced_files.append(existing)
                else:
                    new_config = HaConfig(
                        server_id=server_id,
                        path=file_path,
                        content=content
                    )
                    db.add(new_config)
                    synced_files.append(new_config)
            
            await db.commit()
            
            # Refresh to get IDs etc
            for f in synced_files:
                await db.refresh(f)
                
            return synced_files

    except (OSError, asyncssh.Error) as e:
        logger.error(f"SSH Error: {e}")
        raise HTTPException(status_code=500, detail=f"SSH Connection Error: {str(e)}")
    except Exception as e:
        logger.error(f"Sync Error: {e}")
        raise HTTPException(status_code=500, detail=f"Sync Error: {str(e)}")

@router.get("/servers/{server_id}/configs", response_model=List[HaConfigResponse])
async def get_ha_configs(
    server_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all configuration files for a specific server."""
    # Check if server exists
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    result = await db.execute(select(HaConfig).where(HaConfig.server_id == server_id))
    return result.scalars().all()

@router.get("/servers/{server_id}/configs/{config_id}", response_model=HaConfigResponse)
async def get_ha_config_detail(
    server_id: int,
    config_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific configuration file."""
    result = await db.execute(
        select(HaConfig).where(
            HaConfig.server_id == server_id,
            HaConfig.id == config_id
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config

@router.put("/servers/{server_id}/configs/{config_id}", response_model=HaConfigResponse)
async def update_ha_config(
    server_id: int,
    config_id: uuid.UUID,
    config_update: HaConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a configuration file and sync it to the remote server."""
    # 1. Get the config from DB
    result = await db.execute(
        select(HaConfig).where(
            HaConfig.server_id == server_id,
            HaConfig.id == config_id
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    # 2. Get server details
    server_result = await db.execute(select(Server).where(Server.id == server_id))
    server = server_result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # 3. Update the file on the remote server via SSH
    connect_kwargs = {
        "host": server.ssh_host or server.host,
        "port": server.ssh_port or 22,
        "username": server.ssh_user,
        "known_hosts": None
    }

    if server.ssh_key_path:
        passphrase = None
        if server.ssh_key_passphrase:
            try:
                passphrase = decrypt_value(server.ssh_key_passphrase)
            except Exception:
                logger.warning(f"Failed to decrypt SSH key passphrase for server {server.id}")

        real_key_path, real_passphrase = get_usable_key_path(server.ssh_key_path, passphrase)
        connect_kwargs["client_keys"] = [real_key_path]
        if real_passphrase:
            connect_kwargs["passphrase"] = real_passphrase
    elif server.ssh_password:
        try:
            connect_kwargs["password"] = decrypt_value(server.ssh_password) if server.ssh_password else None
        except Exception:
            logger.warning(f"Failed to decrypt SSH password for server {server.id}")
            connect_kwargs["password"] = None

    try:
        async with asyncssh.connect(**connect_kwargs) as conn:
            # Create a temporary file with the new content
            temp_file = f"/tmp/ha_config_{uuid.uuid4()}.tmp"

            # Write content to temp file (using echo with base64 to handle special chars)
            import base64
            content_b64 = base64.b64encode(config_update.content.encode('utf-8')).decode('ascii')
            write_cmd = f"echo '{content_b64}' | base64 -d > {temp_file}"
            write_result = await conn.run(write_cmd)

            if write_result.exit_status != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to write temp file: {write_result.stderr}"
                )

            # Move temp file to actual location (preserves permissions)
            move_cmd = f"mv {temp_file} '{config.path}'"
            move_result = await conn.run(move_cmd)

            if move_result.exit_status != 0:
                # Cleanup temp file on failure
                await conn.run(f"rm -f {temp_file}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update file: {move_result.stderr}"
                )

            # 4. Update DB with new content
            config.content = config_update.content
            await db.commit()
            await db.refresh(config)

            return config

    except (OSError, asyncssh.Error) as e:
        logger.error(f"SSH Error: {e}")
        raise HTTPException(status_code=500, detail=f"SSH Connection Error: {str(e)}")
    except Exception as e:
        logger.error(f"Update Error: {e}")
        raise HTTPException(status_code=500, detail=f"Update Error: {str(e)}")


@router.get("/servers/{server_id}/files")
async def list_server_files(
    server_id: int,
    path: str = "",
    db: AsyncSession = Depends(get_db)
):
    """
    List files on the Home Assistant server via SSH.

    Args:
        server_id: Server ID
        path: Optional subdirectory path (relative to config path)
        db: Database session

    Returns:
        dict: List of files with metadata
    """
    try:
        from app.utils.ssh import list_remote_files

        # Get server
        result = await db.execute(select(Server).where(Server.id == server_id))
        server = result.scalar_one_or_none()

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )

        # Get files from server
        config_path = server.config_path or "/config"

        # If path parameter is provided, navigate to that subdirectory
        if path:
            # Clean the path to prevent directory traversal attacks
            clean_path = path.strip('/').replace('..', '')
            full_path = f"{config_path}/{clean_path}"
        else:
            full_path = config_path

        files = await list_remote_files(server, full_path)

        # Mark files as recommended or not for GitHub sync
        # Files/folders to recommend skipping (but still show them)
        skip_recommendations = {
            '.cloud', '.storage', 'backups', 'deps', 'tts', '.claude',
            '__pycache__', '.git', 'node_modules', '.HA_VERSION',
            'home-assistant.log', 'home-assistant_v2.db', 'home-assistant.log.1',
            '.homeassistant_log_error', 'OZW_Log.txt'
        }

        # Add recommendation metadata to each file
        annotated_files = []
        for file in files:
            file_name = file.get("name", "")

            # Add recommendation flag
            file["recommended"] = file_name not in skip_recommendations

            # Special case: secrets.yaml should NEVER be synced
            if file_name in ['secrets.yaml', 'secrets.yml']:
                file["recommended"] = False
                file["warning"] = "Contains sensitive data"

            annotated_files.append(file)

        # Sort: directories first, then files alphabetically
        annotated_files.sort(key=lambda x: (not x.get("is_dir", False), x.get("name", "")))

        return {
            "server_id": server_id,
            "server_name": server.name,
            "path": full_path,
            "current_path": path if path else "/",
            "files": annotated_files,
            "total_files": len([f for f in annotated_files if not f.get("is_dir")]),
            "total_dirs": len([f for f in annotated_files if f.get("is_dir")]),
            "recommended_files": len([f for f in annotated_files if f.get("recommended", True)]),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list server files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
