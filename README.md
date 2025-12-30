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

### Why HA Config Manager?

- 🚀 **Automated Deployment**: Deploy Home Assistant instances with one click
- 🤖 **AI Assistant**: Natural language control with Deepseek AI integration
- 🔐 **Enterprise Security**: AES-256-GCM encryption, audit logs, security events
- 💾 **Smart Backups**: Automated Node-RED & Zigbee2MQTT backups with scheduling
- 📡 **Device Management**: Control WLED, FPP, ESPHome devices from one interface
- 🔄 **OTA Updates**: Wireless firmware updates for ESP32/ESP8266 devices
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
- **AI Assistant**: Chat interface powered by Deepseek AI
- **Action Execution**: AI can create servers, deploy HA, modify configs
- **Context Awareness**: Understands current deployment context
- **Rollback Support**: Automatic rollback for failed operations

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
- **Framework**: Vue 3 (Composition API)
- **UI Library**: Vuetify 3 (Material Design)
- **State Management**: Pinia
- **Language**: TypeScript
- **Build Tool**: Vite
- **HTTP Client**: Axios

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
2. Start a conversation
3. Ask questions or request actions:
   - "Create a new server at 192.168.1.100"
   - "Deploy Home Assistant 2024.1 on server-1"
   - "Show me all offline ESPHome devices"
4. Review suggested actions
5. Confirm to execute

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
│   │   │       ├── ai.py
│   │   │       └── security.py
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── integrations/     # External integrations
│   │   ├── core/             # Config, security, deps
│   │   └── main.py           # FastAPI application
│   ├── alembic/              # Database migrations
│   └── requirements.txt
│
├── dashboard/                 # Frontend application
│   ├── src/
│   │   ├── views/            # Page components
│   │   ├── stores/           # Pinia stores
│   │   ├── components/       # Reusable components
│   │   ├── router/           # Vue Router
│   │   ├── services/         # API client
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml         # Docker orchestration
├── IMPLEMENTATION_DOCUMENTATION.md  # Detailed docs
└── README.md                  # This file
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
