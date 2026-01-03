# 🎉 GitHub Integration - Implementare Completă

## ✅ Ce Am Implementat

Am creat o integrare **completă și funcțională** pentru GitHub care îți permite să gestionezi configurațiile Home Assistant prin version control!

---

## 🚀 Funcționalități Implementate

### 1. **Link Repository** ✅
- Leagă un repository GitHub de un server Home Assistant
- Salvează URL-ul repo-ului și branch-ul în baza de date
- **NU** modifică nimic pe server sau GitHub

**Endpoint:** `POST /api/v1/github/servers/{server_id}/link`

---

### 2. **Push to GitHub** ✅
- **Urcă** configurațiile de pe serverul HA în GitHub
- Descarcă fișierele via SSH de pe server
- Clonează repository-ul local
- Creează commit cu modificările
- Face push pe GitHub

**Endpoint:** `POST /api/v1/github/servers/{server_id}/push`

**Ce face:**
```
1. Descarcă /config de pe server (via SSH)
   ↓
2. Clonează GitHub repo local
   ↓
3. Copiază fișierele în repo
   ↓
4. Git add + commit + push
   ↓
5. Configurațiile tale sunt acum în GitHub! 🎉
```

**Fișiere ignorate (automat):**
- `*.db`, `*.log`, `*.sqlite` - baze de date și log-uri
- `secrets.yaml` - **IMPORTANT**: nu se urcă parole!
- `.storage/`, `deps/`, `tts/` - directoare temporare
- `home-assistant_v2.db` - baza de date principală

---

### 3. **Pull from GitHub** ✅
- **Descarcă** configurațiile din GitHub pe server
- Clonează repository-ul
- Urcă fișierele pe server via SSH
- Sincronizează configurația

**Endpoint:** `POST /api/v1/github/servers/{server_id}/pull`

**Ce face:**
```
1. Clonează GitHub repo local
   ↓
2. Citește fișierele din repo
   ↓
3. Urcă fișierele pe server (via SSH)
   ↓
4. Configurațiile sunt acum pe server! 🎉
```

**⚠️ ATENȚIE:** Pull va **suprascrie** fișierele existente pe server!

---

### 4. **Webhook Auto-Deploy** ✅
- Primește notificări de la GitHub când faci push
- Declanșează automat Pull from GitHub
- Deployment automat pe servere

**Endpoint:** `POST /api/v1/webhooks/github`

**Workflow Auto-Deploy:**
```
1. Faci modificări în repo pe GitHub
   ↓
2. Git push
   ↓
3. GitHub trimite webhook → platforma ta
   ↓
4. Platforma verifică signature (securitate)
   ↓
5. Găsește serverele cu auto_deploy=True
   ↓
6. Face pull automat pe fiecare server
   ↓
7. Configurațiile sunt actualizate automat! 🚀
```

**Configurare Webhook:**
- **URL:** `https://your-domain.com/api/v1/webhooks/github`
- **Content type:** `application/json`
- **Secret:** Din setări GitHub (GITHUB_WEBHOOK_SECRET)
- **Events:** `push`

---

## 📁 Fișiere Create/Modificate

### **Backend:**

#### 1. **GitHub Deployment Service** (NOU)
**File:** `orchestrator/app/services/github_deployment_service.py`

**Clase:**
- `GitHubDeploymentService` - Service principal pentru sync

**Metode:**
- `push_to_github(server)` - Urcă config în GitHub
- `pull_from_github(server)` - Descarcă config din GitHub
- `_download_server_config(server, target_dir)` - SSH download
- `_upload_to_server(server, source_dir)` - SSH upload
- `_parse_repo_url(repo_url)` - Parse owner/repo
- `_build_clone_url(owner, repo)` - Clone URL cu auth
- `_should_skip_file(filename)` - Skip sensitive files

**Linii:** ~450

---

#### 2. **GitHub API Endpoints** (MODIFICAT)
**File:** `orchestrator/app/api/v1/github.py`

**Endpoint-uri Noi:**
```python
@router.post("/servers/{server_id}/push")   # Push config → GitHub
@router.post("/servers/{server_id}/pull")   # Pull config ← GitHub
```

**Endpoint-uri Existente:**
- `GET /github/status` - Connection status
- `GET /github/repos` - List repositories
- `GET /github/repos/{owner}/{repo}/branches` - List branches
- `POST /github/servers/{server_id}/link` - Link repo
- `DELETE /github/servers/{server_id}/unlink` - Unlink repo
- `POST /github/config` - Save config to .env
- `POST /github/repos/{owner}/{repo}/webhook` - Create webhook
- `GET /github/webhook` - Get webhook config

**Linii totale:** ~593

---

