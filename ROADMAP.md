# 🗺️ HA Config Manager - Roadmap Complet

## Viziune Generală

**Obiectiv:** Platformă centralizată pentru management configurații Home Assistant cu GitHub ca single source of truth, deployment automat și suport multi-instance.

---

## ✅ Ce Avem Implementat (Ianuarie 2026)

### **Infrastructură Core** ✅
- [x] Docker multi-service (Orchestrator, Dashboard, PostgreSQL)
- [x] FastAPI Backend (Python 3.13) cu SQLAlchemy async
- [x] Next.js 16 Frontend cu React 19, TypeScript
- [x] PostgreSQL 16 pentru persistență date
- [x] Criptare credențiale (Fernet encryption)
- [x] SSH Backend complet funcțional (asyncssh)

### **Autentificare & Securitate** ✅
- [x] JWT-based authentication
- [x] User management (login, register)
- [x] Password hashing (bcrypt)
- [x] Encrypted SSH credentials storage
- [x] SSH key support (OpenSSH + PPK automatic conversion)
- [x] Passphrase encryption pentru chei SSH

### **Server Management** ✅
- [x] CRUD operații pentru servere HA
- [x] SSH connection testing
- [x] System info retrieval (CPU, RAM, Disk, Uptime)
- [x] HA version detection
- [x] Online/Offline status tracking
- [x] Server dashboard complet (Overview, Actions, Terminal, System Info)

### **Config Editor** ✅ **NOU!**
- [x] Sync configurații de pe server (393 fișiere)
- [x] **Hierarchical tree view** cu foldere colapsabile
- [x] **Search în timp real** prin toate fișierele
- [x] Editor text pentru modificare conținut
- [x] Save changes back to server via SSH
- [x] Support pentru YAML, JSON, CONF files
- [x] Symlink handling (`/config -> /homeassistant`)
- [x] Maxdepth 5 pentru subfoldere nested

### **Terminal WebSocket** ✅
- [x] WebSocket endpoint pentru SSH interactive
- [x] xterm.js integration în frontend
- [x] Full terminal support (colors, resize, interactive commands)
- [x] Auto-cleanup la disconnect

### **Home Assistant Operations** ✅
- [x] Restart HA (auto-detect: HA OS → Supervised → Docker)
- [x] Check configuration validity
- [x] HA API proxy (basic)

### **UI/UX** ✅
- [x] Modern dashboard cu Tailwind CSS + shadcn/ui
- [x] Server list cu status indicators
- [x] Responsive design
- [x] Toast notifications (sonner)
- [x] Loading states & error handling
- [x] File tree navigation cu icons

---

## 🚧 Ce Trebuie Implementat (Roadmap GitHub Original)

### **PHASE 1: GitHub Integration** 🎯 PRIORITATE MAXIMĂ

#### 1.1 GitHub Repository Connection
- [ ] **Backend: GitHub API Client**
  - [ ] OAuth App setup pentru autentificare GitHub
  - [ ] Repository list endpoint
  - [ ] Repository content fetching
  - [ ] Branch management
  - [ ] File tree retrieval

- [ ] **Frontend: Repository Selector**
  - [ ] GitHub OAuth flow
  - [ ] Repository picker UI
  - [ ] Branch selector
  - [ ] Repository configuration page

- [ ] **Database Schema**
  - [ ] `github_configs` table (repo_url, branch, access_token_encrypted)
  - [ ] Link la server (one-to-one sau many-to-one)

#### 1.2 GitHub Webhook Receiver
- [ ] **Backend: Webhook Handler**
  - [ ] POST `/api/v1/webhooks/github` endpoint
  - [ ] Signature validation (HMAC-SHA256)
  - [ ] Event filtering (push, pull_request, etc.)
  - [ ] Payload parsing

- [ ] **Deployment Trigger**
  - [ ] Queue sistem pentru deployments (Celery sau similar)
  - [ ] Async job processing
  - [ ] Status tracking (pending, running, success, failed)

#### 1.3 Automatic Deployment
- [ ] **Deployment Service**
  - [ ] Fetch configs from GitHub
  - [ ] Validate YAML/JSON syntax
  - [ ] Backup current configs pe server
  - [ ] Deploy via SSH/SFTP
  - [ ] Restart HA if needed
  - [ ] Rollback pe failure

