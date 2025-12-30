"""Security API endpoints for secrets management and audit logs."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.integrations.secrets import SecretsManager
from app.models.security import AuditLog, Secret, SecretAccessLog, SecurityEvent
from app.models.user import User
from app.schemas.security import (
    AuditLogFilter,
    AuditLogResponse,
    AuditStatistics,
    SecretCreate,
    SecretResponse,
    SecretRevokeRequest,
    SecretRotateRequest,
    SecretStatistics,
    SecretUpdate,
    SecretWithValue,
    SecurityEventResponse,
    SecurityEventResolveRequest,
    SecurityStatistics,
)
from app.utils.logging import log_integration_event

router = APIRouter(prefix="/security", tags=["security"])
logger = logging.getLogger(__name__)


# Secrets endpoints
@router.post("/secrets", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
async def create_secret(
    data: SecretCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new encrypted secret."""
    try:
        secrets_manager = SecretsManager(db)

        secret = await secrets_manager.create_secret(
            name=data.name,
            value=data.value.get_secret_value(),
            secret_type=data.secret_type,
            description=data.description,
            server_id=data.server_id,
            deployment_id=data.deployment_id,
            integration_type=data.integration_type,
            integration_id=data.integration_id,
            rotation_interval_days=data.rotation_interval_days,
            tags=data.tags,
            user_id=current_user.id,
        )

        if not secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create secret",
            )

        return secret

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create secret",
        )


@router.get("/secrets", response_model=List[SecretResponse])
async def list_secrets(
    skip: int = 0,
    limit: int = 100,
    secret_type: Optional[str] = None,
    server_id: Optional[int] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List secrets (without decrypted values)."""
    try:
        query = select(Secret)

        if active_only:
            query = query.where(Secret.is_active == True, Secret.is_revoked == False)

        if secret_type:
            query = query.where(Secret.secret_type == secret_type)

        if server_id:
            query = query.where(Secret.server_id == server_id)

        query = query.order_by(Secret.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        secrets = list(result.scalars().all())

        return secrets

    except Exception as e:
        logger.exception(f"Failed to list secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list secrets",
        )


@router.get("/secrets/{secret_id}", response_model=SecretResponse)
async def get_secret(
    secret_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get secret metadata (without decrypted value)."""
    try:
        secrets_manager = SecretsManager(db)

        secret = await secrets_manager.get_secret(
            secret_id=secret_id,
            user_id=current_user.id,
        )

        if not secret:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        return secret

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get secret",
        )


@router.get("/secrets/{secret_id}/decrypt", response_model=SecretWithValue)
async def decrypt_secret(
    secret_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Decrypt and return secret value."""
    try:
        secrets_manager = SecretsManager(db)

        # Get secret metadata
        secret = await secrets_manager.get_secret(
            secret_id=secret_id,
            user_id=current_user.id,
        )

        if not secret:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        # Decrypt value
        decrypted_value = await secrets_manager.decrypt_secret(
            secret_id=secret_id,
            user_id=current_user.id,
        )

        if decrypted_value is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot decrypt secret (may be revoked)",
            )

        # Return with decrypted value
        secret_dict = {
            **{k: v for k, v in secret.__dict__.items() if not k.startswith('_')},
            'value': decrypted_value
        }

        return SecretWithValue(**secret_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to decrypt secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt secret",
        )


@router.patch("/secrets/{secret_id}", response_model=SecretResponse)
async def update_secret(
    secret_id: int,
    data: SecretUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update secret metadata."""
    try:
        result = await db.execute(
            select(Secret).where(Secret.id == secret_id)
        )
        secret = result.scalar_one_or_none()

        if not secret:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(secret, field, value)

        await db.commit()
        await db.refresh(secret)

        return secret

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update secret",
        )