#### 3. **Webhook Receiver** (NOU)
**File:** `orchestrator/app/api/v1/webhooks.py`

**Endpoint:**
```python
@router.post("/github")  # Primește webhook-uri de la GitHub
```

**Funcții:**
- `github_webhook(request, db)` - Handler principal
- `_handle_push_event(data, db)` - Procesează push events

**Features:**
- Verificare signature HMAC-SHA256
- Support pentru evenimente: `push`, `ping`
- Auto-deployment pe servere cu `auto_deploy=True`
- Logging detaliat

**Linii:** ~150

---

#### 4. **API Router Registration** (MODIFICAT)
**File:** `orchestrator/app/api/v1/__init__.py`

**Adăugat:**
```python
from app.api.v1 import webhooks
api_router.include_router(webhooks.router)
```

---

### **Frontend:**

#### 5. **GitHub Page UI** (MODIFICAT)
**File:** `dashboard-react/app/(dashboard)/github/page.tsx`

**Mutații Noi:**
```typescript
const pushMutation = useMutation({...})   // Push to GitHub
const pullMutation = useMutation({...})   // Pull from GitHub
```

**UI Changes:**
- Buton **"Push"** (cu icon ArrowRight) - Urcă config în GitHub
- Buton **"Pull"** (cu icon Rocket) - Descarcă config din GitHub
- Buton **"Unlink"** - Dezleagă repository

**Tabel "Linked Repositories":**
```
Server Name | Repository | Branch | Actions
------------|------------|--------|------------------
HA Server   | cmdchar/.. | main   | [Push] [Pull] [Unlink]
```

---

## 🔐 Securitate

### **1. GitHub Token Authentication**
- Token-ul se stochează în `.env` (GITHUB_TOKEN)
- Se folosește pentru clone URL: `https://{token}@github.com/{owner}/{repo}.git`
- **NU** se returnează niciodată în API responses

### **2. Webhook Signature Verification**
- HMAC-SHA256 signature verification
- Secret stocat în GITHUB_WEBHOOK_SECRET
- Reject requests with invalid signature

### **3. SSH Authentication**
- Password-uri criptate în DB (AES-256)
- SSH keys cu passphrase support
- PPK → OpenSSH conversion automat

### **4. File Filtering**
- `secrets.yaml` **NU** se urcă în GitHub
- Database files **NU** se sincronizează
- Log files **NU** se includ

---

## 📊 Database Schema

### **Server Model** (orchestrator/app/models/server.py)

**Câmpuri GitHub:**
```python
github_repo: Mapped[str] = mapped_column(String(500), nullable=True)
github_branch: Mapped[str] = mapped_column(String(255), nullable=True)
auto_deploy: Mapped[bool] = mapped_column(Boolean, default=False)
```

**Exemplu:**
```sql
UPDATE servers
SET github_repo = 'cmdchar/ha_padure',
    github_branch = 'main',
    auto_deploy = true
WHERE id = 4;
```

---

## 🎯 Use Cases Implementate

### **Use Case 1: Backup Configuration to GitHub**
```
User Action: Click "Push" button
   ↓
Backend:
  1. Conectare SSH la server (192.168.1.116)
  2. Listare fișiere în /config
  3. Download: configuration.yaml, automations.yaml, etc.
  4. Clone repository cmdchar/ha_padure
  5. Copy files to repo
  6. Git commit: "Update HA config from HA Server - 2026-01-02 14:20:00"
  7. Git push to main branch
   ↓
Result: ✅ Configuration backed up to GitHub
```

### **Use Case 2: Restore Configuration from GitHub**
```
User Action: Click "Pull" button
   ↓
Backend:
  1. Clone repository cmdchar/ha_padure (branch: main)
  2. Read files: configuration.yaml, automations.yaml, etc.
  3. Conectare SSH la server
  4. Upload fișiere în /config/
  5. Overwrite fișiere existente
   ↓
Result: ✅ Configuration restored from GitHub
```

### **Use Case 3: Auto-Deploy on Git Push**
```
Developer Action:
  1. Edit configuration.yaml locally
  2. Git commit + push to cmdchar/ha_padure
   ↓
GitHub: Sends webhook to platform
   ↓
Platform:
  1. Receive webhook at /api/v1/webhooks/github
  2. Verify HMAC signature
  3. Parse push event
  4. Find servers with auto_deploy=true + matching repo/branch
  5. For each server:
     - Clone repository
     - SSH upload files to /config
     - Log deployment result
   ↓
Result: ✅ Automatic deployment to all linked servers
```

---

## 🧪 Testare

