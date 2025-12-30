import asyncio
import sys
import os

# Add parent dir to path to find app module
sys.path.append(os.getcwd())

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.server import Server, ServerType, ServerStatus
from app.utils.security import hash_password
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        # Create Admin User
        stmt = select(User).where(User.username == "admin")
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print("Creating admin user...")
            user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("Admin123!"),
                full_name="Administrator",
                is_active=True,
                is_admin=True,
                is_superuser=True
            )
            session.add(user)
            await session.commit()
            print("Admin user created.")
            print("Credentials: admin / Admin123!")
        else:
            print("Admin user already exists.")
            print("Credentials: admin / Admin123! (assuming unchanged)")

        # Create Server
        stmt = select(Server).where(Server.host == "192.168.1.116")
        result = await session.execute(stmt)
        server = result.scalar_one_or_none()
        
        if not server:
            print("Creating server 192.168.1.116...")
            server = Server(
                name="Home Assistant (192.168.1.116)",
                host="192.168.1.116",
                port=8123,
                use_ssl=False,
                ssh_host="192.168.1.116",
                ssh_port=22,
                ssh_user="root",
                ssh_key_path="/app/bbb_rsa_trad.pem",
                server_type=ServerType.TEST,
                status=ServerStatus.ONLINE,
                config_path="/config",
                is_active=True
            )
            session.add(server)
            await session.commit()
            print("Server created.")
        else:
            print("Server 192.168.1.116 already exists.")
            # Update key path just in case
            server.ssh_key_path = "/app/bbb_rsa_trad.pem"
            server.ssh_user = "root"
            await session.commit()
            print("Server updated with new key path.")

if __name__ == "__main__":
    asyncio.run(main())
