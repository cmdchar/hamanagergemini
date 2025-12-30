"""Deployment management API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deployment import DeploymentEngine
from app.core.rollback import RollbackService
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.deployment import Deployment, DeploymentStatus
from app.models.server import Server
from app.models.user import User
from app.schemas.deployment import (
    DeploymentCreate,
    DeploymentResponse,
    DeploymentResultResponse,
)
from app.utils.logging import logger

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.get("", response_model=List[DeploymentResponse])
async def list_deployments(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[DeploymentStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all deployments.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status_filter: Optional status filter
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[DeploymentResponse]: List of deployments
    """
    query = select(Deployment).order_by(Deployment.created_at.desc())

    if status_filter:
        query = query.where(Deployment.status == status_filter)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    deployments = list(result.scalars().all())

    return [
        DeploymentResponse(
            id=deployment.id,
            name=deployment.name,
            description=deployment.description,
            status=deployment.status,
            trigger=deployment.trigger,
            deploy_all=deployment.deploy_all,
            target_servers=deployment.target_servers,
            total_servers=deployment.total_servers,
            successful_servers=deployment.successful_servers,
            failed_servers=deployment.failed_servers,
            skip_validation=deployment.skip_validation,
            skip_backup=deployment.skip_backup,
            auto_restart=deployment.auto_restart,
            auto_rollback=deployment.auto_rollback,
            can_rollback=deployment.can_rollback,
            rolled_back_from_id=deployment.rolled_back_from_id,
            started_at=deployment.started_at,
            completed_at=deployment.completed_at,
            duration_seconds=deployment.duration_seconds,
            error_message=deployment.error_message,
            user_id=deployment.user_id,
            created_at=deployment.created_at,
            updated_at=deployment.updated_at,
        )
        for deployment in deployments
    ]


@router.post("", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    deployment_data: DeploymentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create and start a new deployment.

    Args:
        deployment_data: Deployment creation data
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session

    Returns:
        DeploymentResponse: Created deployment
    """
    # Validate target servers if not deploying to all
    if not deployment_data.deploy_all and not deployment_data.target_servers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either deploy_all or target_servers",
        )

    # Create deployment
    deployment = Deployment(
        name=deployment_data.name,
        description=deployment_data.description,
        deploy_all=deployment_data.deploy_all,
        target_servers=deployment_data.target_servers,
        skip_validation=deployment_data.skip_validation,
        skip_backup=deployment_data.skip_backup,
        auto_restart=deployment_data.auto_restart,
        auto_rollback=deployment_data.auto_rollback,
        status=DeploymentStatus.PENDING,
        user_id=current_user.id,
    )

    db.add(deployment)
    await db.commit()
    await db.refresh(deployment)

    # Start deployment in background
    background_tasks.add_task(execute_deployment, deployment.id, db)

    logger.info(f"Created deployment {deployment.id}: {deployment.name}")

    return DeploymentResponse(
        id=deployment.id,
        name=deployment.name,
        description=deployment.description,
        status=deployment.status,
        trigger=deployment.trigger,
        deploy_all=deployment.deploy_all,
        target_servers=deployment.target_servers,
        total_servers=deployment.total_servers,
        successful_servers=deployment.successful_servers,
        failed_servers=deployment.failed_servers,
        skip_validation=deployment.skip_validation,
        skip_backup=deployment.skip_backup,
        auto_restart=deployment.auto_restart,
        auto_rollback=deployment.auto_rollback,
        can_rollback=deployment.can_rollback,
        rolled_back_from_id=deployment.rolled_back_from_id,
        started_at=deployment.started_at,
        completed_at=deployment.completed_at,
        duration_seconds=deployment.duration_seconds,
        error_message=deployment.error_message,
        user_id=deployment.user_id,
        created_at=deployment.created_at,
        updated_at=deployment.updated_at,
    )


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get deployment by ID.

    Args:
        deployment_id: Deployment ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        DeploymentResponse: Deployment details

    Raises:
        HTTPException: If deployment not found
    """
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found",
        )

    return DeploymentResponse(
        id=deployment.id,
        name=deployment.name,
        description=deployment.description,
        status=deployment.status,
        trigger=deployment.trigger,
        deploy_all=deployment.deploy_all,
        target_servers=deployment.target_servers,
        total_servers=deployment.total_servers,
        successful_servers=deployment.successful_servers,
        failed_servers=deployment.failed_servers,
        skip_validation=deployment.skip_validation,
        skip_backup=deployment.skip_backup,
        auto_restart=deployment.auto_restart,
        auto_rollback=deployment.auto_rollback,
        can_rollback=deployment.can_rollback,
        rolled_back_from_id=deployment.rolled_back_from_id,
        started_at=deployment.started_at,
        completed_at=deployment.completed_at,
        duration_seconds=deployment.duration_seconds,
        error_message=deployment.error_message,
        user_id=deployment.user_id,
        created_at=deployment.created_at,
        updated_at=deployment.updated_at,
    )


@router.post("/{deployment_id}/cancel")
async def cancel_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a running deployment.

    Args:
        deployment_id: Deployment ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Cancellation result
    """
    engine = DeploymentEngine(db)

    try:
        deployment = await engine.cancel_deployment(deployment_id)
        logger.info(f"Deployment {deployment_id} cancelled by user {current_user.id}")

        return {
            "success": True,
            "message": f"Deployment {deployment_id} cancelled",
            "deployment_id": deployment.id,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{deployment_id}/rollback")
async def rollback_deployment(
    deployment_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rollback a deployment.

    Args:
        deployment_id: Deployment ID
        reason: Optional rollback reason
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Rollback result
    """
    rollback_service = RollbackService(db)

    try:
        success = await rollback_service.rollback_deployment(
            deployment_id, reason or "Manual rollback"
        )
        logger.info(f"Deployment {deployment_id} rolled back by user {current_user.id}")

        return {
            "success": success,
            "message": f"Deployment {deployment_id} rolled back",
            "deployment_id": deployment_id,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback failed: {str(e)}",
        )


async def execute_deployment(deployment_id: int, db: AsyncSession):
    """
    Execute deployment in background.

    Args:
        deployment_id: Deployment ID
        db: Database session
    """
    try:
        engine = DeploymentEngine(db)

        # Get deployment
        result = await db.execute(
            select(Deployment).where(Deployment.id == deployment_id)
        )
        deployment = result.scalar_one_or_none()

        if not deployment:
            logger.error(f"Deployment {deployment_id} not found")
            return

        # Execute deployment
        await engine.deploy(deployment)

        logger.info(f"Deployment {deployment_id} completed successfully")

    except Exception as e:
        logger.exception(f"Deployment {deployment_id} failed: {str(e)}")

        # Update deployment status
        result = await db.execute(
            select(Deployment).where(Deployment.id == deployment_id)
        )
        deployment = result.scalar_one_or_none()

        if deployment:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            await db.commit()
