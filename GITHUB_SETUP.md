# 🔧 GitHub OAuth Setup Guide

## Pași pentru Configurare GitHub Integration

### 1. Creează GitHub OAuth App

1. **Accesează GitHub Developer Settings:**
   - Du-te la: https://github.com/settings/developers
   - Click pe "OAuth Apps" din sidebar
   - Click pe "New OAuth App"

2. **Completează Formularul:**
   ```
   Application name: HA Config Manager (sau orice nume vrei)
   Homepage URL: http://localhost:3000
   Application description: Home Assistant Configuration Manager (opțional)
   Authorization callback URL: http://localhost:3000/api/auth/github/callback
   ```

3. **Înregistrează Aplicația:**
   - Click "Register application"
   - Vei vedea **Client ID** - copiază-l
   - Click "Generate a new client secret"
   - Vei vedea **Client Secret** - copiază-l (se arată o singură dată!)

### 2. Creează Personal Access Token (pentru API)

1. **Accesează Token Settings:**
   - Du-te la: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"

2. **Configurează Token-ul:**
   ```
   Note: HA Config Manager API
   Expiration: No expiration (sau 90 days)

   Scopes (bifează):
   ✅ repo (Full control of private repositories)
   ✅ read:user (Read ALL user profile data)
   ✅ admin:repo_hook (Full control of repository hooks)
   ```

3. **Generează și Copiază:**
   - Click "Generate token"
   - **IMPORTANT:** Copiază token-ul ACUM (nu se va mai arăta!)

### 3. Creează Fișierul `.env`

În rădăcina proiectului, creează fișierul `.env`:

```bash
# Copiază .env.example și completează cu valorile tale
cp .env.example .env
```

Sau creează manual `.env` cu:

```env
# GitHub OAuth Configuration
NEXT_PUBLIC_GITHUB_CLIENT_ID=your_client_id_from_step_1
GITHUB_CLIENT_SECRET=your_client_secret_from_step_1
GITHUB_TOKEN=your_personal_access_token_from_step_2
GITHUB_WEBHOOK_SECRET=any_random_secure_string_min_32_chars

# Deepseek AI (opțional - pentru AI Assistant)
DEEPSEEK_API_KEY=your_deepseek_api_key_if_you_have_one

# Tailscale (opțional - pentru VPN integration)
TAILSCALE_API_KEY=your_tailscale_api_key_if_you_have_one
TAILSCALE_TAILNET=your_tailnet_name
```

### 4. Generează Webhook Secret

Pentru `GITHUB_WEBHOOK_SECRET`, folosește un string random securizat:

**Windows (PowerShell):**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

**Linux/Mac:**
```bash
openssl rand -hex 32
```

**Sau folosește orice string random de minim 32 caractere.**

### 5. Restart Containers

După ce ai creat `.env`, restart containerele:

```bash
docker-compose down
docker-compose up -d --build
```

### 6. Testează Integrarea

1. Accesează: http://localhost:3000
2. Loghează-te
3. Du-te la pagina "GitHub"
4. Click "Connect GitHub"
5. Autorizează aplicația pe GitHub
6. Vei fi redirectat înapoi și vei vedea "Connected as [your_username]"

---

## 🎯 Ce Poți Face După Configurare

### Link Repository la Server

1. Accesează pagina "GitHub"
2. Secțiunea "Link Repository to Server"
3. Selectează:
   - **Server:** Serverul tău HA
   - **Repository:** Repository-ul cu configurații
   - **Branch:** `main` (sau branch-ul tău)
4. Click "Link Repository"

### Deploy Manual

După linking:
1. Găsește serverul în tabelul "Linked Repositories"
2. Click butonul "Deploy"
3. Configurațiile din GitHub vor fi deploy-ate pe server
4. Backup automat înainte de deploy
5. Rollback disponibil în caz de eroare

### Configurează Auto-Deploy (Webhook)

1. Secțiunea "Webhook Configuration"
2. Click "Configure Webhook"
3. Selectează repository-ul
4. Click "Create Webhook"
5. Acum, la fiecare `git push` pe branch-ul linked, deployment automat!

---

## 🔒 Securitate

### .env File
- **NU comite `.env` în git!**
- Fișierul `.gitignore` deja îl exclude
- Pentru production, folosește secrets management (Docker secrets, Kubernetes secrets, etc.)

### GitHub Token
- Păstrează token-ul în siguranță
- Nu-l partaja niciodată
- Regenerează-l periodic
- Revoke token-ul imediat dacă e compromis

### OAuth App
- Folosește HTTPS în production
- Actualizează callback URL pentru domeniul tău
- Monitorizează access logs pe GitHub

---

## ❓ Troubleshooting

### "client_id is undefined"
- ✅ Verifică că `.env` există
- ✅ Verifică că `NEXT_PUBLIC_GITHUB_CLIENT_ID` e setat
- ✅ Restart containers: `docker-compose restart`

### "GitHub not connected"
- ✅ Verifică `GITHUB_TOKEN` în `.env`
- ✅ Verifică că token-ul are scope-urile corecte
- ✅ Check logs: `docker logs ha-config-orchestrator`

### "Failed to create webhook"
- ✅ Verifică `GITHUB_WEBHOOK_SECRET` e setat
- ✅ Verifică că token-ul are `admin:repo_hook` scope
- ✅ Verifică că ești owner al repository-ului

### "Deployment failed"
- ✅ Verifică SSH credentials pentru server
- ✅ Check logs în Deployments page
- ✅ Verifică că repository-ul are configurații valide YAML

---

## 📚 Resurse

- [GitHub OAuth Apps Documentation](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps)
- [GitHub Webhooks Guide](https://docs.github.com/en/webhooks)
- [Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

---

## ✅ Checklist Setup

- [ ] GitHub OAuth App creat
- [ ] Client ID copiat
- [ ] Client Secret copiat
- [ ] Personal Access Token generat cu scope-uri corecte
- [ ] Fișier `.env` creat
- [ ] Toate variabilele completate în `.env`
- [ ] Containers restarted
- [ ] GitHub connection test reușit
- [ ] Repository linked la server
- [ ] Manual deployment test reușit
- [ ] Webhook configurat (opțional)
- [ ] Auto-deploy test reușit (opțional)

---

**Gata! Acum ai GitHub integration complet funcțional!** 🎉

Pentru suport sau întrebări, verifică logs:
```bash
# Backend logs
docker logs ha-config-orchestrator -f

# Frontend logs
docker logs ha-config-dashboard -f
```
