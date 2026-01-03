import asyncio
import sys
import os

# Add /app to python path
sys.path.append("/app")

from app.db.session import AsyncSessionLocal
from app.models.server import Server
from app.utils.security import decrypt_value
from sqlalchemy import select

async def get_server_details():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Server).where(Server.id == 1))
        server = result.scalar_one_or_none()
        
        if not server:
            print("Server 1 not found")
            return

        print(f"Host: {server.host}")
        print(f"Port: {server.port}")
        print(f"Use SSL: {server.use_ssl}")
        print(f"SSH User: {server.ssh_user}")
        print(f"SSH Key Path: {server.ssh_key_path}")
        
        if server.access_token:
            try:
                token = decrypt_value(server.access_token)
                print(f"Decrypted Token: {token[:10]}...{token[-10:]}")
            except Exception as e:
                print(f"Error decrypting token: {e}")
        else:
            print("No access token")

if __name__ == "__main__":
    asyncio.run(get_server_details())
