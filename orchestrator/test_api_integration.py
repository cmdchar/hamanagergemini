import requests
import sys
import json

BASE_URL = "http://localhost:8081/api/v1"

def test_integration():
    # 1. Login
    login_data = {
        "username": "admin",
        "password": "Admin123!"
    }
    
    print("Logging in...")
    try:
        # Try form-data first (standard OAuth2)
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        if response.status_code != 200:
             # Try JSON as fallback
             response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"Login failed: {response.status_code} {response.text}")
            return

        token = response.json()["access_token"]
        print("Login successful.")
        
        headers = {
            "Authorization": f"Bearer {token}"
        }

        # 2. Test Server 1
        print("Testing Server 1 connection (SSH + HA)...")
        response = requests.post(f"{BASE_URL}/servers/1/test", headers=headers)
        
        if response.status_code == 200:
            print("Test request successful.")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Test request failed: {response.status_code} {response.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_integration()
