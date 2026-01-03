# 📚 Ghid Complet: GitHub + Home Assistant Config Manager

## 🎯 Obiectiv
Crearea unui repository GitHub pentru stocarea centralizată a configurațiilor Home Assistant, cu sincronizare automată prin platformă.

---

## 📋 Pași de Configurare

### 1. Creează Repository GitHub

1. **Accesează**: https://github.com/new
2. **Configurare Repository:**
   - **Nume**: `ha-configurations` (sau cum preferi)
   - **Descriere**: `Home Assistant configuration files managed by HA Config Manager`
   - **Vizibilitate**: 🔒 **PRIVATE** (important pentru securitate!)
   - **Initialize cu**:
     - ✅ Add README
     - ✅ Add .gitignore (template: Python)
   - **Click**: "Create repository"

3. **Copiază URL-ul**: `https://github.com/cmdchar/ha-configurations.git`

---

### 2. Structură Recomandată Repository

După creare, structura ar trebui să fie:

```
ha-configurations/
├── servers/                    # Configurații per server
│   ├── ha-main/               # Primul server HA
│   │   ├── configuration.yaml
│   │   ├── automations.yaml
│   │   ├── scripts.yaml
│   │   ├── scenes.yaml
│   │   ├── secrets.yaml.example  # Template fără date sensibile
│   │   └── custom_components/
│   │       └── ...
│   ├── ha-secondary/          # Al doilea server (dacă există)
│   │   └── ...
│   └── README.md              # Documentație pentru servere
├── shared/                    # Resurse partajate între servere
│   ├── packages/              # Pachete de configurație reutilizabile
│   │   ├── lighting.yaml
│   │   ├── climate.yaml
│   │   └── security.yaml
│   ├── templates/             # Template-uri Jinja2
│   └── scripts/               # Scripturi comune
├── docs/                      # Documentație
│   ├── automation-guide.md
│   └── integration-list.md
├── .gitignore                 # Fișiere de ignorat
├── README.md                  # Documentație principală
└── LICENSE                    # Licență (optional)
```

---

### 3. Fișierul `.gitignore` Important

Asigură-te că `.gitignore` include:

```gitignore
# Home Assistant sensitive files
secrets.yaml
*.db
*.db-shm
*.db-wal
*.log
*.sqlite
*.pid

# Temporary files
*.pyc
__pycache__/
.HA_VERSION
.uuid
.cloud
.storage/
deps/
tts/
www/
OZW_Log.txt

# OS files
.DS_Store
Thumbs.db
.idea/
.vscode/

# Backup files
*.backup
backups/
```

---

### 4. Configurare în Platform (HA Config Manager)

#### A. Verifică că GitHub Token funcționează:

1. **Login**: http://localhost:3000
2. **Navighează la**: GitHub (din sidebar)
3. **Verifică Status**: Ar trebui să vezi:
   - ✅ Connected
   - Username: `cmdchar` (username-ul tău GitHub)
   - Email: (email-ul tău)

4. **Vezi Repository-uri**: Ar trebui să vezi `ha-configurations` în listă

#### B. Link Repository la Server:

1. **În secțiunea "Link Repository to Server"**:
   - **Select Repository**: Alege `cmdchar/ha-configurations`
   - **Select Branch**: Alege `main`
   - **Select Server**: Alege serverul tău HA (ex: "HA Server - 192.168.1.116")

2. **Click**: "Link Repository" ✨

3. **Confirmare**: Ar trebui să vezi mesaj de success:
   ```
   ✅ Repository linked successfully!
   ```

---

### 5. Sincronizare Configurații

#### Opțiune A: Pull Manual (din GitHub la Server)

```bash
# În platformă, apasă butonul "Pull from GitHub"
# Sau prin API:
POST /api/v1/github/pull/{server_id}
```

Acest lucru va:
1. Clona repository-ul pe server
2. Copia fișierele în `/config` pe serverul HA
3. Face restart la Home Assistant (opțional)

#### Opțiune B: Push Manual (de pe Server la GitHub)

```bash
# În platformă, apasă butonul "Push to GitHub"
# Sau prin API:
POST /api/v1/github/push/{server_id}
```

Acest lucru va:
1. Copia configurația curentă de pe server
2. Face commit în repository
3. Face push pe GitHub

#### Opțiune C: Sincronizare Automată (cu Webhooks)

