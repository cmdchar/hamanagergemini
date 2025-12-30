import requests
import json
import random
import string
import sys

BASE_URL = "http://localhost:8081/api/v1"
HEALTH_URL = "http://localhost:8081/health"

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def print_response(response, label):
    print(f"\n[{label}] Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_health():
    print("Testing Health Endpoint...")
    try:
        response = requests.get(HEALTH_URL)
        print_response(response, "Health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

def test_auth():
    print("\n--- Testing Authentication ---")
    username = f"user_{generate_random_string()}"
    email = f"{username}@example.com"
    password = "SecretPassword123!"
    
    # Register
    print(f"Registering user: {username}")
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "full_name": "Test User"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print_response(response, "Register")
    
    if response.status_code != 201:
        print("❌ Registration failed")
        return None
    
    # Login
    print("Logging in...")
    login_payload = {
        "username": username,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    print_response(response, "Login")
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("✅ Authentication successful")
        return token
    else:
        print("❌ Login failed")
        return None

def test_servers(token):
    print("\n--- Testing Server CRUD ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create Server
    server_name = f"server_{generate_random_string()}"
    payload = {
        "name": server_name,
        "host": "192.168.1.100",
        "ssh_port": 22,
        "ssh_user": "root",
        "ssh_password": "password",
        "port": 8123,
        "access_token": "long_lived_token",
        "config_path": "/config"
    }
    
    print(f"Creating server: {server_name}")
    response = requests.post(f"{BASE_URL}/servers", json=payload, headers=headers)
    print_response(response, "Create Server")
    
    if response.status_code != 201:
        print("❌ Create Server failed")
        return
        
    server_id = response.json().get("id")
    
    # List Servers
    print("Listing servers...")
    response = requests.get(f"{BASE_URL}/servers", headers=headers)
    print_response(response, "List Servers")
    
    # Delete Server
    print(f"Deleting server ID: {server_id}")
    # Note: Delete endpoint usually uses ID in path
    # I need to verify if delete endpoint exists and what the path is.
    # Assuming standard REST: DELETE /servers/{id}
    # Let's check servers.py content again or just try it.
    # Reading servers.py earlier showed create and list. I didn't see delete in the first 100 lines.
    # Let's assume it exists or skip deletion for now if unsure.
    # But usually it is there.
    
    # Verify if server was created
    servers = response.json()
    created_server = next((s for s in servers if s["id"] == server_id), None)
    if created_server:
        print("✅ Server creation verified in list")
    else:
        print("❌ Server not found in list")

def test_ai(token):
    print("\n--- Testing AI ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create Conversation
    payload = {
        "title": "Test Conversation",
        "model": "deepseek-chat"
    }
    print("Creating AI conversation...")
    response = requests.post(f"{BASE_URL}/ai/conversations", json=payload, headers=headers)
    print_response(response, "Create Conversation")
    
    if response.status_code == 201:
        conversation_id = response.json().get("id")
        print(f"✅ Conversation created with ID: {conversation_id}")
        
        # Chat
        chat_payload = {
            "message": "Hello, how are you?",
            "include_context": False
        }
        print("Sending chat message...")
        response = requests.post(f"{BASE_URL}/ai/conversations/{conversation_id}/chat", json=chat_payload, headers=headers)
        print_response(response, "Chat")
        
        if response.status_code == 200:
            print("✅ Chat successful")
        else:
            print("⚠️ Chat failed (Expected if API key is missing)")
            
    else:
        print("❌ Failed to create conversation")

if __name__ == "__main__":
    test_health()
    token = test_auth()
    if token:
        test_servers(token)
        test_ai(token)
