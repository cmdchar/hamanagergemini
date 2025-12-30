from typing import List, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.server import Server
from app.models.deployment import Deployment, DeploymentResult, DeploymentStatus
from app.models.backup import Backup
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics."""
    
    # Counts
    total_servers = await db.scalar(select(func.count(Server.id)))
    total_backups = await db.scalar(select(func.count(Backup.id)))
    
    # Active deployments
    active_deployments = await db.scalar(
        select(func.count(Deployment.id)).where(
            Deployment.status.in_([
                DeploymentStatus.PENDING,
                DeploymentStatus.VALIDATING,
                DeploymentStatus.BACKING_UP,
                DeploymentStatus.DEPLOYING,
                DeploymentStatus.RESTARTING
            ])
        )
    )
    
    # Recent activities (last 5 deployments)
    recent_deployments_result = await db.execute(
        select(DeploymentResult)
        .order_by(desc(DeploymentResult.created_at))
        .limit(5)
    )
    recent_deployments = recent_deployments_result.scalars().all()
    
    recent_activities = []
    for d in recent_deployments:
        recent_activities.append({
            "id": str(d.id),
            "type": "deployment",
            "message": f"Deployment to server {d.server_id}",
            "timestamp": d.created_at.isoformat() if d.created_at else datetime.now().isoformat()
        })
        
    # System health (Mock data as we don't have agent monitoring yet)
    system_health = {
        "cpu_usage": 15,
        "memory_usage": 45,
        "disk_usage": 30
    }
    
    # Activity chart (Last 7 days mock or aggregated)
    # Returning empty list or mock data for chart to render
    activity_chart = []
    today = datetime.now()
    for i in range(7):
        date = (today - timedelta(days=6-i)).strftime("%Y-%m-%d")
        activity_chart.append({
            "date": date,
            "deployments": 0,
            "backups": 0
        })
    
    return {
        "total_servers": total_servers or 0,
        "active_deployments": active_deployments or 0,
        "total_backups": total_backups or 0,
        "recent_activities": recent_activities,
        "system_health": system_health,
        "activity_chart": activity_chart
    }
