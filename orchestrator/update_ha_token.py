import asyncio
import sys
import os
import argparse

# Add current directory to python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from app.db.session import AsyncSessionLocal
from app.models.server import Server
from app.utils.security import encrypt_value
from sqlalchemy import select

async def update_token(token, server_id=1):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Server).where(Server.id == server_id))
        server = result.scalar_one_or_none()
        
        if not server:
            print(f"Server {server_id} not found")
            return

        print(f"Updating HA Access Token for Server: {server.host}")
        
        encrypted_token = encrypt_value(token)
        server.access_token = encrypted_token
        
        await db.commit()
        print("Database updated successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update Home Assistant Access Token')
    parser.add_argument('token', help='The Long-Lived Access Token')
    parser.add_argument('--server-id', type=int, default=1, help='Server ID (default: 1)')
    
    args = parser.parse_args()
    asyncio.run(update_token(args.token, args.server_id))
