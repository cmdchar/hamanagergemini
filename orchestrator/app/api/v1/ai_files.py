"""AI file modification API endpoints."""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.ai_file_modification import AIFileModification, ModificationAction, ModificationStatus
from app.models.ha_config import HaConfig
from app.models.server import Server
from app.models.user import User
from app.schemas.ai_file_modification import (
    AIFileModificationCreate,
    AIFileModificationDiff,
    AIFileModificationListResponse,
    AIFileModificationPush,
    AIFileModificationResponse,
    AIFileModificationReview,
    AIFileModificationUpdate,
)
from app.utils.ssh import write_remote_file, read_remote_file
from app.utils.logging import log_integration_event

router = APIRouter(prefix="/ai/files", tags=["ai-files"])
logger = logging.getLogger(__name__)


@router.post("/modify", response_model=AIFileModificationResponse, status_code=status.HTTP_201_CREATED)
async def create_file_modification(
    data: AIFileModificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new AI file modification (pending review).

    This endpoint allows AI to propose changes to configuration files.
    Changes are stored as pending until user reviews and approves them.
    """
    try:
        # Verify server exists and user has access
        stmt = select(Server).where(Server.id == data.server_id)
        result = await db.execute(stmt)
        server = result.scalar_one_or_none()

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )

        # If action is UPDATE, get current content if not provided
        if data.action == ModificationAction.UPDATE and not data.content_before:
            # Try to get from database first
            config_stmt = select(HaConfig).where(
                and_(
                    HaConfig.server_id == data.server_id,
                    HaConfig.path == data.file_path
                )
            )
            config_result = await db.execute(config_stmt)
            existing_config = config_result.scalar_one_or_none()

            if existing_config and existing_config.content:
                content_before = existing_config.content
            else:
                # Try to read from server
                try:
                    content_before = await read_remote_file(server, data.file_path)
                except Exception as e:
                    logger.warning(f"Could not read original file content: {e}")
                    content_before = None
        else:
            content_before = data.content_before

        # Create modification record
        modification = AIFileModification(
            user_id=current_user.id,
            server_id=data.server_id,
            conversation_id=data.conversation_id,
            message_id=data.message_id,
            file_path=data.file_path,
            action=data.action,
            content_before=content_before,
            content_after=data.content_after,
            ai_explanation=data.ai_explanation,
            ai_summary=data.ai_summary,
            status=ModificationStatus.PENDING,
        )

        db.add(modification)
        await db.commit()
        await db.refresh(modification)

        log_integration_event(
            "AI",
            "file_modification_created",
            True,
            {
                "modification_id": str(modification.id),
                "file_path": data.file_path,
                "action": data.action,
                "user_id": current_user.id,
            },
        )

        return modification

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create file modification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create file modification",
        )


@router.get("/modifications", response_model=List[AIFileModificationListResponse])
async def list_modifications(
    server_id: Optional[int] = None,
    status_filter: Optional[ModificationStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List AI file modifications for the current user.

    Can be filtered by server_id and status.
    """
    try:
        stmt = select(AIFileModification).where(AIFileModification.user_id == current_user.id)

        if server_id:
            stmt = stmt.where(AIFileModification.server_id == server_id)

        if status_filter:
            stmt = stmt.where(AIFileModification.status == status_filter)

        stmt = stmt.order_by(AIFileModification.created_at.desc())

        result = await db.execute(stmt)
        modifications = list(result.scalars().all())

        return modifications

    except Exception as e:
        logger.exception(f"Failed to list modifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list modifications",
        )


@router.get("/modifications/{modification_id}", response_model=AIFileModificationDiff)
async def get_modification_diff(
    modification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get file modification with BEFORE/AFTER diff.

    Returns the full modification including original and modified content
    for diff viewer display.
    """
    try:
        stmt = select(AIFileModification).where(
            and_(
                AIFileModification.id == modification_id,
                AIFileModification.user_id == current_user.id
            )
        )
        result = await db.execute(stmt)
        modification = result.scalar_one_or_none()

        if not modification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modification not found"
            )

        return modification

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get modification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get modification",
        )


@router.post("/modifications/{modification_id}/review", response_model=AIFileModificationResponse)
async def review_modification(
    modification_id: UUID,
    review_data: AIFileModificationReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Review (approve/reject) a file modification.

    User can approve or reject AI-proposed changes.
    Approved changes can then be pushed to server or GitHub.
    """
    try:
        stmt = select(AIFileModification).where(
            and_(
                AIFileModification.id == modification_id,
                AIFileModification.user_id == current_user.id
            )
        )
        result = await db.execute(stmt)
        modification = result.scalar_one_or_none()

        if not modification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modification not found"
            )

        # Update status
        modification.status = review_data.status
        modification.review_comment = review_data.review_comment
        modification.reviewed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(modification)

        log_integration_event(
            "AI",
            "file_modification_reviewed",
            True,
            {
                "modification_id": str(modification.id),
                "status": review_data.status,
                "user_id": current_user.id,
            },
        )

        return modification

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to review modification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to review modification",
        )