@router.post("/secrets/{secret_id}/rotate", response_model=SecretResponse)
async def rotate_secret(
    secret_id: int,
    data: SecretRotateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rotate secret value."""
    try:
        secrets_manager = SecretsManager(db)

        success = await secrets_manager.rotate_secret(
            secret_id=secret_id,
            new_value=data.new_value.get_secret_value(),
            user_id=current_user.id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to rotate secret",
            )

        # Get updated secret
        result = await db.execute(
            select(Secret).where(Secret.id == secret_id)
        )
        secret = result.scalar_one_or_none()

        return secret

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to rotate secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rotate secret",
        )


@router.post("/secrets/{secret_id}/revoke", response_model=SecretResponse)
async def revoke_secret(
    secret_id: int,
    data: SecretRevokeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a secret."""
    try:
        secrets_manager = SecretsManager(db)

        success = await secrets_manager.revoke_secret(
            secret_id=secret_id,
            reason=data.reason,
            user_id=current_user.id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke secret",
            )

        # Get updated secret
        result = await db.execute(
            select(Secret).where(Secret.id == secret_id)
        )
        secret = result.scalar_one_or_none()

        return secret

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to revoke secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke secret",
        )


@router.delete("/secrets/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    secret_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a secret (hard delete)."""
    try:
        result = await db.execute(
            select(Secret).where(Secret.id == secret_id)
        )
        secret = result.scalar_one_or_none()

        if not secret:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )

        await db.delete(secret)
        await db.commit()

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete secret",
        )


# Audit log endpoints
@router.post("/audit-logs/search", response_model=List[AuditLogResponse])
async def search_audit_logs(
    filters: AuditLogFilter,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search audit logs with filters."""
    try:
        query = select(AuditLog)

        if filters.action:
            query = query.where(AuditLog.action == filters.action)

        if filters.category:
            query = query.where(AuditLog.category == filters.category)

        if filters.severity:
            query = query.where(AuditLog.severity == filters.severity)

        if filters.status:
            query = query.where(AuditLog.status == filters.status)

        if filters.user_id:
            query = query.where(AuditLog.user_id == filters.user_id)

        if filters.resource_type:
            query = query.where(AuditLog.resource_type == filters.resource_type)

        if filters.resource_id:
            query = query.where(AuditLog.resource_id == filters.resource_id)

        if filters.start_date:
            query = query.where(AuditLog.created_at >= filters.start_date)

        if filters.end_date:
            query = query.where(AuditLog.created_at <= filters.end_date)

        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        logs = list(result.scalars().all())

        return logs

    except Exception as e:
        logger.exception(f"Failed to search audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search audit logs",
        )


@router.get("/audit-logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit log by ID."""
    try:
        result = await db.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        log = result.scalar_one_or_none()

        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit log not found",
            )

        return log

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get audit log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit log",
        )


# Security events endpoints
@router.get("/security-events", response_model=List[SecurityEventResponse])
async def list_security_events(
    skip: int = 0,
    limit: int = 100,
    severity: Optional[str] = None,
    unresolved_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List security events."""
    try:
        query = select(SecurityEvent)

        if severity:
            query = query.where(SecurityEvent.severity == severity)

        if unresolved_only:
            query = query.where(
                SecurityEvent.response_required == True,
                SecurityEvent.response_status != "resolved",
            )

        query = query.order_by(SecurityEvent.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        events = list(result.scalars().all())

        return events

    except Exception as e:
        logger.exception(f"Failed to list security events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list security events",
        )


@router.post("/security-events/{event_id}/resolve", response_model=SecurityEventResponse)
async def resolve_security_event(
    event_id: int,
    data: SecurityEventResolveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve a security event."""
    try:
        result = await db.execute(
            select(SecurityEvent).where(SecurityEvent.id == event_id)
        )
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Security event not found",
            )

        # Update event
        event.response_status = data.response_status
        event.response_notes = data.response_notes
        event.responded_by_user_id = current_user.id
        event.responded_at = datetime.utcnow()

        await db.commit()
        await db.refresh(event)

        return event

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to resolve security event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve security event",
        )


