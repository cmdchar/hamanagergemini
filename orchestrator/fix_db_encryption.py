import asyncio
import sys
import os

# Add current directory to python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from app.db.session import AsyncSessionLocal
from app.models.server import Server
from app.utils.security import encrypt_value
from sqlalchemy import select

async def fix_encryption():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Server).where(Server.id == 1))
        server = result.scalar_one_or_none()
        
        if not server:
            print("Server 1 not found")
            return

        print(f"Updating encryption for Server: {server.host}")
        
        # Update SSH Passphrase
        ssh_passphrase = "NiKu987410"
        server.ssh_key_passphrase = encrypt_value(ssh_passphrase)
        print(f"Updated SSH passphrase to: {ssh_passphrase} (encrypted)")

        # We cannot recover the HA Access Token if decryption fails.
        # But we can clear it or leave it broken. 
        # If we leave it broken, it will cause errors.
        # Better to set it to None if it fails decryption? 
        # No, let's just warn the user.
        
        await db.commit()
        print("Database updated successfully.")

if __name__ == "__main__":
    asyncio.run(fix_encryption())
