import paramiko
import asyncio
import os
import sys

async def verify_ssh():
    host = "192.168.1.116"
    username = "root"
    key_path = "/app/bbb_rsa_trad.pem"  # In container path
    
    print(f"Testing connection to {username}@{host} with key {key_path}")
    
    if not os.path.exists(key_path):
        print(f"Error: Key file not found at {key_path}")
        return

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # key_filename takes a list or string
            client.connect(host, username=username, key_filename=key_path, timeout=10)
            print("SUCCESS: Connected via key_filename!")
            stdin, stdout, stderr = client.exec_command("echo 'SSH Connection Working inside Container'")
            print(f"Output: {stdout.read().decode().strip()}")
            client.close()
            return
        except paramiko.SSHException as e:
            print(f"Connection failed: {e}", file=sys.stderr)
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(verify_ssh())
