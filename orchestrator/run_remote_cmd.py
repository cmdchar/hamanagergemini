import asyncio
import sys
import os
import argparse

# Add /app to python path
sys.path.append("/app")

from app.utils.ssh import get_usable_key_path
import asyncssh

async def run_remote_command(cmd_to_run):
    host = "homeassistant.local"
    username = "root"
    key_path = "/app/ssh_keys/bbb.ppk"
    passphrase = "NiKu987410"
    
    # 1. Convert key
    real_key_path, real_passphrase = get_usable_key_path(key_path, passphrase)
    
    try:
        # 2. Connect
        print(f"Connecting to {username}@{host}...")
        async with asyncssh.connect(
            host, 
            username=username, 
            client_keys=[real_key_path],
            passphrase=real_passphrase,
            known_hosts=None
        ) as conn:
            print(f"Running command: {cmd_to_run}")
            print("-" * 40)
            
            # 3. Run command
            result = await conn.run(cmd_to_run, check=False)
            
            # 4. Show output
            print(result.stdout, end="")
            if result.stderr:
                print("STDERR:", result.stderr, end="")
            
            print("-" * 40)
            print(f"Exit Code: {result.exit_status}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 run_remote_cmd.py <command>")
        sys.exit(1)
    
    cmd = " ".join(sys.argv[1:])
    asyncio.run(run_remote_command(cmd))
