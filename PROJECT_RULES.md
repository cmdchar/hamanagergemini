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
- [x] HA Credentials (username + password) - NEW!
- [ ] Import Configurații Automate (Urmează)

---

## 6. Feature: HA Credentials (Home Assistant Authentication)

### Descriere
Permite salvarea și criptarea credențialelor Home Assistant (username + password) pentru fiecare server configurat.

### Backend Changes
**File:** `orchestrator/app/models/server.py`
- Adăugat `ha_username: VARCHAR(255)` - username HA
- Adăugat `ha_password: VARCHAR(500)` - password criptat cu AES-256

**File:** `orchestrator/app/schemas/server.py`
- Actualizat `ServerCreate` - include ha_username, ha_password
- Actualizat `ServerUpdate` - include ha_username, ha_password
- Actualizat `ServerResponse` - include ha_username (password nu se returnează)

**File:** `orchestrator/app/api/v1/servers.py`
- Linia ~119: Adăugat criptare `ha_password` în create endpoint
- Linia ~473: Adăugat update logic pentru ha_username + ha_password
- Linia ~40: Adăugat mapping ha_username în `create_server_response()`

### Database
```sql
-- Migration manual (dacă nu auto-create din models)
ALTER TABLE servers ADD COLUMN ha_username VARCHAR(255) NULL;
ALTER TABLE servers ADD COLUMN ha_password VARCHAR(500) NULL;
```

**Exemplu DB:**
```
id | name | ha_username | ha_password (encrypted)
----|------|------------|------------------------
3  | HA Server | niku | Z0FBQUFBQnp...==
```

### Frontend Changes
**File:** `dashboard-react/components/forms/server-form.tsx`
- Actualizat `serverSchema` - adăugat ha_username, ha_password validation
- Actualizat `defaultValues` - initialize new fields
- Actualizat `useEffect` form reset - include new fields
- Adăugat 2 noi FormField componente după access_token:
  - Input text: "Home Assistant Username (optional)"
  - Input password: "Home Assistant Password (optional)"

**File:** `dashboard-react/app/(dashboard)/servers/[id]/page.tsx`
- Actualizat `Server` interface - adăugat `ha_username?: string`
- Adăugat display în "Server Information" card - arată ha_username cu conditional rendering

### API Endpoints

#### Create Server
```
POST /api/v1/servers
{
  "name": "My HA",
  "host": "192.168.1.116",
  "ha_username": "niku",
  "ha_password": "NiKu987410",
  "access_token": "...",
  ...
}
```

#### Update Server
```
PUT /api/v1/servers/{id}
{
  "ha_username": "niku",
  "ha_password": "NewPassword"
}
```

#### Get Server
```
GET /api/v1/servers/{id}
Response: { ha_username: "niku", ... }
Note: ha_password is NOT returned (security)
```

### Security
- **Encryption:** AES-256 (Fernet) în baza de date
- **Rotation:** Encrypt/decrypt automatic cu ENCRYPTION_KEY din .env
- **API Response:** Password nu se returnează niciodată
- **Storage:** Criptat în DB ca VARCHAR(500)

### Testare
1. Add server cu ha_username: `niku`, ha_password: `NiKu987410`
2. Verifica în DB:
   ```bash
   docker exec ha-config-postgres psql -U haconfig -d haconfig \
     -c "SELECT id, name, ha_username FROM servers;"
   ```
3. Verifica criptare:
   ```bash
   docker exec ha-config-postgres psql -U haconfig -d haconfig \
     -c "SELECT ha_password FROM servers WHERE id=3;"
   # Output: Z0FBQUFBQnp...==  (criptat)
   ```

### Documentare Conexă
- `HA_CREDENTIALS_GUIDE.md` - User documentation completă
- `HA_SERVER_SETUP_GUIDE.md` - SSH user selection guide
- `IMPLEMENTATION_DOCUMENTATION.md` - API overview (secțiunea Servers)

---

## 7. Data Flow: HA Credentials

### Create/Update Server Flow
```
Frontend Form (React)
  ↓
  User fills: ha_username="niku", ha_password="NiKu987410"
  ↓
serverSchema validation (zod)
  ↓
POST/PUT to /api/v1/servers
  ↓
Backend Handler (FastAPI)
  ↓
encrypt_value(ha_password) → AES-256 encryption
  ↓
Server model saves to DB
  ├─ ha_username: "niku" (plain text)
  └─ ha_password: "Z0FBQUFBQnp...==" (encrypted)
  ↓
Response: ServerResponse
  ├─ ha_username: "niku"
  └─ ha_password: None (not returned for security)
```

### Retrieve Server Flow
```
Frontend calls GET /api/v1/servers/{id}
  ↓
Backend fetches from DB
  ├─ ha_username: "niku"
  └─ ha_password: "Z0FBQUFBQnp...==" (encrypted, not decrypted for response)
  ↓
create_server_response() maps fields
  ├─ Maps ha_username → response
  └─ Does NOT map ha_password to response
  ↓
Frontend receives:
  ├─ ha_username: "niku" (displayed)
  └─ ha_password: undefined (not shown)
```

---

## 8. Future Enhancements

### Planned
- [ ] Use ha_password + ha_username for API authentication to HA
- [ ] Add password strength indicator in UI
- [ ] Implement password rotation feature
- [ ] Add HA API auth method detection (token vs basic auth)
- [ ] Create "Test HA Credentials" endpoint

### Related Features to Implement
- GitHub OAuth token storage (same encryption pattern)
- SSH key passphrase encryption (already done)
- SSL certificate management

---

## 9. Troubleshooting - HA Credentials

### Q: Password shows as `null` in database
**A:** Password might not have been provided in form. Check if ha_password field was filled.

### Q: "Invalid credentials" error from HA
**A:** Check that:
1. ha_username exists as user in Home Assistant
2. ha_password is correct
3. User has admin/sufficient permissions

### Q: Want to change only username, not password
**A:** In PUT request, omit ha_password field. Backend will NOT update it if field is null.

### Q: Can't decrypt password - "cipher error"
**A:** Likely ENCRYPTION_KEY mismatch between environments. Check:
```bash
docker exec ha-config-orchestrator env | grep ENCRYPTION_KEY
```
Must match production/staging key.

### Q: Where is encryption key stored?
**A:** `docker-compose.yml` under orchestrator `environment:` section or `.env` file.
- Development: `KQeZwERanQ4SsHZzwlcjQ53SS19FaKw2rmMiPZZDqQ8=`
- Production: Must be set in CI/CD secrets
Github connection 

### Q: GitHub oauth
- client id - [Set in CI/CD secrets]
- client secret - [Set in CI/CD secrets]
- token clasic - [Set in CI/CD secrets]
---
