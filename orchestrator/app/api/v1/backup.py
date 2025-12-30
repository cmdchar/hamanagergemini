"""Backup API endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.integrations.backup import BackupService
from app.models.backup import (
    Backup,
    BackupRestore,
    BackupSchedule,
    NodeREDConfig,
    Zigbee2MQTTConfig,
)
from app.models.user import User
from app.schemas.backup import (
    BackupCleanupRequest,
    BackupCleanupResponse,
    BackupCreate,
    BackupResponse,
    BackupRestoreCreate,
    BackupRestoreResponse,
    BackupScheduleCreate,
    BackupScheduleResponse,
    BackupScheduleUpdate,
    BackupStatistics,
    BackupVerifyResponse,
    NodeREDConfigCreate,
    NodeREDConfigResponse,
    NodeREDConfigUpdate,
    Zigbee2MQTTConfigCreate,
    Zigbee2MQTTConfigResponse,
    Zigbee2MQTTConfigUpdate,
)
from app.utils.logging import log_integration_event

router = APIRouter(prefix="/backups", tags=["backups"])
logger = logging.getLogger(__name__)


# Backup endpoints
@router.post("", response_model=BackupResponse, status_code=status.HTTP_201_CREATED)
async def create_backup(
    data: BackupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new backup."""
    try:
        backup_service = BackupService(db)

        if data.backup_type == "nodered":
            backup = await backup_service.create_nodered_backup(
                config_id=data.config_id,
                name=data.name,
                description=data.description,
            )
        elif data.backup_type == "zigbee2mqtt":
            backup = await backup_service.create_zigbee2mqtt_backup(
                config_id=data.config_id,
                name=data.name,
                description=data.description,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported backup type: {data.backup_type}",
            )

        if not backup:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create backup",
            )

        # Update retention if specified
        if data.retention_days:
            backup.retention_days = data.retention_days
            await db.commit()
            await db.refresh(backup)

        return backup

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create backup",
        )


@router.get("", response_model=List[BackupResponse])
async def list_backups(
    skip: int = 0,
    limit: int = 100,
    backup_type: Optional[str] = None,
    server_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List backups."""
    try:
        query = select(Backup)

        if backup_type:
            query = query.where(Backup.backup_type == backup_type)

        if server_id:
            query = query.where(Backup.server_id == server_id)

        query = query.order_by(Backup.backup_date.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        backups = list(result.scalars().all())

        return backups

    except Exception as e:
        logger.exception(f"Failed to list backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list backups",
        )


@router.get("/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get backup by ID."""
    try:
        result = await db.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()

        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found",
            )

        return backup

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get backup",
        )


@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete backup."""
    try:
        result = await db.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()

        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found",
            )

        # Delete file
        from pathlib import Path

        Path(backup.storage_path).unlink(missing_ok=True)

        # Delete record
        await db.delete(backup)
        await db.commit()

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete backup",
        )


# Restore endpoints
@router.post("/restore", response_model=BackupRestoreResponse)
async def restore_backup(
    data: BackupRestoreCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore a backup."""
    try:
        backup_service = BackupService(db)

        restore = await backup_service.restore_backup(
            backup_id=data.backup_id,
            target_host=data.target_host,
            target_path=data.target_path,
            overwrite=data.overwrite_existing,
            create_backup_before=data.create_backup_before,
        )

        if not restore:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restore backup",
            )

        return restore

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to restore backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore backup",
        )


@router.get("/restores", response_model=List[BackupRestoreResponse])
async def list_restores(
    skip: int = 0,
    limit: int = 50,
    backup_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List restore operations."""
    try:
        query = select(BackupRestore)

        if backup_id:
            query = query.where(BackupRestore.backup_id == backup_id)

        query = query.order_by(BackupRestore.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        restores = list(result.scalars().all())

        return restores

    except Exception as e:
        logger.exception(f"Failed to list restores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list restores",
        )


# Verification and cleanup
@router.post("/{backup_id}/verify", response_model=BackupVerifyResponse)
async def verify_backup(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify backup integrity."""
    try:
        from pathlib import Path

        result = await db.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()

        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found",
            )

        backup_service = BackupService(db)
        valid = await backup_service.verify_backup(backup_id)

        file_exists = Path(backup.storage_path).exists()
        hash_match = valid

        return BackupVerifyResponse(
            backup_id=backup_id,
            valid=valid,
            file_exists=file_exists,
            hash_match=hash_match,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to verify backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify backup",
        )


@router.post("/cleanup", response_model=BackupCleanupResponse)
async def cleanup_backups(
    data: BackupCleanupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clean up old backups."""
    try:
        backup_service = BackupService(db)

        deleted_count = await backup_service.cleanup_old_backups(
            retention_days=data.retention_days,
            max_backups=data.max_backups,
        )

        return BackupCleanupResponse(
            deleted_count=deleted_count,
            freed_space=0,  # Would need to track deleted file sizes
        )

    except Exception as e:
        logger.exception(f"Failed to cleanup backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup backups",
        )


# Schedule endpoints
@router.post("/schedules", response_model=BackupScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    data: BackupScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create backup schedule."""
    try:
        schedule = BackupSchedule(**data.model_dump())
        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)

        log_integration_event(
            "Backup",
            "schedule_created",
            True,
            {"schedule_id": schedule.id, "type": schedule.backup_type},
        )

        return schedule

    except Exception as e:
        logger.exception(f"Failed to create schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schedule",
        )


