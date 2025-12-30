# 🚀 Quick Start Guide

## Pași Rapizi (10 Minute)

### 1. Creează Repository Privat pe GitHub (2 minute)

1. **Accesează**: https://github.com/new
2. **Completează**:
   - Repository name: `ha-config-manager`
   - Description: `Multi-Instance Home Assistant Configuration Management`
   - Visibility: **🔒 Private** (foarte important!)
   - ❌ **NU** adăuga README, .gitignore, sau license
3. **Click**: "Create repository"

### 2. Push Codul (2 minute)

După ce ai creat repository-ul, GitHub îți arată comenzile. Folosește:

```bash
cd /tmp/ha-config-manager

# Adaugă remote
git remote add origin https://github.com/cmdchar/ha-config-manager.git

# Commit tot codul
git add -A
git commit -m "Initial commit: HA Config Manager MVP"

# Push
git push -u origin master
```

**IMPORTANT**: Când Git cere credențiale:
- Username: `cmdchar`
- Password: Folosește **Personal Access Token** (nu parola!)

### 3. Pornește Serviciile Local (3 minute)

```bash
# Clone repository-ul tău (dacă nu ești deja în el)
git clone https://github.com/cmdchar/ha-config-manager.git
cd ha-config-manager

# Configurează environment
cp .env.example .env
nano .env  # Editează cu settings-urile tale

# Pornește totul
docker-compose up -d

# Verifică că merge
curl http://localhost:8080/api/health
```

### 4. Accesează Dashboard (1 minut)

Deschide în browser: **http://localhost:3000**

Vei vedea:
- 3 servere configurate (192.168.1.61, .99, .68)
- Status live
- Butoane deploy

### 5. Instalează Add-on pe HA (3 minute per server)

Pe fiecare server Home Assistant:

**Metoda 1: File Editor (Simplu)**
1. Deschide File Editor în HA
2. Creează folder `/addons/ha-config-sync/`
3. Copiază fișierele din `addon/` din repository
4. Restart Supervisor
5. Instalează add-on-ul

**Metoda 2: SSH (Rapid)**
```bash
# SSH în serverul HA
ssh root@192.168.1.61

# Creează directorul
mkdir -p /addons/ha-config-sync

# Clone repository
cd /addons
git clone https://github.com/cmdchar/ha-config-manager.git temp
mv temp/addon/* ha-config-sync/
rm -rf temp

# Restart
ha supervisor restart
```

### 6. Configurează Add-on

Pentru fiecare server, configurează:

**Server 1 (192.168.1.61):**
```yaml
github_repo: "cmdchar/ha-config"
github_token: "ghp_YOUR_TOKEN"
github_branch: "main"
server_id: "server-61"
orchestrator_url: "http://YOUR_PC_IP:8080"
auto_sync: true
sync_interval: 300
```

**Server 2 (192.168.1.99):**
```yaml
server_id: "server-99"
# Rest same as above
```

**Server 3 (192.168.1.68):**
```yaml
server_id: "server-68"
# Rest same as above
```

### 7. Test Primul Deployment

```bash
# Via API
curl -X POST http://localhost:8080/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "server_ids": ["server-61"],
    "github_repo": "cmdchar/ha-config",
    "branch": "main"
  }'

# Sau din Dashboard
# Click "Deploy" pe server-61
```

---

## ✅ Verificare

După deployment, verifică:

1. **Dashboard**: Vezi status "syncing" → "online"
2. **HA Logs**: Check logs în add-on
3. **Config**: Verifică că fișierele au fost update-ate

---

## 🎯 Ce Urmează?

### Dezvoltare:

1. **Adaugă features noi**:
   ```bash
   git checkout -b feature/rollback-support
   # Fă modificări
   git commit -m "feat: add rollback support"
   git push origin feature/rollback-support
   ```

2. **Testează**:
   ```bash
   make test
   ```

3. **Deploy nou**:
   ```bash
   docker-compose up --build -d
   ```

### Monetizare:

1. **SaaS Version**:
   - Deploy orchestrator în cloud (AWS/DigitalOcean)
   - Adaugă autentificare
   - Stripe pentru plăți
   - Marketing

2. **HACS Release**:
   - Publică add-on-ul
   - Documentație video
   - Community support

---

## 🆘 Troubleshooting

### Repository nu se creează
- Verifică că ești autentificat pe GitHub
- Verifică limite (max 100 repo-uri private pe cont free)

### Push eșuează
- Folosește Personal Access Token, nu parola
- Verifică că token-ul are permisiuni `repo`

### Docker nu pornește
```bash
# Verifică logs
docker-compose logs

# Restart
docker-compose down && docker-compose up -d
```

### Add-on nu apare în HA
```bash
# Restart Supervisor
ha supervisor restart

# Check logs
ha supervisor logs
```

---

## 📞 Support

- **GitHub Issues**: Pentru bug-uri
- **GitHub Discussions**: Pentru întrebări
- **Email**: cmdchar@example.com

---

**Succes cu testarea! 🚀**