- [ ] **Deployment History**
  - [ ] Database table: `deployments` (timestamp, commit_sha, status, logs)
  - [ ] UI pentru deployment history
  - [ ] View logs pentru fiecare deployment

---

### **PHASE 2: Enhanced Features** (Q1 2025 în roadmap original)

#### 2.1 Rollback Support
- [ ] **One-Click Rollback**
  - [ ] Store backups (last 10 deployments)
  - [ ] Rollback endpoint API
  - [ ] Frontend rollback button în deployment history
  - [ ] Automatic HA restart after rollback

#### 2.2 Staging Environment
- [ ] **Multi-Environment Support**
  - [ ] Staging vs Production branch mapping
  - [ ] Deploy to staging first
  - [ ] Promote staging → production
  - [ ] Environment-specific variables

#### 2.3 Diff Viewer
- [ ] **Visual Diff Tool**
  - [ ] Monaco Editor sau similar pentru diff view
  - [ ] Side-by-side comparison
  - [ ] Highlight changes (added, removed, modified)
  - [ ] Show diff before deployment

#### 2.4 Enhanced Logging
- [ ] **Structured Logging**
  - [ ] Log aggregation (Loki, ELK stack?)
  - [ ] Search & filter logs
  - [ ] Export logs
  - [ ] Real-time log streaming

#### 2.5 Notification System
- [ ] **Multi-Channel Notifications**
  - [ ] Email notifications (SMTP)
  - [ ] Slack integration
  - [ ] Discord webhooks
  - [ ] Telegram bot
  - [ ] Push notifications (OneSignal?)
  - [ ] Configurable triggers (deployment success/fail, errors, etc.)

---

### **PHASE 3: Enterprise Features** (Q2 2025 în roadmap original)

#### 3.1 RBAC (Role-Based Access Control)
- [ ] **User Roles**
  - [ ] Admin (full access)
  - [ ] Editor (deploy, edit configs)
  - [ ] Viewer (read-only)
  - [ ] Custom roles cu permissions granulare

- [ ] **Permissions System**
  - [ ] Server-level permissions
  - [ ] Action-level permissions (deploy, rollback, edit, view)
  - [ ] Audit trail pentru toate acțiunile

#### 3.2 API Authentication & Rate Limiting
- [ ] **API Keys**
  - [ ] Generate API keys pentru automation
  - [ ] Scope-based API keys (read-only, deploy-only, etc.)
  - [ ] Revoke keys

- [ ] **Rate Limiting**
  - [ ] Prevent abuse
  - [ ] Per-user limits
  - [ ] Per-endpoint limits

#### 3.3 Advanced Monitoring
- [ ] **Metrics Dashboard**
  - [ ] Deployment success rate
  - [ ] Average deployment time
  - [ ] Server uptime tracking
  - [ ] Error rate tracking
  - [ ] Grafana integration?

#### 3.4 Analytics
- [ ] **Usage Analytics**
  - [ ] Most deployed configs
  - [ ] User activity
  - [ ] Server health trends
  - [ ] Cost optimization insights

---

### **PHASE 4: SaaS Platform** (Q3 2025 în roadmap original)

#### 4.1 Cloud-Hosted Version
- [ ] **Multi-Tenancy**
  - [ ] Tenant isolation
  - [ ] Dedicated databases per tenant
  - [ ] Resource quotas

#### 4.2 Subscription Billing
- [ ] **Pricing Tiers**
  - [ ] Free: 1 instance, 10 deployments/month
  - [ ] Hobby: $9/month - 3 instances
  - [ ] Pro: $29/month - 10 instances
  - [ ] Enterprise: Custom pricing

- [ ] **Payment Integration**
  - [ ] Stripe integration
  - [ ] Subscription management
  - [ ] Usage tracking
  - [ ] Invoice generation

#### 4.3 Marketplace
- [ ] **Config Templates**
  - [ ] Pre-made HA configurations
  - [ ] Community contributions
  - [ ] One-click import