@router.post("/modifications/{modification_id}/push", response_model=AIFileModificationResponse)
async def push_modification(
    modification_id: UUID,
    push_data: AIFileModificationPush,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Push approved modification to server and/or GitHub.

    Only approved modifications can be pushed.
    Can push to server, GitHub, or both simultaneously.
    """
    try:
        stmt = select(AIFileModification).where(
            and_(
                AIFileModification.id == modification_id,
                AIFileModification.user_id == current_user.id
            )
        )
        result = await db.execute(stmt)
        modification = result.scalar_one_or_none()

        if not modification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modification not found"
            )

        # Must be approved to push
        if modification.status != ModificationStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only approved modifications can be pushed"
            )

        # Get server
        server_stmt = select(Server).where(Server.id == modification.server_id)
        server_result = await db.execute(server_stmt)
        server = server_result.scalar_one_or_none()

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )

        # Push to server if requested
        if push_data.push_to_server:
            try:
                await write_remote_file(server, modification.file_path, modification.content_after)
                modification.pushed_to_server = True
                modification.pushed_to_server_at = datetime.utcnow()

                # Also update in database
                config_stmt = select(HaConfig).where(
                    and_(
                        HaConfig.server_id == modification.server_id,
                        HaConfig.path == modification.file_path
                    )
                )
                config_result = await db.execute(config_stmt)
                existing_config = config_result.scalar_one_or_none()

                if existing_config:
                    existing_config.content = modification.content_after
                else:
                    new_config = HaConfig(
                        server_id=modification.server_id,
                        path=modification.file_path,
                        content=modification.content_after,
                    )
                    db.add(new_config)

            except Exception as e:
                logger.error(f"Failed to push to server: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to push to server: {str(e)}"
                )

        # Push to GitHub if requested
        if push_data.push_to_github:
            # Import here to avoid circular dependency
            from app.services.github_deployment_service import GitHubDeploymentService

            try:
                github_service = GitHubDeploymentService(db)

                # Push to GitHub
                commit_message = push_data.commit_message or f"AI modification: {modification.ai_summary or modification.file_path}"
                result = await github_service.push_to_github(
                    server_id=modification.server_id,
                    branch=None,  # Use default branch
                    commit_message=commit_message,
                )

                modification.pushed_to_github = True
                modification.pushed_to_github_at = datetime.utcnow()
                modification.github_commit_sha = result.get("commit_sha")

            except Exception as e:
                logger.error(f"Failed to push to GitHub: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to push to GitHub: {str(e)}"
                )

        await db.commit()
        await db.refresh(modification)

        log_integration_event(
            "AI",
            "file_modification_pushed",
            True,
            {
                "modification_id": str(modification.id),
                "pushed_to_server": push_data.push_to_server,
                "pushed_to_github": push_data.push_to_github,
                "user_id": current_user.id,
            },
        )

        return modification

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to push modification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to push modification",
        )


@router.delete("/modifications/{modification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_modification(
    modification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a file modification.

    Can only delete pending modifications that haven't been pushed.
    """
    try:
        stmt = select(AIFileModification).where(
            and_(
                AIFileModification.id == modification_id,
                AIFileModification.user_id == current_user.id
            )
        )
        result = await db.execute(stmt)
        modification = result.scalar_one_or_none()

        if not modification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modification not found"
            )

        # Don't allow deletion of pushed modifications
        if modification.pushed_to_server or modification.pushed_to_github:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete modifications that have been pushed"
            )

        await db.delete(modification)
        await db.commit()

        log_integration_event(
            "AI",
            "file_modification_deleted",
            True,
            {
                "modification_id": str(modification_id),
                "user_id": current_user.id,
            },
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete modification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete modification",
        )
