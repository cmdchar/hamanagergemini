# Jurnal Modificări și Reguli Proiect (Project Rules)

Acest document servește ca "Master Document" pentru starea curentă a proiectului **HA Config Manager**. Include structura proiectului, funcționalitățile implementate, modificările tehnice și ghidul de utilizare.

## 1. Prezentare Generală & Stare
- **Nume Proiect:** HA Config Manager
- **Scop:** Gestionarea centralizată a configurațiilor Home Assistant, orchestrarea deployment-urilor și monitorizarea serverelor.
- **Branch Curent:** `claude/audit-dependencies-mjojfvfv822s1uud-5SOax`
- **Stare Dezvoltare:** Funcțional (Alpha). Backend-ul și Frontend-ul comunică corect. Funcționalitățile critice (SSH, Terminal, Server Management) sunt active.

## 2. Arhitectură și Structură

### A. Infrastructură (Docker)
- **Container Orchestrator:** Backend Python/FastAPI (`port: 8081` mapat pe host).
- **Container Dashboard:** Frontend Next.js (`port: 3000`).
- **Container Postgres:** Bază de date (`port: 5432`).
- **Docker Compose:** `docker-compose.yml` gestionează rețeaua `ha-config-network` și volumele persistente.

### B. Backend (`/orchestrator`)
Tech Stack: **FastAPI, SQLAlchemy (Async), Pydantic, AsyncSSH, Argon2**.

**Structură Cheie:**
- `app/api/v1/`: Endpoint-uri API (Routere).
  - `auth.py`: Autentificare (JWT).
  - `servers.py`: CRUD servere, test conexiune SSH.
  - `terminal.py`: WebSocket pentru terminal web.
  - `deployments.py`: Gestionare deployment-uri.
  - `dashboard.py`: Statistici sumare.
- `app/core/`: Logică de business centrală.
  - `security.py`: Hashing parole (Argon2).
- `app/models/`: Modele SQLAlchemy (tabele DB).
- `setup_env.py`: Script de inițializare automată (Admin + Server Default).

### C. Frontend (`/dashboard-react`)
Tech Stack: **Next.js 14 (App Router), React Query, Tailwind CSS, Shadcn UI, Zustand, XTerm.js**.

**Structură Cheie:**
- `app/(dashboard)/`: Pagini protejate de autentificare.
  - `servers/`: Lista servere, adăugare/editare, link Node-RED.
  - `terminal/`: Consolă SSH web-based.
  - `deployments/`: Istoric și status deployment-uri.
- `components/`: Componente reutilizabile.
  - `terminal/web-terminal.tsx`: Implementare XTerm.js + WebSocket.
- `lib/api.ts`: Client Axios configurat cu interceptori pentru Auth.

## 3. Funcționalități Implementate și Testate

### ✅ 1. Autentificare & Securitate
- **Login/Register:** Funcțional.
- **Hashing:** Migrat de la `bcrypt` la `argon2` pentru a suporta parole lungi (>72 caractere).
- **CORS:** Configurat pentru a permite request-uri de pe `localhost:3000`.

### ✅ 2. Management Servere (SSH)
- **Adăugare/Editare/Ștergere:** Funcțional.
- **Test Conexiune:** Buton dedicat care verifică conectivitatea SSH în timp real.
- **Suport Chei SSH:** Backend-ul acceptă căi către chei private (convertite în format PEM/OpenSSH).
- **Link Node-RED:** Acces rapid la instanța Node-RED a serverului (`http://IP:1880`).

### ✅ 3. Web Terminal
- **Acces:** Meniu dedicat `/terminal`.
- **Tehnologie:** WebSocket securizat către backend -> tunel SSH `asyncssh` către serverul target.
- **Capabilități:** Shell complet interactiv (suportă `nano`, `htop`, comenzi `ha`).

### ✅ 4. Deployments
- **Listare:** Vizualizare istoric deployment-uri (Schema corectată pentru a include câmpul `trigger`).
- **Status:** Monitorizare succes/eșec.

### ✅ 5. AI Assistant
- **Integrare:** DeepSeek API configurat.
- **Chat:** Interfață disponibilă în dashboard pentru asistență la configurare.

## 4. Jurnal Modificări Tehnice (Change Log)

### Sesiune Curentă (30 Dec 2025)
1.  **Fix Critic CORS/Network:**
    - Actualizat `main.py` și `config.py` pentru whitelist `localhost:3000`.
    - Modificat frontend `api.ts` pentru logging detaliat.
2.  **Fix Login:**
    - Schimbat payload-ul de login din `FormData` în `JSON` în `login/page.tsx`.
3.  **Implementare Terminal:**
    - Creat backend WebSocket endpoint (`terminal.py`).
    - Creat frontend page și componentă XTerm (`web-terminal.tsx`).
4.  **Fix Schema Deployments:**
    - Adăugat câmpurile lipsă (`trigger`, `auto_rollback`) în modelele Pydantic backend.
5.  **Utilitare:**
    - Conversie cheie SSH: `bbb.ppk` -> `bbb_rsa_trad.pem`.
    - Script `setup_env.py` pentru bootstrapping rapid.

## 5. Ghid de Utilizare Rapidă

### Acces
- **URL Dashboard:** [http://localhost:3000](http://localhost:3000)
- **User Admin:** `admin`
- **Parolă:** `Admin123!`

### Comenzi Utile (Terminal Local)
```powershell
# Pornire completă (rebuild forțat)
docker compose down
docker compose up --build -d

# Inițializare date (dacă baza de date e goală)
docker compose exec orchestrator python /app/setup_env.py

# Verificare loguri backend
docker compose logs -f orchestrator
```

### Server Home Assistant (Target)
- **IP:** `192.168.1.116`
- **Utilizator SSH:** `root`
- **Metoda Auth:** Cheie privată (`bbb_rsa_trad.pem` configurată automat de `setup_env.py`).

## 6. Următorii Pași (Roadmap)
- [ ] Implementare "Config Browser" (explorator fișiere remote).
- [ ] Import automat configurații existente din HA.
- [ ] Rafinare interfață AI Assistant.
