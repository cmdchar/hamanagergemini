# 🏠 HA Config Manager

<div align="center">

**Comprehensive Home Assistant Configuration & Device Management Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2+-brightgreen.svg)](https://react.dev)
[![Next.js](https://img.shields.io/badge/Next.js-16.0+-black.svg)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[Features](#-features) •
[Installation](#-installation) •
[Usage](#-usage) •
[Documentation](#-documentation) •
[Contributing](#-contributing)

</div>

---

## 📋 Overview

HA Config Manager is a powerful, enterprise-grade platform for managing Home Assistant deployments and smart home devices. Built with modern technologies, it provides centralized control, automated backups, AI assistance, and comprehensive security features.

### 🎯 What's New (Latest Update)

- **AI File Modification System**: Complete workflow for AI-proposed changes with review, diff viewer, and push controls
- **Diff Viewer UI**: Side-by-side and unified diff views with syntax highlighting for AI modifications
- **Conversation History**: View and resume all past AI conversations with full message history
- **Auto-Sync on Server Add**: Automatically sync all configuration files recursively when adding a new server
- **React 19.2 Frontend**: Complete migration from Vue 3 to modern React with Next.js 16
- **GitHub Integration**: Push AI-generated changes to repositories with PR management
- **Enhanced AI Assistant**: Persistent context awareness with live server file access
- **Deployment History**: Complete audit trail of all deployments and changes
- **WebSocket Terminal**: Real-time command execution and log streaming

### Why HA Config Manager?

- 🚀 **Automated Deployment**: Deploy Home Assistant instances with one click
- 🤖 **AI Assistant**: Natural language control with Deepseek AI + file modification tracking
- 🔐 **Enterprise Security**: AES-256-GCM encryption, audit logs, security events
- 💾 **Smart Backups**: Automated Node-RED & Zigbee2MQTT backups with scheduling
- 📡 **Device Management**: Control WLED, FPP, ESPHome devices from one interface
- 🔄 **OTA Updates**: Wireless firmware updates for ESP32/ESP8266 devices
- 📤 **GitHub Ready**: Deploy changes directly to repositories with automated PRs
- 📊 **Complete Audit Trail**: Track every system operation for compliance

---

## ✨ Features

### 🏗️ Infrastructure Management
- **Server Management**: SSH-based remote server control
- **Deployment Automation**: PM2-based Home Assistant deployment
- **Health Monitoring**: Real-time status tracking for all resources
- **Configuration Management**: Centralized config storage and versioning

### 🔌 Device Integrations
- **WLED**: LED strip control with presets and schedules
- **FPP (Falcon Player)**: Christmas light show automation
- **ESPHome**: mDNS discovery and OTA firmware updates
- **Tailscale**: VPN management and device tracking
- **Node-RED**: Flow backup and restore
- **Zigbee2MQTT**: Configuration and database backups

### 🤖 AI & Automation
- **AI Assistant**: Chat interface powered by Deepseek AI with persistent context
- **Conversation Management**: View, resume, and manage all past AI conversations
  - **Pin/Unpin**: Keep important conversations at the top
  - **Archive**: Organize conversations by archiving completed ones
  - **Soft Delete**: Remove conversations from view while preserving history
  - Auto-Naming: Intelligent conversation titling based on content
- **AI Tools Framework**: Extensible system for AI-executed scripts
  - **Script Execution**: AI can run custom scripts (Python/Bash) for system tasks
  - **Secure Sandbox**: Scripts run in restricted directory with validated arguments
  - **Extensible Registry**: Easy addition of new tools via @ai_tool decorator
- **File Modification Workflow**: Complete system for AI-proposed changes
  - AI proposes changes in standardized format
  - User reviews changes in diff viewer (unified/split view)
  - Approve/Reject workflow with comments
  - Push to Server and/or GitHub with tracking
- **Diff Viewer**: Side-by-side and unified views with syntax highlighting
- **Live Server Access**: AI sees actual files on server via SSH in real-time
- **Auto-sync**: Recursive file sync when adding servers
- **Action Execution**: AI can create servers, deploy HA, modify configs
- **Context Awareness**: Understands current deployment context and file modifications
- **Rollback Support**: Automatic rollback for failed operations
- **Modification History**: Complete audit trail of all AI changes with version tracking

### 💾 Backup & Restore
- **Scheduled Backups**: Cron-based automation with retention policies
- **Compression**: Tar.gz archives with SHA256 verification
- **Smart Restore**: Pre-restore backups for safe rollback
- **Multiple Sources**: Node-RED flows, Zigbee2MQTT configs, HA snapshots

### 🔐 Security & Compliance
- **Secrets Management**: AES-256-GCM encryption with PBKDF2 (100k iterations)
- **Automatic Rotation**: Configurable rotation intervals
- **Audit Logging**: System-wide operation tracking
- **Security Events**: Incident detection and response workflows
- **Compliance Ready**: GDPR, SOC2 compliance tags
- **Audit Trails**: Complete tracking of AI modifications and system changes

### 🔄 GitHub Integration
- **Push to Repository**: Deploy modified files directly to GitHub
- **PR Management**: Create pull requests from AI-generated changes
- **Deployment History**: Track all deployments with commit history
- **Webhook Support**: GitHub webhooks for automated triggers
- **CI/CD Integration**: Connect to deployment pipelines

### 📊 Monitoring & Analytics
- **Real-time Status**: Live device and deployment monitoring
- **Statistics Dashboards**: Comprehensive metrics and insights
- **Log Streaming**: WebSocket-based real-time logs
- **Resource Tracking**: CPU, memory, disk usage monitoring

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 14+ with asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **Authentication**: JWT tokens with bcrypt
- **Task Scheduling**: APScheduler (cron support)
- **Encryption**: Cryptography library (Fernet)
- **AI**: Deepseek API integration

### Frontend
- **Framework**: React 19.2 (latest)
- **UI Library**: shadcn/ui (Tailwind CSS)
- **State Management**: Zustand with TypeScript
- **Language**: TypeScript 5.0+
- **Build Tool**: Vite with Next.js 16.0+
- **HTTP Client**: Axios
- **Styling**: Tailwind CSS with custom components
- **Real-time**: WebSocket support for live logs and events

### DevOps
- **Containerization**: Docker & Docker Compose
- **Process Manager**: PM2
- **Migrations**: Alembic
- **API Docs**: OpenAPI/Swagger

---

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- PostgreSQL 14 or higher
- Docker (optional, for containerized deployment)

### Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/cmdchar/ha-config-manager.git
cd ha-config-manager
```

#### 2. Backend Setup

```bash
cd orchestrator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://haconfig:password@localhost/haconfig
SECRET_KEY=your-super-secret-jwt-key-change-in-production
SECRETS_MASTER_KEY=your-encryption-master-key-change-in-production
DEEPSEEK_API_KEY=your-deepseek-api-key
EOF

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

#### 3. Frontend Setup

```bash
cd dashboard

# Install dependencies
npm install

# Create .env file
cat > .env << EOF
VITE_API_BASE_URL=http://localhost:8000/api/v1
EOF

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

#### 4. Database Setup

```bash
# Create PostgreSQL database
createdb haconfig

# Or using psql
psql -U postgres -c "CREATE DATABASE haconfig;"
psql -U postgres -c "CREATE USER haconfig WITH PASSWORD 'password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE haconfig TO haconfig;"
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Docker Compose Services:**
- `postgres`: PostgreSQL database
- `backend`: FastAPI application (port 8000)
- `frontend`: Vue 3 application (port 3000)

---

## 🚀 Usage

### Initial Setup

1. **Register an Account**
   - Navigate to `http://localhost:3000/register`
   - Create your admin account

2. **Add Your First Server**
   - Go to **Servers** page
   - Click **Add Server**
   - Enter SSH connection details
   - Test connection

3. **Deploy Home Assistant**
   - Go to **Deployments** page
   - Click **New Deployment**
   - Select server, choose HA version
   - Click **Deploy**

### Managing Devices

#### WLED Controllers

```bash
# Add WLED device
POST /api/v1/wled/devices
{
  "name": "Living Room LED",
  "ip_address": "192.168.1.100",
  "port": 80
}

# Control device
POST /api/v1/wled/devices/{id}/state
{
  "on": true,
  "brightness": 128,
  "color": {"r": 255, "g": 0, "b": 0}
}
```

#### ESPHome Devices

```bash
# Discover devices via mDNS
POST /api/v1/esphome/devices/discover
{
  "timeout": 10
}

# Upload firmware OTA
POST /api/v1/esphome/devices/{id}/ota
Content-Type: multipart/form-data
file: firmware.bin
```

### Creating Backups

#### Node-RED Backup

```bash
# Register Node-RED instance
POST /api/v1/backup/nodered/configs
{
  "name": "Main Node-RED",
  "url": "http://192.168.1.50:1880",
  "flows_path": "/data/flows.json"
}

# Create immediate backup
POST /api/v1/backup/nodered/backups
{
  "config_id": 1
}

# Schedule daily backups at 2 AM
POST /api/v1/backup/schedules
{
  "config_id": 1,
  "backup_type": "nodered",
  "cron_expression": "0 2 * * *",
  "retention_days": 30
}
```

### Using AI Assistant

1. Navigate to **AI Assistant** page
2. **Start or Resume Conversation**
   - Click **"New Conversation"** button to start fresh
   - Or select from **past conversations** in the sidebar
   - All message history is preserved and searchable
3. **Ask questions or request actions:**
   - "Create a new server at 192.168.1.100"
   - "Deploy Home Assistant 2024.1 on server-1"
   - "Show me all offline ESPHome devices"
   - "Modify my configuration.yaml to add MQTT integration"
   - "Update automations.yaml with a motion sensor trigger"
4. **Review AI-Proposed Changes**
   - AI detects when it wants to modify files
   - Toast notification appears: "AI created 1 file modification. Review in AI Modifications."
   - Click **"Review"** to see the changes
5. **Review in Diff Viewer**
   - Navigate to **AI Modifications** page
   - See all pending, approved, and rejected changes
   - Click on modification to view **BEFORE/AFTER diff**
   - Toggle between **Unified** and **Split** view
   - Read AI's explanation of changes
6. **Approve/Reject**
   - Add optional review comment
   - Click **"Approve"** or **"Reject"**
7. **Push Changes** (if approved)
   - Choose **Push to Server** and/or **Push to GitHub**
   - Add commit message for GitHub
   - Track push status and commit SHA

#### AI File Modifications Tracking

The system tracks all AI-generated code changes with full history:

```bash
# Get AI file modifications
GET /api/v1/ai-files/modifications?limit=20

# View specific modification details
GET /api/v1/ai-files/modifications/{id}
# Returns: diff, content before/after, timestamp, AI reasoning

# Track modification status
GET /api/v1/ai-files/modifications/{id}/status
# Status: pending, applied, failed, reverted

# Revert a modification
POST /api/v1/ai-files/modifications/{id}/revert
{
  "reason": "Does not match requirements"
}
```

#### GitHub Integration

Deploy AI-generated changes directly to GitHub:

```bash
# Get GitHub deployment history
GET /api/v1/github/deployments?limit=10

# Create PR from AI modifications
POST /api/v1/github/create-pr
{
  "modification_ids": [1, 2, 3],
  "title": "AI-generated Home Assistant config updates",
  "description": "Automated configuration changes from AI Assistant",
  "target_branch": "main"
}

# Sync with GitHub
POST /api/v1/github/sync
{
  "action": "pull"  # or "push"
}

# Setup webhook for automatic deployments
POST /api/v1/webhooks/github
{
  "event": "push",
  "branch": "main",
  "actions": ["deploy", "restart"]
}
```

### Managing Secrets

```bash
# Create encrypted secret
POST /api/v1/security/secrets
{
  "name": "mqtt_password",
  "value": "super-secret-password",
  "secret_type": "password",
  "rotation_interval_days": 90
}

# Decrypt secret (creates audit log)
GET /api/v1/security/secrets/{id}/decrypt

# Rotate secret
POST /api/v1/security/secrets/{id}/rotate
{
  "new_value": "new-super-secret-password"
}

# Revoke secret
POST /api/v1/security/secrets/{id}/revoke
{
  "reason": "Compromised in security incident"
}
```

### Viewing Audit Logs

```bash
# Search audit logs with filters
POST /api/v1/security/audit-logs/search
{
  "category": "secret",
  "severity": "critical",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z"
}

# Get security events
GET /api/v1/security/security-events?unresolved_only=true

# Resolve security event
POST /api/v1/security/security-events/{id}/resolve
{
  "response_status": "resolved",
  "response_notes": "False alarm, legitimate access"
}
```

---

## 📚 Documentation

### Complete Documentation

- **[Implementation Documentation](IMPLEMENTATION_DOCUMENTATION.md)**: Detailed architecture, implementation steps, and code structure
- **[API Documentation](http://localhost:8000/docs)**: Interactive Swagger UI (when backend is running)

### Key Concepts

#### Deployment Lifecycle

```
Create → Configure → Deploy → Monitor → Update → Backup → Restore
```

1. **Create**: Add server with SSH credentials
2. **Configure**: Set HA version, port, domain
3. **Deploy**: Automated installation with PM2
4. **Monitor**: Real-time status and logs
5. **Update**: Version upgrades
6. **Backup**: Automated configuration backups
7. **Restore**: Rollback to previous state

#### Security Model

- **Encryption at Rest**: All secrets encrypted with AES-256-GCM
- **Authentication**: JWT tokens with configurable expiry
- **Authorization**: Permission-based access control
- **Audit Trail**: Every operation logged with user, timestamp, changes
- **Security Events**: Automated incident detection (unauthorized access, brute force, etc.)

#### Backup Strategy

- **3-2-1 Rule**: 3 copies, 2 different media, 1 offsite (implement offsite manually)
- **Retention**: Configurable per schedule (default: 30 days)
- **Verification**: SHA256 checksums for all backups
- **Restoration**: Automatic pre-restore backup for rollback

---

## 🏗️ Project Structure

```
ha-config-manager/
├── orchestrator/              # Backend API
│   ├── app/
│   │   ├── api/              # REST API endpoints
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── servers.py
│   │   │       ├── deployments.py
│   │   │       ├── wled.py
│   │   │       ├── esphome.py
│   │   │       ├── backup.py
│   │   │       ├── ai.py                    # AI Assistant API
│   │   │       ├── ai_files.py              # AI File Modifications
│   │   │       ├── github.py                # GitHub Integration
│   │   │       ├── webhooks.py              # Webhook handlers
│   │   │       ├── ha_config.py             # HA Config Management
│   │   │       ├── terminal.py              # WebSocket terminal
│   │   │       └── security.py
│   │   ├── models/           # SQLAlchemy models
│   │   │   ├── ai_context.py                # AI Context
│   │   │   ├── ai_file_modification.py      # File changes
│   │   │   ├── audit_log.py                 # Audit logs
│   │   │   └── ...
│   │   ├── schemas/          # Pydantic schemas
│   │   │   ├── ai_file_modification.py
│   │   │   ├── github.py
│   │   │   └── ...
│   │   ├── services/         # Business logic
│   │   │   ├── ai_chat_service.py           # AI handling
│   │   │   ├── ai_context_service.py        # Context
│   │   │   ├── github_deployment_service.py # GitHub
│   │   │   └── ...
│   │   ├── integrations/     # External APIs
│   │   │   ├── deepseek.py
│   │   │   └── ...
│   │   ├── utils/
│   │   │   ├── ssh.py
│   │   │   └── ...
│   │   ├── core/
│   │   └── main.py
│   ├── alembic/
│   └── requirements.txt
│
├── dashboard-react/           # Frontend (React 19.2)
│   ├── app/
│   │   ├── (dashboard)/
│   │   │   ├── ai-assistant/     # AI Chat
│   │   │   ├── ai-modifications/ # AI Changes
│   │   │   ├── github/           # GitHub UI
│   │   │   ├── deployment-history/
│   │   │   ├── servers/
│   │   │   ├── esphome/
│   │   │   ├── wled/
│   │   │   └── layout.tsx
│   │   ├── login/
│   │   ├── register/
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ai-chat-bubble.tsx
│   │   ├── diff-viewer.tsx
│   │   ├── app-sidebar.tsx
│   │   ├── forms/
│   │   ├── ui/
│   │   └── ...
│   ├── hooks/
│   ├── store/
│   ├── lib/
│   ├── package.json
│   └── tsconfig.json
│
├── docker-compose.yml
├── IMPLEMENTATION_DOCUMENTATION.md
└── README.md
```

---

## 🧪 Development

### Running Tests

```bash
# Backend tests
cd orchestrator
pytest

# Frontend tests
cd dashboard
npm run test

# E2E tests
npm run test:e2e
```

### Code Quality

```bash
# Backend linting
cd orchestrator
flake8 app/
black app/
mypy app/

# Frontend linting
cd dashboard
npm run lint
npm run type-check
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

---

## 🔧 Configuration

### Environment Variables

#### Backend (`orchestrator/.env`)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/haconfig

# Security
SECRET_KEY=your-jwt-secret-key
SECRETS_MASTER_KEY=your-encryption-master-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External Services
DEEPSEEK_API_KEY=your-deepseek-api-key

# Application
DEBUG=false
LOG_LEVEL=info
```

#### Frontend (`dashboard/.env`)

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Application
VITE_APP_TITLE=HA Config Manager
VITE_APP_VERSION=1.0.0
```

---

## 📊 Project Statistics

- **Total Lines of Code**: ~20,500
- **Backend**: ~11,000 lines (Python)
- **Frontend**: ~9,500 lines (TypeScript/Vue)
- **Files**: ~70 files
- **Integrations**: 7 major integrations
- **API Endpoints**: 100+ endpoints
- **Database Tables**: 25+ tables
- **Development Time**: 25 weeks (3 phases)

### Phase Breakdown

| Phase | Weeks | Lines | Focus |
|-------|-------|-------|-------|
| Phase 1 | 1-8 | ~6,000 | Infrastructure (Servers, Deployments, WLED, FPP, Tailscale) |
| Phase 2 | 9-16 | ~3,500 | Advanced Integrations (Snapshots, Enhancements) |
| Phase 3 | 17-25 | 11,016 | Advanced Features (AI, ESPHome, Backups, Security) |

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/ha-config-manager.git
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make Your Changes**
   - Follow existing code style
   - Add tests for new features
   - Update documentation

4. **Commit Your Changes**
   ```bash
   git commit -m "Add amazing feature"
   ```

5. **Push to Your Fork**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Open a Pull Request**
   - Describe your changes
   - Reference any related issues
   - Wait for review

### Development Guidelines

- **Code Style**: Follow PEP 8 (Python) and Airbnb style guide (JavaScript/TypeScript)
- **Testing**: Maintain >80% code coverage
- **Documentation**: Update docs for new features
- **Commits**: Use conventional commits (feat, fix, docs, etc.)

---

## 🐛 Troubleshooting

### Common Issues

#### Backend won't start

```bash
# Check database connection
psql -U haconfig -d haconfig -c "SELECT 1;"

# Verify migrations
alembic current
alembic upgrade head

# Check logs
tail -f logs/app.log
```

#### Frontend can't connect to API

```bash
# Verify backend is running
curl http://localhost:8000/api/v1/health

# Check CORS settings in backend
# Ensure VITE_API_BASE_URL is correct in .env
```

#### Database migration errors

```bash
# Reset database (CAUTION: destroys data)
alembic downgrade base
alembic upgrade head

# Or recreate database
dropdb haconfig
createdb haconfig
alembic upgrade head
```

#### Docker issues

```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# View container logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI**: For the amazing async web framework
- **Vue.js**: For the reactive frontend framework
- **Vuetify**: For the beautiful Material Design components
- **Home Assistant**: For the inspiration and integration opportunities
- **Deepseek**: For the AI capabilities
- **Community**: For all the feedback and contributions

---

## 📞 Support

- **Documentation**: [IMPLEMENTATION_DOCUMENTATION.md](IMPLEMENTATION_DOCUMENTATION.md)
- **Issues**: [GitHub Issues](https://github.com/cmdchar/ha-config-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cmdchar/ha-config-manager/discussions)

---

## 🗺️ Roadmap

### Completed ✅
- [x] Phase 1: Infrastructure (Servers, Deployments, Basic Integrations)
- [x] Phase 2: Advanced Integrations
- [x] Phase 3: Advanced Features (AI, ESPHome, Backups, Security)

### In Progress 🚧
- [ ] Comprehensive Testing Suite
- [ ] Production Hardening (Security, Performance, Monitoring)
- [ ] User Documentation & Tutorials

### Planned 📋
- [ ] **PWA (Progressive Web App)** - Transform Vue 3 app into installable PWA
  - [ ] Service Workers for offline functionality
  - [ ] Web App Manifest
  - [ ] Push notifications
  - [ ] Add to Home Screen
- [ ] RBAC (Role-Based Access Control)
- [ ] Multi-tenancy support
- [ ] Advanced Analytics Dashboard
- [ ] Webhook integrations
- [ ] SSO (OAuth2/SAML)
- [ ] High Availability setup
- [ ] Kubernetes deployment manifests

---

<div align="center">

**Built with ❤️ for the Home Assistant community**

[⬆ Back to Top](#-ha-config-manager)

</div>
