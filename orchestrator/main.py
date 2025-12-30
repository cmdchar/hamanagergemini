"""
HA Config Manager - Cloud Orchestrator
Gestionează deployment-uri către multiple instanțe Home Assistant
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import httpx
import logging
from datetime import datetime
import json

# Configurare logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HA Config Manager API", version="1.0.0")

# CORS pentru frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # În producție, specifică domeniile
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Server(BaseModel):
    id: str
    name: str
    ip: str
    port: int = 8099
    status: str = "unknown"
    last_sync: Optional[datetime] = None
    ha_version: Optional[str] = None

class DeploymentRequest(BaseModel):
    server_ids: List[str]
    github_repo: str
    branch: str = "main"
    force: bool = False

class WebhookPayload(BaseModel):
    ref: str
    repository: Dict
    commits: List[Dict]

class ServerEvent(BaseModel):
    server_id: str
    event: str
    timestamp: float
    data: Dict = {}

# Database în memorie (în producție: PostgreSQL)
servers_db: Dict[str, Server] = {
    "server-61": Server(
        id="server-61",
        name="HA Server Living Room",
        ip="192.168.1.61",
        status="online"
    ),
    "server-99": Server(
        id="server-99",
        name="HA Server Bedroom",
        ip="192.168.1.99",
        status="online"
    ),
    "server-68": Server(
        id="server-68",
        name="HA Server Office",
        ip="192.168.1.68",
        status="online"
    ),
}

deployment_history = []

# API Routes

@app.get("/")
async def root():
    return {
        "name": "HA Config Manager API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/servers", response_model=List[Server])
async def get_servers():
    """Returnează lista de servere"""
    return list(servers_db.values())

@app.get("/api/servers/{server_id}", response_model=Server)
async def get_server(server_id: str):
    """Returnează informații despre un server specific"""
    if server_id not in servers_db:
        raise HTTPException(status_code=404, detail="Server not found")
    return servers_db[server_id]

@app.post("/api/servers")
async def add_server(server: Server):
    """Adaugă un server nou"""
    if server.id in servers_db:
        raise HTTPException(status_code=400, detail="Server already exists")

    servers_db[server.id] = server
    logger.info(f"Server added: {server.id}")
    return {"status": "success", "server": server}

@app.delete("/api/servers/{server_id}")
async def remove_server(server_id: str):
    """Șterge un server"""
    if server_id not in servers_db:
        raise HTTPException(status_code=404, detail="Server not found")

    del servers_db[server_id]
    logger.info(f"Server removed: {server_id}")
    return {"status": "success"}

@app.post("/api/deploy")
async def deploy(request: DeploymentRequest, background_tasks: BackgroundTasks):
    """Deploy configurații către servere"""
    logger.info(f"Deployment request for servers: {request.server_ids}")

    # Validează serverele
    invalid_servers = [sid for sid in request.server_ids if sid not in servers_db]
    if invalid_servers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid servers: {invalid_servers}"
        )

    # Adaugă task-uri de deployment în background
    for server_id in request.server_ids:
        background_tasks.add_task(
            deploy_to_server,
            server_id,
            request.github_repo,
            request.branch
        )

    deployment = {
        "id": f"deploy-{datetime.now().timestamp()}",
        "servers": request.server_ids,
        "github_repo": request.github_repo,
        "branch": request.branch,
        "status": "in_progress",
        "timestamp": datetime.now().isoformat()
    }
    deployment_history.append(deployment)

    return {
        "status": "deployment_started",
        "deployment": deployment
    }

@app.post("/api/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Primește webhook de la GitHub"""
    payload = await request.json()

    logger.info(f"GitHub webhook received")
    logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

    # Extrage informații
    ref = payload.get('ref', '')
    repo_name = payload.get('repository', {}).get('full_name', '')

    logger.info(f"Push to {ref} in {repo_name}")

    # Determină ce servere trebuie update-ate
    # În acest PoC, deploy la toate serverele
    if ref.startswith('refs/heads/'):
        branch = ref.replace('refs/heads/', '')

        # Deploy la toate serverele care monitorizează acest branch
        for server in servers_db.values():
            background_tasks.add_task(
                deploy_to_server,
                server.id,
                repo_name,
                branch
            )

        return {
            "status": "deployment_triggered",
            "servers": list(servers_db.keys()),
            "branch": branch
        }

    return {"status": "ignored"}

@app.post("/api/events")
async def receive_event(event: ServerEvent):
    """Primește evenimente de la servere (add-on agents)"""
    logger.info(f"Event from {event.server_id}: {event.event}")

    if event.server_id in servers_db:
        server = servers_db[event.server_id]

        # Update status pe baza event-ului
        if event.event == 'sync_started':
            server.status = 'syncing'
        elif event.event == 'sync_completed':
            server.status = 'online'
            server.last_sync = datetime.fromtimestamp(event.timestamp)
        elif event.event == 'sync_failed':
            server.status = 'error'

        servers_db[event.server_id] = server

    return {"status": "received"}

@app.get("/api/deployments")
async def get_deployments():
    """Returnează istoricul deployment-urilor"""
    return deployment_history

@app.get("/api/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "servers_count": len(servers_db),
        "timestamp": datetime.now().isoformat()
    }

# Helper Functions

async def deploy_to_server(server_id: str, repo: str, branch: str):
    """Deploy configurații către un server specific"""
    if server_id not in servers_db:
        logger.error(f"Server {server_id} not found")
        return

    server = servers_db[server_id]
    logger.info(f"Deploying to {server_id} ({server.ip})")

    try:
        # Apelează API-ul add-on-ului de pe server
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"http://{server.ip}:{server.port}/api/sync",
                json={
                    "repo": repo,
                    "branch": branch
                }
            )

            if response.status_code == 200:
                logger.info(f"Deployment to {server_id} successful")
                server.status = "syncing"
            else:
                logger.error(f"Deployment to {server_id} failed: {response.status_code}")
                server.status = "error"

    except httpx.RequestError as e:
        logger.error(f"Failed to connect to {server_id}: {e}")
        server.status = "offline"
    except Exception as e:
        logger.error(f"Deployment error for {server_id}: {e}")
        server.status = "error"

    servers_db[server_id] = server

async def check_server_status(server_id: str):
    """Verifică status-ul unui server"""
    if server_id not in servers_db:
        return

    server = servers_db[server_id]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://{server.ip}:{server.port}/api/status")

            if response.status_code == 200:
                data = response.json()
                server.status = "online"
                server.ha_version = data.get('ha_version')
            else:
                server.status = "unknown"

    except httpx.RequestError:
        server.status = "offline"
    except Exception as e:
        logger.error(f"Status check error for {server_id}: {e}")
        server.status = "error"

    servers_db[server_id] = server

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
