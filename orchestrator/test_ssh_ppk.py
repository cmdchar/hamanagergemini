import asyncio
import asyncssh
import sys
import os

# Add /app to python path to import app modules
sys.path.append("/app")

try:
    from app.utils.ssh import get_usable_key_path
except ImportError:
    # If running locally without app structure, mock or adjust path
    sys.path.append(os.path.join(os.getcwd()))
    from app.utils.ssh import get_usable_key_path

async def test_connection():
    host = "homeassistant.local"  # User provided hostname
    # host = "192.168.1.116" # Fallback IP from previous context
    username = "root"
    # key_path = "/app/ssh_keys/bbb.ppk"
    # Use relative path if /app not found
    if os.path.exists("/app/ssh_keys/bbb.ppk"):
        key_path = "/app/ssh_keys/bbb.ppk"
    else:
        key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ssh_keys", "bbb.ppk")
    passphrase = "NiKu987410"

    print(f"Testing connection to {username}@{host}")
    print(f"Original key: {key_path}")
    
    if not os.path.exists(key_path):
        print(f"ERROR: Key file not found at {key_path}")
        return

    try:
        # Convert key if needed
        print("Converting key if needed...")
        real_key_path, real_passphrase = get_usable_key_path(key_path, passphrase)
        print(f"Using key path: {real_key_path}")
        
        # Connect
        print("Connecting...")
        async with asyncssh.connect(
            host, 
            username=username, 
            client_keys=[real_key_path],
            passphrase=real_passphrase,
            known_hosts=None
        ) as conn:
            print("Connected! Running test command...")
            result = await conn.run("echo 'Hello from HA Config Manager!'", check=True)
            print(f"Command output: {result.stdout.strip()}")
            print("SUCCESS: SSH connection established and command executed.")

    except OSError as e:
        print(f"Network/Socket Error: {e}")
        print("Tip: If host is not found, try using the IP address (e.g. 192.168.1.116)")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
