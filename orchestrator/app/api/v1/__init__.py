"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import ai, auth, backup, deployments, esphome, fpp, security, servers, tailscale, wled, wled_schedules, dashboard, terminal

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router)
api_router.include_router(servers.router)
api_router.include_router(deployments.router)
api_router.include_router(dashboard.router)
api_router.include_router(wled.router)
api_router.include_router(wled_schedules.router)
api_router.include_router(fpp.router)
api_router.include_router(tailscale.router)
api_router.include_router(esphome.router)
api_router.include_router(backup.router)
api_router.include_router(ai.router)
api_router.include_router(security.router)
api_router.include_router(terminal.router)