# Statistics endpoints
@router.get("/secrets/statistics", response_model=SecretStatistics)
async def get_secret_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get secret statistics."""
    try:
        total = await db.scalar(select(func.count(Secret.id)))
        active = await db.scalar(
            select(func.count(Secret.id)).where(
                Secret.is_active == True,
                Secret.is_revoked == False,
            )
        )
        revoked = await db.scalar(
            select(func.count(Secret.id)).where(Secret.is_revoked == True)
        )

        # By type
        type_result = await db.execute(
            select(Secret.secret_type, func.count(Secret.id))
            .where(Secret.is_active == True)
            .group_by(Secret.secret_type)
        )
        by_type = {row[0]: row[1] for row in type_result}

        # Rotation required
        rotation_required = await db.scalar(
            select(func.count(Secret.id)).where(Secret.rotation_required == True)
        )

        # Today's accesses
        today = datetime.utcnow().date()
        accesses_today = await db.scalar(
            select(func.count(SecretAccessLog.id)).where(
                func.date(SecretAccessLog.created_at) == today
            )
        )
        failed_today = await db.scalar(
            select(func.count(SecretAccessLog.id)).where(
                func.date(SecretAccessLog.created_at) == today,
                SecretAccessLog.success == False,
            )
        )

        return SecretStatistics(
            total_secrets=total or 0,
            active_secrets=active or 0,
            revoked_secrets=revoked or 0,
            secrets_by_type=by_type,
            secrets_requiring_rotation=rotation_required or 0,
            total_accesses_today=accesses_today or 0,
            failed_accesses_today=failed_today or 0,
        )

    except Exception as e:
        logger.exception(f"Failed to get secret statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get secret statistics",
        )


@router.get("/audit-logs/statistics", response_model=AuditStatistics)
async def get_audit_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit log statistics."""
    try:
        total = await db.scalar(select(func.count(AuditLog.id)))

        # By category
        cat_result = await db.execute(
            select(AuditLog.category, func.count(AuditLog.id))
            .group_by(AuditLog.category)
        )
        by_category = {row[0]: row[1] for row in cat_result}

        # By severity
        sev_result = await db.execute(
            select(AuditLog.severity, func.count(AuditLog.id))
            .group_by(AuditLog.severity)
        )
        by_severity = {row[0]: row[1] for row in sev_result}

        # Today's events
        today = datetime.utcnow().date()
        today_events = await db.scalar(
            select(func.count(AuditLog.id)).where(
                func.date(AuditLog.created_at) == today
            )
        )
        today_errors = await db.scalar(
            select(func.count(AuditLog.id)).where(
                func.date(AuditLog.created_at) == today,
                AuditLog.status == "failure",
            )
        )

        # Top users
        user_result = await db.execute(
            select(AuditLog.user_id, func.count(AuditLog.id))
            .where(AuditLog.user_id.is_not(None))
            .group_by(AuditLog.user_id)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
        )
        top_users = [{"user_id": row[0], "count": row[1]} for row in user_result]

        # Top actions
        action_result = await db.execute(
            select(AuditLog.action, func.count(AuditLog.id))
            .group_by(AuditLog.action)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
        )
        top_actions = [{"action": row[0], "count": row[1]} for row in action_result]

        return AuditStatistics(
            total_events=total or 0,
            events_by_category=by_category,
            events_by_severity=by_severity,
            events_today=today_events or 0,
            errors_today=today_errors or 0,
            top_users=top_users,
            top_actions=top_actions,
        )

    except Exception as e:
        logger.exception(f"Failed to get audit statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit statistics",
        )


@router.get("/security-events/statistics", response_model=SecurityStatistics)
async def get_security_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get security event statistics."""
    try:
        total = await db.scalar(select(func.count(SecurityEvent.id)))
        critical = await db.scalar(
            select(func.count(SecurityEvent.id)).where(
                SecurityEvent.severity == "critical"
            )
        )
        high = await db.scalar(
            select(func.count(SecurityEvent.id)).where(
                SecurityEvent.severity == "high"
            )
        )
        unresolved = await db.scalar(
            select(func.count(SecurityEvent.id)).where(
                SecurityEvent.response_required == True,
                SecurityEvent.response_status != "resolved",
            )
        )

        # By type
        type_result = await db.execute(
            select(SecurityEvent.event_type, func.count(SecurityEvent.id))
            .group_by(SecurityEvent.event_type)
        )
        by_type = {row[0]: row[1] for row in type_result}

        # Requiring response
        requiring_response = await db.scalar(
            select(func.count(SecurityEvent.id)).where(
                SecurityEvent.response_required == True,
                SecurityEvent.response_status.is_(None),
            )
        )

        return SecurityStatistics(
            total_events=total or 0,
            critical_events=critical or 0,
            high_severity_events=high or 0,
            unresolved_events=unresolved or 0,
            events_by_type=by_type,
            events_requiring_response=requiring_response or 0,
        )

    except Exception as e:
        logger.exception(f"Failed to get security statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security statistics",
        )