⚠️ **Necesită domeniu public sau ngrok** (nu funcționează pe localhost)

1. **Setup Webhook** în GitHub:
   - URL: `https://your-domain.com/api/v1/github/webhook`
   - Events: `push`
   - Secret: (generat automat de platformă)

2. **Când faci push pe GitHub**:
   - Webhook notifică platforma
   - Platforma face pull automat
   - HA se restartează cu noua configurație

---

### 6. Workflow Recomandat

#### Scenariul 1: Editezi configurația prin UI HA

1. **Modifici** `automations.yaml` în Home Assistant UI
2. **Mergi în platformă** → GitHub page
3. **Click**: "Push to GitHub"
4. **Verifici pe GitHub**: Vezi commit-ul nou cu modificările

#### Scenariul 2: Editezi configurația pe GitHub

1. **Editezi** fișiere direct pe GitHub (sau local + push)
2. **Mergi în platformă** → GitHub page
3. **Click**: "Pull from GitHub"
4. **HA se restartează** cu noile configurații

#### Scenariul 3: Setup Server Nou

1. **Instalezi** Home Assistant pe server nou
2. **Adaugi serverul** în platformă
3. **Link repository** la serverul nou
4. **Pull from GitHub** → Configurația se copiază automat!

---

### 7. Comenzi Utile (API)

```bash
# Check GitHub status
GET /api/v1/github/status

# List repositories
GET /api/v1/github/repos

# List branches
GET /api/v1/github/repos/{owner}/{repo}/branches

# Link repository to server
POST /api/v1/github/servers/{server_id}/link
{
  "repo_url": "https://github.com/cmdchar/ha-configurations.git",
  "branch": "main"
}

# Pull from GitHub to server
POST /api/v1/github/servers/{server_id}/pull

# Push from server to GitHub
POST /api/v1/github/servers/{server_id}/push
```

---

### 8. Securitate și Best Practices

#### ✅ DO:
- Folosește repository **PRIVATE**
- Adaugă `secrets.yaml` în `.gitignore`
- Creează `secrets.yaml.example` cu placeholder-uri
- Face commit-uri cu mesaje descriptive
- Testează configurația înainte de push
- Creează branch-uri pentru modificări majore

#### ❌ DON'T:
- Nu face commit la `secrets.yaml` (conține parole!)
- Nu face commit la `*.db` (baze de date)
- Nu face commit la `*.log` (log-uri)
- Nu expune token-ul GitHub în cod
- Nu face push direct la `main` fără testare

---

### 9. Troubleshooting

#### Q: "GitHub not connected" error
**A:** Verifică că `GITHUB_TOKEN` este setat corect în `.env` și repornește containerele:
```bash
docker-compose down && docker-compose up -d
```

#### Q: "Failed to clone repository" error
**A:** Verifică:
1. Token-ul are permisiuni `repo`
2. Repository-ul există
3. Token-ul aparține user-ului care deține repo-ul

#### Q: "Permission denied" când face push
**A:** Token-ul trebuie să aibă permisiuni de scriere (`repo` scope complete)

#### Q: Conflicte la pull/push
**A:**
1. Backup manual al configurației curente
2. Rezolvă conflictele manual
3. Creează commit nou cu rezoluția

#### Q: Webhook nu funcționează
**A:** Webhook-urile necesită IP public. Pe localhost, folosește pull/push manual.

---

### 10. Next Steps

După ce ai configurat tot:

1. **Testează workflow-ul**:
   - Modifică ceva în HA
   - Push la GitHub
   - Verifică pe GitHub că e acolo
   - Modifică pe GitHub
   - Pull din GitHub
   - Verifică în HA că s-a schimbat

2. **Automatizări utile**:
   - Backup automat în GitHub (cron job)
   - Notificări la pull/push successful
   - Check configurație înainte de push
   - Auto-restart HA după pull

3. **Documentează**:
   - Structura ta de configurație
   - Automatizări custom
   - Integrări folosite
   - Proceduri de recovery

---

## 🎉 Gata!

Acum ai un sistem complet de version control pentru configurațiile Home Assistant, cu:
- ✅ Backup automat pe GitHub
- ✅ Sincronizare între multiple servere
- ✅ Istoric complet al modificărilor
- ✅ Posibilitate de rollback
- ✅ Colaborare în echipă (dacă invitați alții)

**Enjoy!** 🚀
