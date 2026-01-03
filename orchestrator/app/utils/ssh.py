import os
import tempfile
import subprocess
import logging
import stat
from typing import Optional, Tuple, Dict, Any, List

import asyncssh

from app.utils.security import decrypt_value

logger = logging.getLogger(__name__)

def get_usable_key_path(key_path: str, passphrase: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Get a usable key path (converting PPK to OpenSSH if necessary) and the passphrase to use.
    Returns (key_path, passphrase).
    """
    if not key_path or not os.path.exists(key_path):
        return key_path, passphrase

    # Check headers
    is_ppk = False
    try:
        with open(key_path, 'r') as f:
            first_line = f.readline()
            if 'PuTTY-User-Key-File' in first_line:
                is_ppk = True
    except Exception as e:
        logger.warning(f"Could not read key file header: {e}")
        pass

    if is_ppk:
        # Convert to OpenSSH
        openssh_path = key_path + ".openssh"
        
        # If conversion already exists, we could reuse it, but we should ensure it works with current passphrase.
        # To be safe, let's regenerate it if we have a passphrase, or if it doesn't exist.
        # But regenerating every time is slow.
        # Let's regenerate if it doesn't exist.
        if os.path.exists(openssh_path):
            # We assume it was converted correctly with the same passphrase.
            # If the file exists, return it immediately to avoid unnecessary conversion
            # or failure if puttygen is missing.
            logger.info(f"Using existing OpenSSH key at {openssh_path}")
            return openssh_path, passphrase

        logger.info(f"Converting PPK key {key_path} to OpenSSH format at {openssh_path}")

        cmd = ["puttygen", key_path, "-O", "private-openssh", "-o", openssh_path]
        
        pass_file = None
        try:
            if passphrase:
                fd, pass_file = tempfile.mkstemp()
                with os.fdopen(fd, 'w') as f:
                    f.write(passphrase)
                cmd.extend(["--old-passphrase", pass_file])
                # We keep the passphrase for the new key (default behavior)
                # So we return the passphrase as is.
            
            # If no passphrase, puttygen might prompt if the key is actually encrypted.
            # But we can't handle prompts.
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"puttygen failed: {result.stderr}")
                return key_path, passphrase
            
            return openssh_path, passphrase
            
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return key_path, passphrase
        finally:
            if pass_file and os.path.exists(pass_file):
                os.unlink(pass_file)
                
    return key_path, passphrase

async def get_ssh_connection_params(server: Any) -> Dict[str, Any]:
    """Helper to construct SSH connection parameters from a server object."""
    connect_kwargs = {
        "host": server.ssh_host or server.host,
        "port": server.ssh_port or 22,
        "username": server.ssh_user,
        "known_hosts": None,
    }

    if server.ssh_key_path:
        passphrase = None
        if server.ssh_key_passphrase:
            try:
                passphrase = decrypt_value(server.ssh_key_passphrase)
            except Exception as e:
                logger.error(f"Failed to decrypt passphrase: {e}")
        
        real_key_path, real_passphrase = get_usable_key_path(server.ssh_key_path, passphrase)
        connect_kwargs["client_keys"] = [real_key_path]
        if real_passphrase:
            connect_kwargs["passphrase"] = real_passphrase
    elif server.ssh_password:
        try:
            password = decrypt_value(server.ssh_password) if server.ssh_password else None
            connect_kwargs["password"] = password
        except Exception as e:
             logger.error(f"Failed to decrypt password: {e}")

    return connect_kwargs

async def execute_ssh_command(server: Any, command: str) -> Dict[str, Any]:
    """Execute a command via SSH on the server."""
    try:
        connect_kwargs = await get_ssh_connection_params(server)
        async with asyncssh.connect(**connect_kwargs) as conn:
            result = await conn.run(command, check=False)
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_status
            }
    except Exception as e:
        logger.error(f"SSH execution failed: {e}")
        raise e

async def list_remote_files(server: Any, path: str) -> List[Dict[str, Any]]:
    """List files in a remote directory."""
    try:
        connect_kwargs = await get_ssh_connection_params(server)
        async with asyncssh.connect(**connect_kwargs) as conn:
            async with conn.start_sftp_client() as sftp:
                files = []
                async for entry in sftp.scandir(path):
                    is_dir = False
                    if entry.attrs.permissions is not None:
                         is_dir = stat.S_ISDIR(entry.attrs.permissions)
                    
                    files.append({
                        "name": entry.filename,
                        "path": f"{path.rstrip('/')}/{entry.filename}",
                        "is_dir": is_dir,
                        "size": entry.attrs.size,
                        "mtime": entry.attrs.mtime
                    })
                
                files.sort(key=lambda x: (not x["is_dir"], x["name"]))
                return files
    except Exception as e:
        logger.error(f"SFTP list failed: {e}")
        raise e

async def read_remote_file(server: Any, path: str) -> str:
    """Read a remote file."""
    try:
        connect_kwargs = await get_ssh_connection_params(server)
        async with asyncssh.connect(**connect_kwargs) as conn:
            async with conn.start_sftp_client() as sftp:
                async with sftp.open(path, 'r') as f:
                    return await f.read()
    except Exception as e:
        logger.error(f"SFTP read failed: {e}")
        raise e

async def write_remote_file(server: Any, path: str, content: str):
    """Write content to a remote file."""
    try:
        connect_kwargs = await get_ssh_connection_params(server)
        async with asyncssh.connect(**connect_kwargs) as conn:
            async with conn.start_sftp_client() as sftp:
                async with sftp.open(path, 'w') as f:
                    await f.write(content)
    except Exception as e:
        logger.error(f"SFTP write failed: {e}")
        raise e
