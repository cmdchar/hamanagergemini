"""WLED schedule management API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.wled_schedule import WLEDSchedule
from app.schemas.wled import (
    WLEDScheduleCreate,
    WLEDScheduleResponse,
    WLEDScheduleUpdate,
)
from app.services.wled_scheduler import get_scheduler

router = APIRouter(prefix="/wled/schedules", tags=["wled-schedules"])


@router.get("", response_model=List[WLEDScheduleResponse])
async def list_schedules(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all WLED schedules.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        enabled_only: Filter for enabled schedules only
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[WLEDScheduleResponse]: List of schedules
    """
    query = select(WLEDSchedule)

    if enabled_only:
        query = query.where(WLEDSchedule.enabled == True)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    schedules = list(result.scalars().all())

    return [
        WLEDScheduleResponse(
            id=schedule.id,
            name=schedule.name,
            description=schedule.description,
            device_ids=schedule.device_ids,
            sync_group=schedule.sync_group,
            cron_expression=schedule.cron_expression,
            preset_id=schedule.preset_id,
            state=schedule.state,
            enabled=schedule.enabled,
            start_date=schedule.start_date,
            end_date=schedule.end_date,
            last_run=schedule.last_run,
            next_run=schedule.next_run,
            run_count=schedule.run_count,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )
        for schedule in schedules
    ]


@router.post("", response_model=WLEDScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: WLEDScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new WLED schedule.

    Args:
        schedule_data: Schedule creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        WLEDScheduleResponse: Created schedule
    """
    # Validate that either device_ids or sync_group is provided
    if not schedule_data.device_ids and not schedule_data.sync_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either device_ids or sync_group",
        )

    # Validate that either preset_id or state is provided
    if not schedule_data.preset_id and not schedule_data.state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either preset_id or state",
        )

    # Validate cron expression
    try:
        from apscheduler.triggers.cron import CronTrigger

        CronTrigger.from_crontab(schedule_data.cron_expression)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cron expression: {str(e)}",
        )

    schedule = WLEDSchedule(
        name=schedule_data.name,
        description=schedule_data.description,
        device_ids=schedule_data.device_ids,
        sync_group=schedule_data.sync_group,
        cron_expression=schedule_data.cron_expression,
        preset_id=schedule_data.preset_id,
        state=schedule_data.state.model_dump(exclude_unset=True)
        if schedule_data.state
        else None,
        enabled=schedule_data.enabled,
        start_date=schedule_data.start_date,
        end_date=schedule_data.end_date,
    )

    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    # Add to scheduler if enabled
    if schedule.enabled:
        scheduler = get_scheduler()
        await scheduler.add_schedule(schedule)

    return WLEDScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        description=schedule.description,
        device_ids=schedule.device_ids,
        sync_group=schedule.sync_group,
        cron_expression=schedule.cron_expression,
        preset_id=schedule.preset_id,
        state=schedule.state,
        enabled=schedule.enabled,
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        last_run=schedule.last_run,
        next_run=schedule.next_run,
        run_count=schedule.run_count,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.get("/{schedule_id}", response_model=WLEDScheduleResponse)
async def get_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get WLED schedule by ID.

    Args:
        schedule_id: Schedule ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        WLEDScheduleResponse: Schedule details

    Raises:
        HTTPException: If schedule not found
    """
    result = await db.execute(
        select(WLEDSchedule).where(WLEDSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WLED schedule {schedule_id} not found",
        )

    return WLEDScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        description=schedule.description,
        device_ids=schedule.device_ids,
        sync_group=schedule.sync_group,
        cron_expression=schedule.cron_expression,
        preset_id=schedule.preset_id,
        state=schedule.state,
        enabled=schedule.enabled,
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        last_run=schedule.last_run,
        next_run=schedule.next_run,
        run_count=schedule.run_count,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.put("/{schedule_id}", response_model=WLEDScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: WLEDScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update WLED schedule.

    Args:
        schedule_id: Schedule ID
        schedule_data: Schedule update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        WLEDScheduleResponse: Updated schedule

    Raises:
        HTTPException: If schedule not found
    """
    result = await db.execute(
        select(WLEDSchedule).where(WLEDSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WLED schedule {schedule_id} not found",
        )

    # Validate cron expression if provided
    if schedule_data.cron_expression:
        try:
            from apscheduler.triggers.cron import CronTrigger

            CronTrigger.from_crontab(schedule_data.cron_expression)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cron expression: {str(e)}",
            )

    # Update fields
    update_data = schedule_data.model_dump(exclude_unset=True)

    # Handle state conversion
    if "state" in update_data and update_data["state"] is not None:
        update_data["state"] = update_data["state"].model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(schedule, field, value)

    await db.commit()
    await db.refresh(schedule)

    # Update in scheduler
    scheduler = get_scheduler()
    await scheduler.update_schedule(schedule)

    return WLEDScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        description=schedule.description,
        device_ids=schedule.device_ids,
        sync_group=schedule.sync_group,
        cron_expression=schedule.cron_expression,
        preset_id=schedule.preset_id,
        state=schedule.state,
        enabled=schedule.enabled,
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        last_run=schedule.last_run,
        next_run=schedule.next_run,
        run_count=schedule.run_count,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete WLED schedule.

    Args:
        schedule_id: Schedule ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If schedule not found
    """
    result = await db.execute(
        select(WLEDSchedule).where(WLEDSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WLED schedule {schedule_id} not found",
        )

    # Remove from scheduler
    scheduler = get_scheduler()
    await scheduler.remove_schedule(schedule_id)

    await db.delete(schedule)
    await db.commit()


@router.post("/{schedule_id}/enable")
async def enable_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Enable a WLED schedule.

    Args:
        schedule_id: Schedule ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If schedule not found
    """
    result = await db.execute(
        select(WLEDSchedule).where(WLEDSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WLED schedule {schedule_id} not found",
        )

    schedule.enabled = True
    await db.commit()
    await db.refresh(schedule)

    # Add to scheduler
    scheduler = get_scheduler()
    await scheduler.add_schedule(schedule)

    return {"success": True, "message": "Schedule enabled"}


@router.post("/{schedule_id}/disable")
async def disable_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Disable a WLED schedule.

    Args:
        schedule_id: Schedule ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If schedule not found
    """
    result = await db.execute(
        select(WLEDSchedule).where(WLEDSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WLED schedule {schedule_id} not found",
        )

    schedule.enabled = False
    await db.commit()

    # Remove from scheduler
    scheduler = get_scheduler()
    await scheduler.remove_schedule(schedule_id)

    return {"success": True, "message": "Schedule disabled"}


@router.post("/{schedule_id}/run-now")
async def run_schedule_now(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger a schedule to run immediately.

    Args:
        schedule_id: Schedule ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If schedule not found
    """
    result = await db.execute(
        select(WLEDSchedule).where(WLEDSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WLED schedule {schedule_id} not found",
        )

    # Get scheduler and execute
    scheduler = get_scheduler()
    await scheduler._execute_schedule(schedule_id)

    return {"success": True, "message": "Schedule executed"}
