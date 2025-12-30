# Reguli Specifice Proiect (HA Config Manager)

## 1. Informații Generale
- **Nume Proiect:** HA Config Manager (Gemini Edition).
- **Repository:** `https://github.com/cmdchar/hamanagergemini.git` (Ramura `main`).
- **Arhitectură:** Microservices (Docker Compose).
  - **Frontend:** Next.js (React) + Tailwind + React Query.
  - **Backend:** FastAPI (Python 3.11) + SQLAlchemy (Async).
  - **Bază de date:** PostgreSQL 16.

## 2. Acces și Credențiale (Development)
- **Frontend URL:** `http://localhost:3000`
- **Backend API:** `http://localhost:8081`
- **Swagger Docs:** `http://localhost:8081/docs`
- **Admin User:** `admin`
- **Admin Pass:** `Admin123!`
- **DB User/Pass:** `haconfig` / `haconfig_secret`

## 3. Server Home Assistant (Remote)
- **IP:** `192.168.1.116`
- **User:** `root`
- **Cheie SSH:** `bbb.ppk` (cu passphrase în `.env`).
- **Conversie:** Backend-ul folosește formatul OpenSSH/PEM (`bbb_rsa_trad.pem`).
- **Capabilități:** Terminal Web, Node-RED (port 1880), File Editor.

## 4. Configurație Tehnică
- **Porturi Externe Docker:**
  - Frontend: `3000`
  - Backend: `8081` (intern `8080`)
  - Postgres: `5432`
- **Deploy:**
  - Pornire: `docker compose up --build`
  - Reset DB: `docker compose down -v`

## 5. Status Funcționalități
- [x] Autentificare & JWT
- [x] CRUD Servere
- [x] Terminal Web (WebSocket)
- [x] Integrare AI (DeepSeek)
- [x] Link Node-RED
- [ ] Import Configurații Automate (Urmează)
