# Home Assistant Server Configuration - Complete Guide

## HA Server Form Fields (Add & Edit)

Acum formularul de server suportă autentificare completă pentru Home Assistant.

### Secțiunea "Home Assistant Authentication"

Când adaugi sau edități un server, vei vedea câmpurile de autentificare HA:

#### **Access Token** (optional)
- Long-Lived Access Token din Home Assistant
- Generat din HA Settings > Developer Tools
- Format: `eyJhbGciOiJIUzI1NiIsInR5cCI...`
- Criptat în baza de date
- Folosit pentru: API calls cu Bearer authorization

#### **HA Username** (optional) - NEW! ✨
- Username pentru autentificare Home Assistant
- Exemplu: `niku` (user-ul tău)
- Criptat în baza de date
- Folosit pentru: Basic auth + API calls

#### **HA Password** (optional) - NEW! ✨
- Parola Home Assistant
- Exemplu: `NiKu987410`
- **IMPORTANT**: Criptată în baza de date cu AES encryption
- Folosit pentru: Basic authentication
- NON reversible - stockată sigur

---

## Configurație HA cu Credențiale

### Exemplu - Server cu Username + Password

```json
{
  "name": "Home Assistant Principal",
  "host": "192.168.1.116",
  "port": 8123,
  "use_ssl": false,
  "ha_username": "niku",
  "ha_password": "NiKu987410",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI...",
  "ssh_user": "homeassistant",
  "ssh_port": 22,
  "config_path": "/config",
  "server_type": "production"
}
```

### Exemplu - Server cu Access Token (Modern)

```json
{
  "name": "Home Assistant Modern",
  "host": "ha.example.com",
  "port": 8123,
  "use_ssl": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI...",
  "ssh_user": "homeassistant",
  "config_path": "/config",
  "server_type": "production"
}
```

---

## Fluxul de Autentificare HA Config Manager

### 1. LOGIN → HA Config Manager
```
User: admin
Password: password
↓
JWT Token obținut
```

### 2. ADD SERVER cu HA Credentials
```
POST /api/v1/servers
{
  "ha_username": "niku",
  "ha_password": "NiKu987410",
  ...
}
↓
Password criptat în DB (AES)
```

### 3. RETRIEVE SERVER (GET)
```
GET /api/v1/servers/123
↓
{
  "id": 123,
  "name": "...",
  "ha_username": "niku",
  "ha_password": "...(encrypted in DB, not returned)",
  ...
}
```

### 4. HA CONFIG MANAGER → HOME ASSISTANT
```
Authorization: Basic base64(niku:NiKu987410)
↓
Home Assistant API
```

---

## Security Considerations ⚠️

### Encryption
- **HA Password**: Criptat cu AES-256 în baza de date
- **Access Token**: Criptat cu AES-256 în baza de date
- **SSH Password**: Criptat cu AES-256 în baza de date
- **SSH Key Passphrase**: Criptat cu AES-256 în baza de date

### Storage
- Nu sunt salvate în plain text niciunde
- Clonele de lucru au encryption key în environment
- Production: Use environment variable `ENCRYPTION_KEY`

### API Response
- HA password nu e returnat în API responses (security)
- Access token nu e returnat în API responses (security)
- Doar username-ul e vizibil în responses

---

## Database Storage

```sql
-- Tabelul servers cu HA credentials
servers (
  id: INTEGER PRIMARY KEY
  name: VARCHAR(255)
  ha_username: VARCHAR(255)  -- Plain text
  ha_password: VARCHAR(500)  -- AES Encrypted (Base64 encoded)
  access_token: VARCHAR(500) -- AES Encrypted (Base64 encoded)
  ...
)
```

### Exemplu DB:
```
id | name           | ha_username | ha_password (encrypted)
---|----------------|-------------|------------------------
1  | HA Main        | admin       | Z0FBQUFBQnB...==
2  | HA Test        | niku        | Z0FBQUFBQnp...==
```

---

## API Endpoints

### Create Server
```
POST /api/v1/servers
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Home Assistant",
  "host": "192.168.1.116",
  "ha_username": "niku",
  "ha_password": "NiKu987410",
  ...
}

Response (201):
{
  "id": 3,
  "name": "Home Assistant",
  "ha_username": "niku",
  "ha_password": "nicu"  // Not returned
  ...
}
```

### Update Server
```
PUT /api/v1/servers/3
Content-Type: application/json
Authorization: Bearer {token}

{
  "ha_username": "niku_new",
  "ha_password": "NewPassword123"
}

Response (200):
{
  "id": 3,
  "ha_username": "niku_new",
  ...
}
```

### Get Server
```
GET /api/v1/servers/3
Authorization: Bearer {token}

Response (200):
{
  "id": 3,
  "name": "Home Assistant",
  "ha_username": "niku",
  // ha_password not included
  ...
}
```

---

## Authentication Methods

### Method 1: Long-Lived Access Token (Recommended)
- Generat din HA Settings
- Non-expiring
- Secure HTTP Bearer
- **Use**: `access_token` field

### Method 2: Username + Password (Legacy)
- Clasic Basic Authentication
- **Use**: `ha_username` + `ha_password` fields
- Criptat în DB

### Method 3: Kombinat (Best)
- Access Token pentru API calls
- Username + Password pentru fallback
- Ambele criptate în DB

---

## Troubleshooting

### ❌ "Failed to authenticate to Home Assistant"
1. Verifică ha_username și ha_password
2. Testează accesul SSH cu acel user
3. Verify Home Assistant nu are failban de IP

### ❌ "Invalid credentials"
1. Parola greșită
2. User nu există în Home Assistant
3. Access Token expirat (generează altul)

### ❌ "Permission denied"
1. User-ul nu are permisiuni de admin
2. Trebuie să setezi role-ul în HA

---

## Test Credentials

Pentru testing, poți folosi:
```
HA Username: niku
HA Password: NiKu987410
Host: 192.168.1.116
Port: 8123
```

⚠️ **IMPORTANT**: In production, schimbă aceste credențiale!

---

## Frontend Form (React/Next.js)

Formularul AR TREBUI să aibă câmpuri pentru:

```jsx
<form>
  {/* HA Authentication Section */}
  <h3>Home Assistant Authentication</h3>
  
  <input
    type="text"
    name="ha_username"
    label="HA Username"
    placeholder="ex: niku"
  />
  
  <input
    type="password"
    name="ha_password"
    label="HA Password"
    placeholder="ex: NiKu987410"
  />
  
  <input
    type="text"
    name="access_token"
    label="Access Token (optional)"
    placeholder="Long-lived access token"
  />
  
  {/* SSH Section */}
  {/* ... rest of form ... */}
</form>
```

---

## Status Quo

✅ Backend API: Complete
- [x] Model: ha_username, ha_password fields
- [x] Schema: All CRUD operations
- [x] Encryption: AES-256 (DB storage)
- [x] Endpoints: POST, PUT, GET
- [x] Database: Migrated with both columns

🔄 Frontend: TODO
- [ ] Add form fields for ha_username
- [ ] Add form field for ha_password
- [ ] Display in server details
- [ ] Edit capability
- [ ] Password strength indicator

---

## Next Steps

1. **Frontend**: Add ha_username + ha_password fields to server forms
2. **Testing**: Create test suite for HA authentication
3. **Docs**: Update user documentation
4. **Production**: Set proper ENCRYPTION_KEY in environment
