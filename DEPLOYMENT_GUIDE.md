# 🚀 HA Config Manager - Deployment & Testing Guide

**Ultima actualizare:** 1 Ianuarie 2026
**Versiune platformă:** v1.0 (Production-Ready)

---

## 📋 Cuprins

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Configurare Inițială](#configurare-inițială)
4. [GitHub OAuth Setup](#github-oauth-setup)
5. [Deployment Development](#deployment-development)
6. [Deployment Production](#deployment-production)
7. [Testing Guide](#testing-guide)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)

---

## 🚀 Quick Start

### Pornire Rapidă (Development)

```bash
# 1. Clone repository
git clone <repository-url>
cd ha-config-manager

# 2. Pornește containerele
docker-compose up -d

# 3. Verifică status
docker ps

# 4. Accesează aplicația
# Frontend: http://localhost:3000
# Backend API: http://localhost:8081/docs (Swagger UI)
# Database: localhost:5432
```

**Gata!** Platforma rulează. Acum poți crea un cont și adăuga servere.

**⚠️ Pentru GitHub Integration:** Vezi secțiunea [GitHub OAuth Setup](#github-oauth-setup)

---

## 📦 Prerequisites

### Software Necesar

- **Docker:** v24.0+ ([Download](https://www.docker.com/products/docker-desktop))
- **Docker Compose:** v2.20+ (inclus în Docker Desktop)
- **Git:** Orice versiune recentă
- **Browser modern:** Chrome, Firefox, Edge, Safari

### Hardware Recomandat

**Minim:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB free space

**Recomandat:**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 20GB+ free space
- SSD pentru performanță

### Ports Necesare

Asigură-te că următoarele porturi sunt libere:
- **3000** - Frontend (Next.js)
- **8081** - Backend (FastAPI)
- **5432** - PostgreSQL

**Verificare:**
```bash
# Windows
netstat -ano | findstr "3000 8081 5432"

# Linux/Mac
lsof -i :3000 -i :8081 -i :5432
```

---

## ⚙️ Configurare Inițială

### 1. Environment Variables (Opțional)

Platforma funcționează out-of-the-box cu setări default. Pentru features avansate:

```bash
# Copiază template-ul
cp .env.example .env

# Editează .env cu valorile tale
nano .env  # sau notepad .env pe Windows
```

**Variabile disponibile:**

```env
# GitHub Integration (opțional - vezi secțiunea GitHub OAuth Setup)
NEXT_PUBLIC_GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_WEBHOOK_SECRET=random_secure_string_min_32_chars

# Deepseek AI Assistant (opțional)
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Tailscale VPN (opțional)
TAILSCALE_API_KEY=tskey-api-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TAILSCALE_TAILNET=your-tailnet-name
```

**⚠️ Important:** Dacă nu creezi `.env`, platforma folosește valorile default din `docker-compose.yml`. GitHub Integration va necesita configurare ulterioară.

### 2. Build & Start Containers

```bash
# Build și pornire toate containerele
docker-compose up -d --build

# Verifică logs pentru erori
docker-compose logs -f

# Sau logs individual
docker logs ha-config-orchestrator -f
docker logs ha-config-dashboard -f
docker logs ha-config-postgres -f
```

**Așteptare:** Prima build durează 2-5 minute (download images + install dependencies).

### 3. Verificare Health

```bash
# Check toate containerele rulează
docker ps

# Output așteptat:
# ha-config-postgres   Up X minutes (healthy)
# ha-config-orchestrator   Up X minutes
# ha-config-dashboard   Up X minutes
```

**Health check endpoints:**
- Backend: http://localhost:8081/docs (Swagger UI)
- Frontend: http://localhost:3000 (Login page)

### 4. Creare Cont Utilizator

**Opțiunea 1: UI (Recomandat)**
1. Accesează http://localhost:3000/register
2. Completează username, email, password
3. Click "Register"
4. Redirect automat la login
5. Login cu credențialele create

**Opțiunea 2: Script (Advanced)**
```bash
# Rulează script de creare user
docker exec -it ha-config-orchestrator python /app/create_test_user.py

# Sau creează manual prin API
curl -X POST http://localhost:8081/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "SecurePassword123!"
  }'
```

---

## 🔐 GitHub OAuth Setup

**⚠️ Opțional dar recomandat** pentru GitHub Integration (auto-deploy din repo).

### Pas 1: Creare GitHub OAuth App

1. **Accesează GitHub Developer Settings:**
   - URL: https://github.com/settings/developers
   - Click "OAuth Apps" → "New OAuth App"

2. **Completează formularul:**
   ```
   Application name: HA Config Manager
   Homepage URL: http://localhost:3000
   Authorization callback URL: http://localhost:3000/api/auth/github/callback
   ```

3. **Salvează credențialele:**
   - Copiază **Client ID** (format: `Iv1.xxxxxxxxxxxxxxxx`)
   - Click "Generate a new client secret"
   - Copiază **Client Secret** (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
   - ⚠️ **Client Secret se arată o singură dată!** Salvează-l acum.

### Pas 2: Creare Personal Access Token

1. **Accesează Token Settings:**
   - URL: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"

2. **Configurează token:**
   ```
   Note: HA Config Manager API
   Expiration: No expiration (sau 90 days)

   Scopes (selectează):
   ✅ repo (Full control of private repositories)
      ✅ repo:status
      ✅ repo_deployment
      ✅ public_repo
      ✅ repo:invite
   ✅ read:user (Read ALL user profile data)
   ✅ admin:repo_hook (Full control of repository hooks)
      ✅ write:repo_hook
      ✅ read:repo_hook
   ```

3. **Copiază token:**
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - ⚠️ **Se arată o singură dată!** Salvează-l acum.

### Pas 3: Generare Webhook Secret

**Windows PowerShell:**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

**Linux/Mac:**
```bash
openssl rand -hex 32
```

**Sau folosește:** Orice string random de minim 32 caractere (parola securizată).

### Pas 4: Configurare .env

Creează/editează fișierul `.env`:

```bash
# Windows
notepad .env

# Linux/Mac
nano .env
```

Adaugă valorile obținute:

```env
# GitHub OAuth
NEXT_PUBLIC_GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_WEBHOOK_SECRET=your_random_32_char_string_here
```

### Pas 5: Restart Containers

```bash
docker-compose down
docker-compose up -d
```

**⚠️ Important:** Restart este necesar pentru a încărca noile environment variables.

### Pas 6: Test GitHub Integration

1. **Accesează pagina GitHub:**
   - URL: http://localhost:3000/github

2. **Connect GitHub:**
   - Click "Connect GitHub"
   - Autorizează aplicația pe GitHub
   - Redirect înapoi la platformă

3. **Verifică conexiune:**
   - Ar trebui să vezi: "Connected as [your_username]"
   - Lista repositories ar trebui să se încarce

4. **Link repository la server:**
   - Selectează un server din dropdown
   - Selectează un repository
   - Selectează branch (ex: `main`)
   - Click "Link Repository"

5. **Test deployment:**
   - Click butonul "Deploy" din tabelul "Linked Repositories"
   - Verifică logs în pagina Deployments

**✅ Succes!** GitHub Integration este acum complet funcțional.

---

## 💻 Deployment Development

### Start/Stop Containers

```bash
# Start toate
docker-compose up -d

# Stop toate
docker-compose down

# Restart toate
docker-compose restart

# Restart individual
docker-compose restart orchestrator
docker-compose restart dashboard
```

### Rebuild După Modificări Cod

**Backend changes:**
```bash
# Rebuild orchestrator
docker-compose up -d --build orchestrator

# Sau rebuild + view logs
docker-compose up --build orchestrator
```

**Frontend changes:**
```bash
# Rebuild dashboard
docker-compose up -d --build dashboard
```

**Rebuild all:**
```bash
# Force rebuild toate containerele
docker-compose up -d --build --force-recreate
```

### Development Workflow

**Backend (Python):**
1. Modifică cod în `orchestrator/`
2. Restart container: `docker-compose restart orchestrator`
3. Check logs: `docker logs ha-config-orchestrator -f`
4. Test endpoint: Browser sau Postman

**Frontend (Next.js):**
1. Modifică cod în `dashboard-react/`
2. Hot reload automat (Fast Refresh)
3. Refresh browser
4. Check console pentru erori

**Database schema changes:**
1. Modifică models în `orchestrator/app/models/`
2. (Todo) Generează migrație Alembic
3. Run migration
4. Update schemas în `orchestrator/app/schemas/`

### Logs și Debugging

```bash
# View logs toate containerele
docker-compose logs -f

# Logs individual cu tail
docker logs ha-config-orchestrator -f --tail=100
docker logs ha-config-dashboard -f --tail=100
docker logs ha-config-postgres -f --tail=100

# Search în logs
docker logs ha-config-orchestrator 2>&1 | grep "ERROR"

# Exec în container pentru debugging
docker exec -it ha-config-orchestrator bash
docker exec -it ha-config-dashboard sh

# Connect la PostgreSQL
docker exec -it ha-config-postgres psql -U haconfig -d haconfig
```

### Database Management

```bash
# Backup database
docker exec ha-config-postgres pg_dump -U haconfig haconfig > backup.sql

# Restore database
cat backup.sql | docker exec -i ha-config-postgres psql -U haconfig haconfig

# Reset database (⚠️ Șterge toate datele!)
docker-compose down -v  # -v șterge volumes
docker-compose up -d
```

---

## 🌐 Deployment Production

### Pre-Production Checklist

- [ ] **Change SECRET_KEY** în docker-compose.yml (min 32 chars random)
- [ ] **Change ENCRYPTION_KEY** (generează nou cu Fernet.generate_key())
- [ ] **Change PostgreSQL password** în docker-compose.yml
- [ ] **Setup HTTPS** (reverse proxy: Nginx, Traefik, Caddy)
- [ ] **Configure domain** DNS records
- [ ] **Setup backup automations** (database + SSH keys)
- [ ] **Enable monitoring** (Prometheus + Grafana)
- [ ] **Configure log aggregation** (ELK, Loki, etc.)
- [ ] **Review CORS settings** (`orchestrator/app/config.py`)
- [ ] **Setup email** pentru notifications (SMTP config)
- [ ] **Configure rate limiting** (prevent abuse)

### Production Environment Variables

**Minimale necesare:**
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

# Security (generează noi valori!)
SECRET_KEY=<64-char-random-string>
ENCRYPTION_KEY=<fernet-key-32-bytes-base64>

# GitHub (opțional)
GITHUB_TOKEN=ghp_xxx
GITHUB_CLIENT_SECRET=xxx
GITHUB_WEBHOOK_SECRET=xxx
NEXT_PUBLIC_GITHUB_CLIENT_ID=Iv1.xxx

# AI Assistant (opțional)
DEEPSEEK_API_KEY=sk-xxx

# Tailscale (opțional)
TAILSCALE_API_KEY=tskey-xxx
TAILSCALE_TAILNET=your-tailnet
```

### Generate Secure Keys

**SECRET_KEY (JWT signing):**
```python
# Python
import secrets
print(secrets.token_urlsafe(64))
```

**ENCRYPTION_KEY (Fernet):**
```python
# Python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

**PostgreSQL Password:**
```bash
# Linux/Mac
openssl rand -base64 32

# Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

### Reverse Proxy Setup (Nginx Example)

**nginx.conf:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8081;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket (Terminal)
    location /api/v1/terminal/ {
        proxy_pass http://localhost:8081;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
```

### Docker Compose Production

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - internal

  orchestrator:
    build:
      context: ./orchestrator
      dockerfile: Dockerfile.prod
    restart: always
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./orchestrator/keys:/app/keys
    networks:
      - internal
    depends_on:
      - postgres

  dashboard:
    build:
      context: ./dashboard-react
      dockerfile: Dockerfile.prod
    restart: always
    environment:
      - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
      - NEXT_PUBLIC_GITHUB_CLIENT_ID=${NEXT_PUBLIC_GITHUB_CLIENT_ID}
    networks:
      - internal
    depends_on:
      - orchestrator

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    networks:
      - internal
    depends_on:
      - dashboard
      - orchestrator

volumes:
  postgres_data:

networks:
  internal:
    driver: bridge
```

**Deploy:**
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 🧪 Testing Guide

### Manual Testing Checklist

#### 1. Authentication
- [ ] Register new user
- [ ] Login cu credențiale corecte
- [ ] Login fail cu credențiale greșite
- [ ] Logout
- [ ] Protected routes redirect la login când nu ești autentificat

#### 2. Server Management
- [ ] Add new server (SSH password)
- [ ] Add new server (SSH key - OpenSSH)
- [ ] Add new server (SSH key - PPK format)
- [ ] Edit server details
- [ ] Test server connection (SSH + HA API)
- [ ] View system info (CPU, RAM, Disk)
- [ ] Delete server

#### 3. Config File Management
- [ ] Sync configs from server (393 files)
- [ ] Navigate file tree (expand/collapse folders)
- [ ] Search files în timp real
- [ ] Open și edit fișier config
- [ ] Save changes to server
- [ ] Verify changes persistent după save

#### 4. Terminal SSH
- [ ] Select server from dropdown
- [ ] Terminal connection established
- [ ] Execute commands (ls, pwd, cd, etc.)
- [ ] ANSI colors funcționează
- [ ] Resize terminal funcționează
- [ ] Disconnect gracefully

#### 5. GitHub Integration (dacă configurat)
- [ ] Connect GitHub OAuth
- [ ] View repositories list
- [ ] Select repository + branch
- [ ] Link repository la server
- [ ] Trigger manual deployment
- [ ] Verify backup created
- [ ] Check deployment logs
- [ ] Configure webhook
- [ ] Test auto-deploy (git push trigger)

#### 6. Home Assistant Actions
- [ ] Restart HA instance
- [ ] Check config validation
- [ ] View HA version
- [ ] Proxy HA API requests

### Automated Testing Scripts

#### Test 1: Full API Integration

**File:** `orchestrator/test_api_integration.py`

```bash
# Rulare
python orchestrator/test_api_integration.py

# Output așteptat
✓ Login successful (status 200)
✓ Token received: eyJ0eXAiOiJKV1QiLCJhbGc...
✓ Servers list retrieved: 1 server(s)
✓ Server test connection: SUCCESS
  - SSH: ✓ (latency: 587ms)
  - HA API: ✓ (latency: 42ms)
```

#### Test 2: Config Editor + Terminal

**File:** `test_features.py`

```bash
# Rulare
python test_features.py

# Output așteptat
✓ Authentication successful
✓ Sync configs: 393 files synced
✓ Update config file: SUCCESS
✓ WebSocket terminal endpoint: AVAILABLE
```

#### Test 3: SSH Connection

**File:** `orchestrator/test_ssh_ppk.py`

```bash
# Rulare
python orchestrator/test_ssh_ppk.py

# Output așteptat
✓ SSH connection established
✓ Command executed: hostname
✓ Output: your-server-hostname
```

### Performance Testing

**Load test API endpoints:**
```bash
# Install Apache Bench
# Windows: Download from https://httpd.apache.org/
# Linux: apt-get install apache2-utils
# Mac: brew install httpd

# Test login endpoint
ab -n 1000 -c 10 -p login.json -T application/json http://localhost:8081/api/v1/auth/login

# Test servers list
ab -n 1000 -c 10 -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8081/api/v1/servers
```

**Monitor resource usage:**
```bash
# Container stats
docker stats

# Detailed stats
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```

### Security Testing

**Check exposed ports:**
```bash
nmap -p 3000,8081,5432 localhost
```

**Test authentication bypass:**
```bash
# Attempt access protected endpoint fără token
curl http://localhost:8081/api/v1/servers

# Expected: 401 Unauthorized
```

**Test SQL injection:**
```bash
# Attempt malicious input
curl -X POST http://localhost:8081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'\'' OR 1=1--","password":"anything"}'

# Expected: Login fail (Pydantic validation prevents injection)
```

---

## 🔧 Troubleshooting

### Common Issues

#### Issue 1: Containers nu pornesc

**Symptom:** `docker-compose up` eșuează

**Debug:**
```bash
# Check logs
docker-compose logs

# Check specific container
docker-compose logs orchestrator
docker-compose logs dashboard
docker-compose logs postgres
```

**Soluții:**
- Verifică porturi libere (3000, 8081, 5432)
- Verifică disk space: `df -h`
- Rebuild containers: `docker-compose up -d --build --force-recreate`

#### Issue 2: Frontend nu se încarcă

**Symptom:** http://localhost:3000 timeout sau blank page

**Debug:**
```bash
# Check dashboard logs
docker logs ha-config-dashboard -f

# Check dacă containerul rulează
docker ps | grep dashboard
```

**Soluții:**
- Verifică `NEXT_PUBLIC_API_URL` în docker-compose.yml
- Check browser console pentru erori
- Rebuild frontend: `docker-compose up -d --build dashboard`

#### Issue 3: Backend API errors

**Symptom:** API calls returnează 500 sau timeout

**Debug:**
```bash
# Check orchestrator logs
docker logs ha-config-orchestrator -f

# Check database connection
docker exec -it ha-config-postgres psql -U haconfig -d haconfig -c "SELECT 1;"
```

**Soluții:**
- Verifică `DATABASE_URL` corect
- Check PostgreSQL healthcheck: `docker inspect ha-config-postgres | grep Health`
- Restart orchestrator: `docker-compose restart orchestrator`

#### Issue 4: GitHub OAuth "client_id undefined"

**Symptom:** Redirect la `https://github.com/login/oauth/authorize?client_id=undefined`

**Cauză:** `NEXT_PUBLIC_GITHUB_CLIENT_ID` lipsește

**Soluție:**
```bash
# Adaugă în .env
echo "NEXT_PUBLIC_GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxxxxxx" >> .env

# Restart dashboard
docker-compose restart dashboard
```

#### Issue 5: SSH connection failed

**Symptom:** "Permission denied" sau "Connection timeout"

**Debug:**
```bash
# Test SSH manual
ssh -i path/to/key.ppk user@host -p 22

# Check server în DB
docker exec -it ha-config-orchestrator python /app/debug_server.py
```

**Soluții:**
- Verifică SSH credentials corecte
- Verifică SSH key permissions (600)
- Verifică server IP/port accesibil
- Test conversie PPK: `puttygen key.ppk -O private-openssh -o key.openssh`

#### Issue 6: Config sync returns 0 files

**Symptom:** "Configurations synced successfully" dar "No configs found"

**Cauză:** Symlink `/config` → `/homeassistant` nu este urmat

**Soluție:** **DEJA REZOLVAT** în v1.0 cu flag `-L` în `find` command

**Verificare:**
```bash
# Conectează SSH la server
docker exec -it ha-config-orchestrator python -c "
from app.utils.ssh import execute_ssh_command
print(execute_ssh_command(server_id=1, command='find -L /config -maxdepth 2 -type f | wc -l'))
"

# Should return: 30+ files
```

#### Issue 7: Database connection errors

**Symptom:** "FATAL: password authentication failed for user"

**Debug:**
```bash
# Check PostgreSQL logs
docker logs ha-config-postgres

# Test connection
docker exec -it ha-config-postgres psql -U haconfig -d haconfig
```

**Soluții:**
- Verifică `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` match în docker-compose.yml
- Verifică `DATABASE_URL` format corect: `postgresql+asyncpg://user:pass@postgres:5432/dbname`
- Reset database: `docker-compose down -v && docker-compose up -d`

#### Issue 8: WebSocket terminal not connecting

**Symptom:** Terminal shows "Connection failed" sau blank

**Debug:**
```bash
# Check orchestrator logs
docker logs ha-config-orchestrator | grep -i websocket

# Test WebSocket endpoint
wscat -c "ws://localhost:8081/api/v1/terminal/1?token=YOUR_JWT_TOKEN"
```

**Soluții:**
- Verifică JWT token valid (check localStorage în browser)
- Verifică server status online
- Check firewall/antivirus nu blochează WebSocket
- Verifică browser support WebSocket (toate browserele moderne)

---

## 🔄 Maintenance

### Regular Tasks

**Daily:**
- [ ] Check logs pentru erori: `docker-compose logs --tail=100`
- [ ] Monitor disk usage: `docker system df`

**Weekly:**
- [ ] Backup database: `docker exec ha-config-postgres pg_dump -U haconfig haconfig > backups/weekly_$(date +%Y%m%d).sql`
- [ ] Review audit logs (când implementat)
- [ ] Update dependencies: `docker-compose pull`

**Monthly:**
- [ ] Rotate logs: `docker-compose logs > logs/archive_$(date +%Y%m).log`
- [ ] Review și cleanup backups vechi
- [ ] Security audit (check pentru vulnerabilities)
- [ ] Performance review (slow queries, resource usage)

### Backup Strategy

**Database Backup (Automated):**
```bash
# Cron job pentru backup daily (Linux/Mac)
0 2 * * * docker exec ha-config-postgres pg_dump -U haconfig haconfig | gzip > /backups/ha-config-$(date +\%Y\%m\%d).sql.gz

# Windows Task Scheduler
# Rulează PowerShell script:
docker exec ha-config-postgres pg_dump -U haconfig haconfig | Out-File -FilePath "C:\backups\ha-config-$(Get-Date -Format 'yyyyMMdd').sql"
```

**SSH Keys Backup:**
```bash
# Backup keys folder
tar -czf keys-backup-$(date +%Y%m%d).tar.gz orchestrator/keys/

# Restore
tar -xzf keys-backup-YYYYMMDD.tar.gz -C orchestrator/
```

**Full Application Backup:**
```bash
# Backup everything (code + data + config)
tar -czf ha-config-manager-full-$(date +%Y%m%d).tar.gz \
  --exclude=node_modules \
  --exclude=.next \
  --exclude=__pycache__ \
  .
```

### Updates și Upgrades

**Update Docker images:**
```bash
# Pull latest images
docker-compose pull

# Rebuild cu noi images
docker-compose up -d --build
```

**Update Python dependencies:**
```bash
# Editează orchestrator/requirements.txt
# Rebuild container
docker-compose up -d --build orchestrator
```

**Update Node dependencies:**
```bash
# Editează dashboard-react/package.json
# Rebuild container
docker-compose up -d --build dashboard
```

### Monitoring Setup (Advanced)

**Prometheus + Grafana (Optional):**

**docker-compose.monitoring.yml:**
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - ha-config-network

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - ha-config-network
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:

networks:
  ha-config-network:
    external: true
```

**Start monitoring:**
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

---

## 📞 Support

### Log Collection pentru Debug

```bash
# Collect toate logs
mkdir debug-logs
docker-compose logs > debug-logs/all-logs.txt
docker logs ha-config-orchestrator > debug-logs/orchestrator.log
docker logs ha-config-dashboard > debug-logs/dashboard.log
docker logs ha-config-postgres > debug-logs/postgres.log

# Container inspect
docker inspect ha-config-orchestrator > debug-logs/orchestrator-inspect.json
docker inspect ha-config-dashboard > debug-logs/dashboard-inspect.json

# Archive pentru support
tar -czf debug-logs-$(date +%Y%m%d-%H%M%S).tar.gz debug-logs/
```

### Useful Commands Reference

```bash
# Container management
docker-compose up -d                    # Start all
docker-compose down                     # Stop all
docker-compose restart SERVICE          # Restart specific
docker-compose logs -f SERVICE          # Follow logs
docker-compose ps                       # List containers

# Docker system
docker system df                        # Disk usage
docker system prune                     # Cleanup unused
docker volume ls                        # List volumes
docker network ls                       # List networks

# Database
docker exec -it ha-config-postgres psql -U haconfig -d haconfig
docker exec ha-config-postgres pg_dump -U haconfig haconfig > backup.sql

# Debugging
docker exec -it ha-config-orchestrator bash
docker exec -it ha-config-dashboard sh
docker logs CONTAINER -f --tail=100
```

---

## ✅ Post-Deployment Checklist

- [ ] Toate containerele running și healthy
- [ ] Frontend accesibil la http://localhost:3000
- [ ] Backend API accesibil la http://localhost:8081/docs
- [ ] Database connection funcțională
- [ ] User registration funcționează
- [ ] User login funcționează
- [ ] Server add funcționează (SSH connection test passed)
- [ ] Config sync funcționează (393 files)
- [ ] Terminal SSH funcționează
- [ ] GitHub OAuth configurat (dacă necesar)
- [ ] Backup setup configurat
- [ ] Logs reviewed pentru erori
- [ ] Documentation citită și înțeleasă

**🎉 Felicitări! Platforma HA Config Manager este deployed și funcțională!**

---

**Document creat:** 1 Ianuarie 2026
**Pentru suport:** Vezi `progress.md`, `PLATFORM_STATUS_COMPLETE.md`, `GITHUB_SETUP.md`
