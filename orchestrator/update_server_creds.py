import asyncio
import sys
import os

# Add /app to python path
sys.path.append("/app")

from app.db.session import AsyncSessionLocal
from app.models.server import Server
from app.utils.security import encrypt_value
from sqlalchemy import select

async def update_creds():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Server).where(Server.id == 1))
        server = result.scalar_one_or_none()
        
        if not server:
            print("Server 1 not found")
            return

        print(f"Current SSH User: {server.ssh_user}")
        
        # Update SSH User to root
        server.ssh_user = "root"
        print("Updated SSH User to: root")
        
        # Ensure Key path is correct
        server.ssh_key_path = "/app/ssh_keys/bbb.ppk"
        
        # Update SSH Passphrase
        ssh_passphrase = "NiKu987410"
        server.ssh_key_passphrase = encrypt_value(ssh_passphrase)
        print(f"Updated SSH passphrase")

        await db.commit()
        print("Database updated successfully.")

if __name__ == "__main__":
    asyncio.run(update_creds())
