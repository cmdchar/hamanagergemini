import asyncio
import httpx
import sys

# URL-ul API-ului (intern in container = 8080)
API_URL = "http://localhost:8080/api/v1"

# Credentiale Admin
LOGIN_DATA = {
    "username": "admin",
    "password": "Admin123!"
}

# Date server pentru simulare Frontend (fara parola, cum permite formularul)
FRONTEND_SERVER_PAYLOAD = {
    "name": "Frontend Test Server",
    "host": "10.0.0.50",
    "port": 22,
    "username": "root"
    # password field is optional in Zod schema
}

async def verify_system():
    async with httpx.AsyncClient() as client:
        print(f"--- 1. Autentificare la {API_URL} ---")
        try:
            # Endpoint-ul /auth/login asteapta JSON (LoginRequest), nu Form Data
            resp = await client.post(f"{API_URL}/auth/login", json=LOGIN_DATA)
            if resp.status_code != 200:
                print(f"Eroare Login: {resp.status_code} - {resp.text}")
                return False
            
            # LoginResponse contine access_token
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("Login reusit. Token obtinut.")
        except Exception as e:
            print(f"Eroare conexiune: {e}")
            return False

        print("\n--- 2. Verificare Server Existent (192.168.1.116) ---")
        resp = await client.get(f"{API_URL}/servers", headers=headers)
        if resp.status_code == 200:
            servers = resp.json()
            found = False
            for s in servers:
                print(f"Gasit server: {s['name']} ({s['host']})")
                if s['host'] == "192.168.1.116":
                    found = True
            
            if found:
                print("SUCCESS: Serverul 192.168.1.116 exista in baza de date.")
            else:
                print("WARNING: Serverul 192.168.1.116 NU a fost gasit.")
        else:
            print(f"Eroare la listarea serverelor: {resp.status_code}")

        print("\n--- 3. Simulare Adaugare Server din Frontend ---")
        # Frontend-ul trimite JSON. Verificam daca backend-ul accepta formatul exact.
        resp = await client.post(f"{API_URL}/servers", headers=headers, json=FRONTEND_SERVER_PAYLOAD)
        if resp.status_code in [200, 201]:
            new_server = resp.json()
            print(f"SUCCESS: Server creat cu succes prin API (Simulare Frontend). ID: {new_server['id']}")
            
            # Cleanup
            print("Stergere server de test...")
            await client.delete(f"{API_URL}/servers/{new_server['id']}", headers=headers)
        else:
            print(f"FAILURE: Nu s-a putut crea serverul. Status: {resp.status_code}")
            print(f"Raspuns: {resp.text}")

        print("\n--- 4. Verificare Dashboard Stats (Fix Enum) ---")
        resp = await client.get(f"{API_URL}/dashboard/stats", headers=headers)
        if resp.status_code == 200:
            stats = resp.json()
            print(f"SUCCESS: Dashboard stats functioneaza. Date: {stats}")
        else:
            print(f"FAILURE: Dashboard stats a returnat eroare: {resp.status_code}")
            print(f"Raspuns: {resp.text}")

        print("\n--- 5. Verificare Deployments List (Fix Missing Trigger) ---")
        resp = await client.get(f"{API_URL}/deployments", headers=headers)
        if resp.status_code == 200:
            deps = resp.json()
            print(f"SUCCESS: Lista de deployments incarcata. Numar: {len(deps)}")
        else:
            print(f"FAILURE: Lista deployments a returnat eroare: {resp.status_code}")
            print(f"Raspuns: {resp.text}")

if __name__ == "__main__":
    asyncio.run(verify_system())