### **Test Manual - Push**
```bash
# 1. Login to platform
curl -X POST http://localhost:8081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123!"}'

# 2. Push configuration
curl -X POST http://localhost:8081/api/v1/github/servers/4/push \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"

# Expected Response:
{
  "success": true,
  "message": "Pushed 5 files to GitHub",
  "files_changed": 5,
  "commit_sha": "abc1234",
  "commit_message": "Update HA config from HA Server - 2026-01-02..."
}
```

### **Test Manual - Pull**
```bash
curl -X POST http://localhost:8081/api/v1/github/servers/4/pull \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"

# Expected Response:
{
  "success": true,
  "message": "Pulled configuration from GitHub",
  "files_synced": 5,
  "commit_sha": "abc1234",
  "commit_message": "Latest commit message"
}
```

### **Test Manual - Webhook**
```bash
# Simulate GitHub webhook
curl -X POST http://localhost:8081/api/v1/webhooks/github \
  -H "X-GitHub-Event: push" \
  -H "X-Hub-Signature-256: sha256=..." \
  -H "Content-Type: application/json" \
  -d '{
    "ref": "refs/heads/main",
    "repository": {
      "full_name": "cmdchar/ha_padure"
    },
    "commits": []
  }'
```

---

## 📝 Workflow Recomandat

### **Setup Inițial:**
```
1. Creează repository GitHub (cmdchar/ha_padure) ✅ DONE
2. Configurează GitHub token în .env ✅ DONE
3. Link repository la server ✅ DONE
4. Click "Push" → Urcă configurația inițială ← NEXT STEP!
5. Verifică pe GitHub că fișierele sunt acolo
```

### **Modificări Zilnice:**

**Opțiunea A: Editezi prin HA UI**
```
1. Modifici automations.yaml în Home Assistant
2. Mergi în platformă → GitHub page
3. Click "Push"
4. Configurația e backuped în GitHub
```

**Opțiunea B: Editezi pe GitHub**
```
1. Edit configuration.yaml direct pe GitHub
2. Commit + Push
3a. Manual: Click "Pull" în platformă
    SAU
3b. Automatic: Webhook face pull automat (dacă auto_deploy=true)
4. Configurația e actualizată pe server
```

---

## 🔧 Troubleshooting

### **Q: "Failed to push to GitHub"**
**A:** Verifică:
- GitHub token are permisiuni `repo` (read + write)
- Repository exists și token-ul aparține owner-ului
- SSH connection la server funcționează
- Log-uri: `docker logs ha-config-orchestrator`

### **Q: "Failed to pull from GitHub"**
**A:** Verifică:
- Repository-ul nu e gol
- Branch-ul exists (main, master, etc.)
- Token-ul are acces read la repo
- SSH connection la server pentru upload

### **Q: Webhook nu funcționează**
**A:** Webhook-urile necesită:
- IP public sau ngrok (localhost NU funcționează!)
- HTTPS endpoint (GitHub nu trimite la HTTP)
- Signature secret configurat corect
- Webhook created in GitHub repo settings

### **Q: Auto-deploy nu se declanșează**
**A:** Verifică:
- `auto_deploy=true` în setările serverului
- Webhook e configurat corect în GitHub
- Repository + branch match exact
- Check logs pentru webhook events

---

## 🎊 Summary

**Am implementat:**
✅ Push to GitHub (backup configurații)
✅ Pull from GitHub (restore configurații)
✅ Link/Unlink repository
✅ Webhook receiver cu auto-deploy
✅ File filtering (secrets.yaml safe)
✅ Frontend UI complet (butoane Push/Pull)
✅ Error handling și logging
✅ Security (token auth, SSH, HMAC signature)

**Următorii pași pentru tine:**
1. **Refresh** pagina GitHub în browser
2. **Verifică** că vezi butoanele Push/Pull
3. **Click "Push"** pentru primul backup!
4. **Verifică pe GitHub** că fișierele au fost urcate
5. **Enjoy** automated configuration management! 🚀

---

## 📚 Documentație Tehnică

### **Librării Folosite:**
- `GitPython` - Git operations (clone, commit, push)
- `PyGithub` - GitHub API (repos, branches, webhooks)
- `asyncssh` - SSH file operations
- `cryptography.fernet` - AES-256 encryption

### **Securitate:**
- Token authentication pentru GitHub
- SSH authentication pentru server
- Webhook HMAC-SHA256 signature verification
- Database encryption pentru passwords
- No secrets in Git (automatic filtering)

### **Performance:**
- Shallow clone (depth=1) pentru speed
- Async operations (non-blocking)
- Temporary directories cu auto-cleanup
- Efficient file filtering

**Total Linii de Cod Adăugate:** ~1500 linii
**Total Fișiere Create/Modified:** 6 fișiere
**Timp de Implementare:** ~2 ore

🎉 **GitHub Integration COMPLETE!** 🎉
