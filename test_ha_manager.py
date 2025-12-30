import requests
import json
import time

BASE_URL = "http://localhost:8081/api/v1"

def print_step(msg):
    print(f"\n=== {msg} ===")

def test_backend():
    # 0. Check Root and Docs
    print_step("Checking Root and Docs")
    try:
        resp = requests.get("http://localhost:8081/")
        print(f"Root (/): {resp.status_code}")
        print(f"Root content: {resp.text}")
        if resp.status_code == 200:
            # print(f"Root response: {resp.json()}")
            pass
        
        resp = requests.get("http://localhost:8081/api/docs")
        print(f"Docs (/api/docs): {resp.status_code}")
        
        resp = requests.get("http://localhost:8081/docs")
        print(f"Docs (/docs): {resp.status_code}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # 1. Register
    print_step("Testing Registration")
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Password123!",
        "full_name": "Test User"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if resp.status_code == 201:
            print("Registration successful")
        elif resp.status_code == 400 and "already registered" in resp.text:
             print("User already registered, proceeding to login")
        else:
            print(f"Registration failed: {resp.status_code} - {resp.text}")
            return
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # 2. Login
    print_step("Testing Login")
    login_data = {
        "username": "testuser",
        "password": "Password123!"
    }
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} - {resp.text}")
        return
    
    token_data = resp.json()
    access_token = token_data["access_token"]
    print(f"Login successful. Token: {access_token[:10]}...")
    
    headers = {"Authorization": f"Bearer {access_token}"}

    # 3. List Servers (should be empty or existing)
    print_step("Listing Servers")
    resp = requests.get(f"{BASE_URL}/servers", headers=headers)
    if resp.status_code == 200:
        servers = resp.json()
        print(f"Found {len(servers)} servers")
    else:
        print(f"List servers failed: {resp.status_code} - {resp.text}")

    # 4. Create Server
    print_step("Creating Server")
    server_data = {
        "name": "Test HA Server",
        "host": "192.168.1.100",
        "port": 8123,
        "use_ssl": False,
        "ssh_port": 22,
        "ssh_user": "root",
        "server_type": "production"
    }
    resp = requests.post(f"{BASE_URL}/servers", json=server_data, headers=headers)
    if resp.status_code == 201:
        new_server = resp.json()
        print(f"Server created: {new_server['id']} - {new_server['name']}")
        server_id = new_server['id']
    else:
        print(f"Create server failed: {resp.status_code} - {resp.text}")
        server_id = None

    # 5. List Servers again
    if server_id:
        print_step("Verifying Server Creation")
        resp = requests.get(f"{BASE_URL}/servers", headers=headers)
        servers = resp.json()
        found = any(s['id'] == server_id for s in servers)
        print(f"Server found in list: {found}")

    # 6. Delete Server (Cleanup)
    if server_id:
        print_step("Deleting Server")
        resp = requests.delete(f"{BASE_URL}/servers/{server_id}", headers=headers)
        if resp.status_code == 204:
            print("Server deleted successfully")
        else:
             print(f"Delete server failed: {resp.status_code} - {resp.text}")

def test_frontend():
    print_step("Testing Frontend Availability")
    try:
        resp = requests.get("http://localhost:3000")
        if resp.status_code == 200:
            print("Frontend is reachable (200 OK)")
        else:
            print(f"Frontend returned {resp.status_code}")
    except Exception as e:
        print(f"Frontend unreachable: {e}")

if __name__ == "__main__":
    test_backend()
    test_frontend()
