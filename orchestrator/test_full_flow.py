import requests
import sys

API_URL = "http://localhost:8081/api/v1"
LOGIN_DATA = {"username": "admin", "password": "Admin123!"}

def test_flow():
    # 1. Login
    print("1. Logging in...")
    resp = None
    try:
        resp = requests.post(f"{API_URL}/auth/login", json=LOGIN_DATA)
        resp.raise_for_status()
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("   Login successful.")
    except Exception as e:
        print(f"   Login failed: {e}")
        if resp:
            print(f"   Response: {resp.text}")
        return

    # 2. List Servers
    print("2. Listing servers...")
    try:
        resp = requests.get(f"{API_URL}/servers", headers=headers)
        resp.raise_for_status()
        servers = resp.json()
        print(f"   Found {len(servers)} servers.")
        target_server = None
        for s in servers:
            print(f"   - Server {s['id']}: {s['name']} ({s['host']})")
            if s['host'] == "192.168.1.116":
                target_server = s
        
        if not target_server:
            print("   Target server 192.168.1.116 not found via API!")
            return
    except Exception as e:
        print(f"   List servers failed: {e}")
        return

    # 3. Create Deployment
    print("3. Creating deployment (dry run)...")
    deployment_data = {
        "name": "Test Deployment API",
        "target_servers": [target_server['id']],
        "deploy_all": False,
        "skip_validation": True,
        "skip_backup": True,
        "auto_restart": False,
        "auto_rollback": True,
        "metadata": {
            "path": "/config",
            "config_path": "/config"
        }
    }
    
    try:
        resp = requests.post(f"{API_URL}/deployments", json=deployment_data, headers=headers)
        if resp.status_code in [200, 201]:
            print("   Deployment created successfully.")
            print(f"   Response: {resp.json()}")
        else:
            print(f"   Deployment failed with status {resp.status_code}")
            print(f"   Response: {resp.text}")
    except Exception as e:
        print(f"   Deployment request failed: {e}")

if __name__ == "__main__":
    test_flow()
