import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8081/api/v1"
EMAIL = "admin"
PASSWORD = "Admin123!"

async def test_ha_features():
    async with aiohttp.ClientSession() as session:
        # 1. Login
        logger.info("Authenticating...")
        async with session.post(f"{API_URL}/auth/login", json={"username": EMAIL, "password": PASSWORD}) as resp:
            if resp.status != 200:
                logger.error(f"Login failed: {resp.status} {await resp.text()}")
                return
            data = await resp.json()
            token = data["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            logger.info("Login successful.")

        # 2. Get Servers
        logger.info("Fetching servers...")
        server_id = None
        async with session.get(f"{API_URL}/servers", headers=headers) as resp:
            if resp.status != 200:
                logger.error(f"Failed to get servers: {resp.status}")
                return
            servers = await resp.json()
            logger.info(f"Found {len(servers)} servers.")
            for s in servers:
                logger.info(f" - {s['name']} ({s['host']})")
                if s['host'] == "192.168.1.116":
                    server_id = s['id']
        
        if not server_id:
            logger.warning("Target server 192.168.1.116 not found. Skipping sync test.")
            return

        # 3. Test Sync Config
        logger.info(f"Testing Config Sync for server {server_id}...")
        async with session.post(f"{API_URL}/servers/{server_id}/sync-config", headers=headers) as resp:
            if resp.status == 200:
                configs = await resp.json()
                logger.info(f"Sync successful. Found {len(configs)} config files.")
                for c in configs[:5]: # Show first 5
                    logger.info(f" - {c['path']}")
            else:
                text = await resp.text()
                logger.error(f"Sync failed: {resp.status} {text}")

        # 4. Test Get Configs
        logger.info("Fetching stored configs...")
        async with session.get(f"{API_URL}/servers/{server_id}/configs", headers=headers) as resp:
            if resp.status == 200:
                configs = await resp.json()
                logger.info(f"Retrieved {len(configs)} stored configs.")
            else:
                logger.error(f"Failed to get configs: {resp.status}")

        # 5. Test Terminal WebSocket (Connect only)
        logger.info("Testing Terminal WebSocket connection...")
        ws_url = f"{API_URL.replace('http', 'ws')}/terminal/{server_id}?token={token}"
        try:
            async with session.ws_connect(ws_url) as ws:
                logger.info("WebSocket connected.")
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        logger.info(f"Terminal Output: {msg.data.strip()}")
                        if "Connection Established" in msg.data or "password" in msg.data.lower() or "#" in msg.data or "$" in msg.data:
                            logger.info("Terminal connection seems active.")
                            break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error('ws connection closed with exception %s', ws.exception())
                        break
        except Exception as e:
            logger.error(f"WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ha_features())
