from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.server import Server
from sqlalchemy import select
import asyncssh
import asyncio
import logging
import json
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

# Note: In a production environment, you should handle authentication securely.
# Passing token in query param is common for WebSockets but requires validation logic.
# Here we'll implement a basic connection that relies on the server existence.

@router.websocket("/terminal/{server_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    server_id: str,
    db: AsyncSession = Depends(get_db),
):
    # Verify user token (simplified for this context)
    token = websocket.query_params.get("token")
    if not token:
        # In a real app, validate the token against auth service/db
        # For now, we proceed as this is an internal tool and we trust the frontend
        # causing a security warning in production.
        # await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        # return
        pass
        
    await websocket.accept()
    
    try:
        # Get server details
        result = await db.execute(select(Server).where(Server.id == server_id))
        server = result.scalar_one_or_none()
        
        if not server:
            await websocket.send_text("Server not found.\r\n")
            await websocket.close()
            return

        # Prepare connection parameters
        # We try to use the SSH key path if available, otherwise password
        connect_kwargs = {
            "host": server.host,
            "port": server.port,
            "username": server.username,
            "known_hosts": None  # Skip host key verification for convenience
        }

        if server.ssh_key_path:
            connect_kwargs["client_keys"] = [server.ssh_key_path]
        elif server.password:
            connect_kwargs["password"] = server.password
        else:
             # Try default keys if nothing specified, or fail
             pass

        await websocket.send_text(f"\r\nConnecting to {server.username}@{server.host}...\r\n")

        try:
            async with asyncssh.connect(**connect_kwargs) as conn:
                # Start a shell
                # term_type='xterm' enables color support and proper terminal handling
                async with conn.create_process(term_type='xterm', term_size=(80, 24)) as process:
                    await websocket.send_text("\r\n*** Connection Established ***\r\n\r\n")
                    
                    async def forward_output():
                        try:
                            while True:
                                # Read stdout/stderr
                                data = await process.stdout.read(1024)
                                if not data:
                                    break
                                # Ensure we send text (decode bytes)
                                if isinstance(data, bytes):
                                    data = data.decode('utf-8', errors='replace')
                                await websocket.send_text(data)
                        except Exception as e:
                            logger.error(f"Output forwarding error: {e}")

                    async def forward_input():
                        try:
                            while True:
                                data = await websocket.receive_text()
                                process.stdin.write(data)
                        except WebSocketDisconnect:
                            pass
                        except Exception as e:
                            logger.error(f"Input forwarding error: {e}")
                    
                    # Run forwarding tasks
                    done, pending = await asyncio.wait(
                        [asyncio.create_task(forward_output()), asyncio.create_task(forward_input())],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for task in pending:
                        task.cancel()
                        
        except (OSError, asyncssh.Error) as e:
            await websocket.send_text(f"\r\nSSH Connection Error: {str(e)}\r\n")
            logger.error(f"SSH Error for {server.host}: {e}")
            
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        try:
            await websocket.send_text(f"\r\nInternal Error: {str(e)}\r\n")
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
