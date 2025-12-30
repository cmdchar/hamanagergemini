import requests
import sys

BASE_URL = "http://localhost:8081/api/v1"

def create_user():
    username = "admin"
    email = "admin@example.com"
    password = "Password123!"
    full_name = "Admin User"

    print(f"Creating user: {username}")
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "full_name": full_name
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        
        if response.status_code == 201:
            print("✅ User created successfully!")
            print(f"Username: {username}")
            print(f"Email: {email}")
            print(f"Password: {password}")
        elif response.status_code == 400 and "already exists" in response.text:
             print("⚠️ User already exists.")
             print(f"Username: {username}")
             print(f"Password: {password} (if you haven't changed it)")
        else:
            print(f"❌ Failed to create user. Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    create_user()