#### 4.4 Mobile App
- [ ] **React Native App**
  - [ ] Deployment triggers
  - [ ] Server monitoring
  - [ ] Push notifications
  - [ ] Emergency rollback

---

## 🎯 Prioritizare Recomandată (Pentru Următoarele Sesiuni)

### **Sprint 1: GitHub Integration Basics** (Prioritate 1)
1. ✅ **GitHub OAuth Setup**
2. ✅ **Repository Connection UI**
3. ✅ **Fetch configs from GitHub**
4. ✅ **Manual deployment trigger**

### **Sprint 2: Webhook & Auto-Deploy** (Prioritate 2)
1. ✅ **GitHub webhook receiver**
2. ✅ **Webhook signature validation**
3. ✅ **Automatic deployment on push**
4. ✅ **Deployment queue system**

### **Sprint 3: Validation & Safety** (Prioritate 3)
1. ✅ **Pre-deployment validation**
2. ✅ **Backup before deploy**
3. ✅ **Rollback functionality**
4. ✅ **Deployment history UI**

### **Sprint 4: Monitoring & Notifications** (Prioritate 4)
1. ✅ **Deployment status tracking**
2. ✅ **Email notifications**
3. ✅ **Slack/Discord integration**
4. ✅ **Real-time deployment logs**

---

## 📊 Comparație cu GitHub Original

| Feature | GitHub Original | Implementare Actuală | Status |
|---------|----------------|---------------------|--------|
| **Multi-Instance Management** | ✅ | ✅ | **COMPLET** |
| **SSH Config Sync** | ✅ | ✅ | **COMPLET** |
| **Web Dashboard** | ✅ (Vue 3) | ✅ (Next.js 16) | **COMPLET** (Tech diferit) |
| **REST API** | ✅ | ✅ | **COMPLET** |
| **GitHub Integration** | ✅ | ❌ | **LIPSEȘTE** |
| **Webhook Support** | ✅ | ❌ | **LIPSEȘTE** |
| **Auto Deployment** | ✅ | ❌ | **LIPSEȘTE** |
| **Validation** | ✅ | ⚠️ (Parțial - HA check config) | **PARȚIAL** |
| **Rollback** | ⏳ | ❌ | **PLANIFICAT** |
| **Diff Viewer** | ⏳ | ❌ | **PLANIFICAT** |
| **RBAC** | ⏳ | ❌ | **PLANIFICAT** |
| **Audit Logs** | ⏳ | ✅ (Model există) | **MODEL EXISTĂ** |
| **Notifications** | ⏳ | ❌ | **PLANIFICAT** |

---

## 🚀 Next Steps - Acțiuni Concrete

### **Imediat (Această Săptămână):**
1. **GitHub OAuth Integration**
   - Setup GitHub OAuth App
   - Implement OAuth flow în backend
   - UI pentru conectare repository

2. **Repository Linking**
   - Link servere cu GitHub repos
   - Store encrypted GitHub tokens
   - Fetch file list from repo

3. **Manual Deployment**
   - Deploy configs from GitHub to server
   - Backup before deploy
   - Show deployment status

### **Săptămâna Viitoare:**
1. **Webhook Receiver**
2. **Auto-deployment on push**
3. **Deployment history UI**

### **Luna Viitoare:**
1. **Rollback support**
2. **Notifications (Email + Slack)**
3. **Enhanced logging**

---

## 📝 Notes

**Diferențe față de GitHub Original:**
- ✅ **Am folosit Next.js 16 + React 19** în loc de Vue 3 (mai modern, mai bun pentru SEO)
- ✅ **Am adăugat WebSocket Terminal** (nu era în plan original)
- ✅ **Am implementat Hierarchical File Tree** (îmbunătățire UI semnificativă)
- ✅ **PostgreSQL** în loc de SQLite (production-ready)
- ✅ **Async SQLAlchemy** pentru performanță

**Avantaje Implementare Actuală:**
- Modern tech stack (Python 3.13, Next.js 16, React 19)
- Better type safety (TypeScript + Pydantic)
- Production-ready infrastructure (Docker, PostgreSQL)
- Enhanced security (encrypted credentials, JWT)

**Focus pentru următoarea fază:** GitHub integration este piesa lipsă critică pentru a atinge MVP-ul original!
