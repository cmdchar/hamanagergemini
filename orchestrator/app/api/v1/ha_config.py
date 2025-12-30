from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.session import get_db
from app.models.server import Server
from app.models.ha_config import HaConfig
from app.schemas.ha_config import HaConfigResponse
from typing import List
import asyncssh
import logging
import uuid

router = APIRouter()
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
        connect_kwargs["client_keys"] = [server.ssh_key_path]
    elif server.ssh_password:
        connect_kwargs["password"] = server.ssh_password
    
    synced_files = []

    try:
        async with asyncssh.connect(**connect_kwargs) as conn:
            # 3. Find YAML files in /config
            # We use 'find' to get relative paths. Assuming /config is the base.
            # We'll limit to depth 2 to avoid huge trees (node_modules etc if any)
            # and filter for yaml/json/conf
            cmd = "find /config -maxdepth 2 -type f \\( -name '*.yaml' -o -name '*.json' -o -name '*.conf' \\)"
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