@router.get("/schedules", response_model=List[BackupScheduleResponse])
async def list_schedules(
    skip: int = 0,
    limit: int = 50,
    enabled_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List backup schedules."""
    try:
        query = select(BackupSchedule)

        if enabled_only:
            query = query.where(BackupSchedule.enabled == True)

        query = query.order_by(BackupSchedule.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        schedules = list(result.scalars().all())

        return schedules

    except Exception as e:
        logger.exception(f"Failed to list schedules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list schedules",
        )


@router.patch("/schedules/{schedule_id}", response_model=BackupScheduleResponse)
async def update_schedule(
    schedule_id: int,
    data: BackupScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update backup schedule."""
    try:
        result = await db.execute(
            select(BackupSchedule).where(BackupSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found",
            )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)

        await db.commit()
        await db.refresh(schedule)

        return schedule

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update schedule",
        )


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete backup schedule."""
    try:
        result = await db.execute(
            select(BackupSchedule).where(BackupSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found",
            )

        await db.delete(schedule)
        await db.commit()

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete schedule",
        )


# Node-RED config endpoints
@router.post("/nodered/configs", response_model=NodeREDConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_nodered_config(
    data: NodeREDConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create Node-RED configuration."""
    try:
        config = NodeREDConfig(**data.model_dump())
        db.add(config)
        await db.commit()
        await db.refresh(config)

        return config

    except Exception as e:
        logger.exception(f"Failed to create Node-RED config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Node-RED config",
        )


@router.get("/nodered/configs", response_model=List[NodeREDConfigResponse])
async def list_nodered_configs(
    skip: int = 0,
    limit: int = 50,
    server_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List Node-RED configurations."""
    try:
        query = select(NodeREDConfig)

        if server_id:
            query = query.where(NodeREDConfig.server_id == server_id)

        query = query.order_by(NodeREDConfig.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        configs = list(result.scalars().all())

        return configs

    except Exception as e:
        logger.exception(f"Failed to list Node-RED configs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list Node-RED configs",
        )


@router.patch("/nodered/configs/{config_id}", response_model=NodeREDConfigResponse)
async def update_nodered_config(
    config_id: int,
    data: NodeREDConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update Node-RED configuration."""
    try:
        result = await db.execute(
            select(NodeREDConfig).where(NodeREDConfig.id == config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node-RED config not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        await db.commit()
        await db.refresh(config)

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update Node-RED config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Node-RED config",
        )


# Zigbee2MQTT config endpoints
@router.post("/zigbee2mqtt/configs", response_model=Zigbee2MQTTConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_zigbee2mqtt_config(
    data: Zigbee2MQTTConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create Zigbee2MQTT configuration."""
    try:
        config = Zigbee2MQTTConfig(**data.model_dump())
        db.add(config)
        await db.commit()
        await db.refresh(config)

        return config

    except Exception as e:
        logger.exception(f"Failed to create Zigbee2MQTT config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Zigbee2MQTT config",
        )


@router.get("/zigbee2mqtt/configs", response_model=List[Zigbee2MQTTConfigResponse])
async def list_zigbee2mqtt_configs(
    skip: int = 0,
    limit: int = 50,
    server_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List Zigbee2MQTT configurations."""
    try:
        query = select(Zigbee2MQTTConfig)

        if server_id:
            query = query.where(Zigbee2MQTTConfig.server_id == server_id)

        query = query.order_by(Zigbee2MQTTConfig.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        configs = list(result.scalars().all())

        return configs

    except Exception as e:
        logger.exception(f"Failed to list Zigbee2MQTT configs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list Zigbee2MQTT configs",
        )


@router.patch("/zigbee2mqtt/configs/{config_id}", response_model=Zigbee2MQTTConfigResponse)
async def update_zigbee2mqtt_config(
    config_id: int,
    data: Zigbee2MQTTConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update Zigbee2MQTT configuration."""
    try:
        result = await db.execute(
            select(Zigbee2MQTTConfig).where(Zigbee2MQTTConfig.id == config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Zigbee2MQTT config not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        await db.commit()
        await db.refresh(config)

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update Zigbee2MQTT config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Zigbee2MQTT config",
        )


# Statistics
@router.get("/statistics", response_model=BackupStatistics)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get backup statistics."""
    try:
        # Backup counts
        total_backups = await db.scalar(select(func.count(Backup.id)))
        total_size = await db.scalar(select(func.sum(Backup.file_size))) or 0

        # Backups by type
        type_result = await db.execute(
            select(Backup.backup_type, func.count(Backup.id))
            .group_by(Backup.backup_type)
        )
        backups_by_type = {row[0]: row[1] for row in type_result}

        # Oldest and newest
        oldest = await db.scalar(
            select(Backup.backup_date).order_by(Backup.backup_date.asc()).limit(1)
        )
        newest = await db.scalar(
            select(Backup.backup_date).order_by(Backup.backup_date.desc()).limit(1)
        )

        # Restore counts
        total_restores = await db.scalar(select(func.count(BackupRestore.id)))
        successful_restores = await db.scalar(
            select(func.count(BackupRestore.id)).where(BackupRestore.success == True)
        )

        # Schedule counts
        scheduled_backups = await db.scalar(select(func.count(BackupSchedule.id)))
        active_schedules = await db.scalar(
            select(func.count(BackupSchedule.id)).where(BackupSchedule.enabled == True)
        )

        return BackupStatistics(
            total_backups=total_backups or 0,
            total_size=int(total_size),
            backups_by_type=backups_by_type,
            oldest_backup=oldest,
            newest_backup=newest,
            total_restores=total_restores or 0,
            successful_restores=successful_restores or 0,
            failed_restores=(total_restores or 0) - (successful_restores or 0),
            scheduled_backups=scheduled_backups or 0,
            active_schedules=active_schedules or 0,
        )

    except Exception as e:
        logger.exception(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics",
        )
