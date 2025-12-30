# Development Guide

## 🛠️ Setting Up Development Environment

### Prerequisites

- Python 3.11+
- Node.js 18+ (for dashboard development)
- Docker & Docker Compose
- Git
- Home Assistant instance for testing

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/cmdchar/ha-config-manager.git
cd ha-config-manager

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements-dev.txt

# 4. Install pre-commit hooks
pre-commit install

# 5. Copy environment file
cp .env.example .env

# 6. Edit configuration
nano .env
```

---

## 📁 Project Structure

```
ha-config-manager/
├── addon/                      # Home Assistant Add-on
│   ├── config.yaml            # Add-on configuration
│   ├── Dockerfile             # Container image
│   ├── requirements.txt       # Python dependencies
│   ├── rootfs/
│   │   └── usr/bin/
│   │       └── ha-sync.py    # Main add-on script
│   └── README.md
│
├── orchestrator/               # Backend API Server
│   ├── main.py                # FastAPI application
│   ├── api/                   # API routes
│   │   ├── __init__.py
│   │   ├── servers.py         # Server management
│   │   ├── deployments.py     # Deployment endpoints
│   │   └── webhooks.py        # GitHub webhooks
│   ├── models/                # Pydantic models
│   │   ├── __init__.py
│   │   ├── server.py
│   │   └── deployment.py
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── deployment.py      # Deployment service
│   │   └── github.py          # GitHub integration
│   ├── database/              # Database layer
│   │   ├── __init__.py
│   │   └── models.py
│   ├── config.py              # Configuration
│   ├── requirements.txt
│   └── Dockerfile
│
├── dashboard/                  # Frontend UI
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/        # Vue components
│   │   ├── views/             # Page views
│   │   ├── store/             # State management
│   │   ├── api/               # API client
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
│
├── docs/                       # Documentation
│   ├── INSTALLATION.md
│   ├── CONFIGURATION.md
│   ├── API.md
│   ├── DEVELOPMENT.md
│   └── DEPLOYMENT.md
│
├── tests/                      # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .github/                    # GitHub workflows
│   └── workflows/
│       ├── ci.yml
│       ├── tests.yml
│       └── release.yml
│
├── docker-compose.yml          # Development environment
├── docker-compose.prod.yml     # Production environment
├── Makefile                    # Common commands
├── .env.example                # Environment template
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🔧 Development Workflow

### Branch Strategy

```
main (protected)
├── develop
│   ├── feature/webhook-auth
│   ├── feature/rollback-support
│   └── bugfix/deployment-timeout
└── hotfix/critical-bug
```

### Creating a Feature

```bash
# 1. Create branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# 2. Make changes and commit
git add .
git commit -m "feat: add awesome feature"

# 3. Push and create PR
git push origin feature/your-feature-name
```

### Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add rollback support
fix: resolve deployment timeout issue
docs: update installation guide
test: add integration tests for webhooks
chore: update dependencies
refactor: improve deployment service
```

---

## 🧪 Testing

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit

# Run specific test file
pytest tests/unit/test_deployment.py

# Run with coverage
pytest --cov=orchestrator tests/unit
```

### Integration Tests

```bash
# Requires Docker
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration

# Cleanup
docker-compose -f docker-compose.test.yml down
```

### End-to-End Tests

```bash
# Start full environment
docker-compose up -d

# Run E2E tests
pytest tests/e2e

# Or use Playwright for UI tests
npx playwright test
```

---

## 🐛 Debugging

### Orchestrator (Backend)

```bash
# Run with debugger
python -m debugpy --listen 5678 orchestrator/main.py

# Or use VS Code launch configuration
# See .vscode/launch.json
```

### Add-on

```bash
# Run locally (simulate add-on environment)
export GITHUB_REPO="cmdchar/ha-config"
export GITHUB_TOKEN="your_token"
export SERVER_ID="test-server"

python addon/rootfs/usr/bin/ha-sync.py
```

### Dashboard

```bash
cd dashboard
npm run dev  # Vite dev server with hot reload
```

---

## 📝 Code Style

### Python

We use:
- **Black** for formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
black orchestrator/ addon/

# Sort imports
isort orchestrator/ addon/

# Lint
flake8 orchestrator/ addon/

# Type check
mypy orchestrator/
```

### JavaScript/Vue

```bash
cd dashboard

# Format
npm run format

# Lint
npm run lint

# Type check
npm run type-check
```

---

## 🔄 Making Changes

### Adding a New API Endpoint

1. **Create route in `orchestrator/api/`**:

```python
# orchestrator/api/servers.py
from fastapi import APIRouter, HTTPException
from models.server import Server

router = APIRouter(prefix="/servers", tags=["servers"])

@router.get("/{server_id}")
async def get_server(server_id: str):
    # Implementation
    pass
```

2. **Add to main app**:

```python
# orchestrator/main.py
from api.servers import router as servers_router

app.include_router(servers_router)
```

3. **Write tests**:

```python
# tests/unit/api/test_servers.py
def test_get_server():
    # Test implementation
    pass
```

### Adding a New Feature to Add-on

1. **Update script**:

```python
# addon/rootfs/usr/bin/ha-sync.py
def new_feature():
    # Implementation
    pass
```

2. **Update configuration**:

```yaml
# addon/config.yaml
schema:
  new_option: str
```

3. **Document in README**:

```markdown
# addon/README.md
## New Feature

Description of the new feature...
```

---

## 🚀 Local Development Environment

### Full Stack Development

```bash
# Terminal 1: Orchestrator
cd orchestrator
uvicorn main:app --reload --port 8080

# Terminal 2: Dashboard
cd dashboard
npm run dev

# Terminal 3: Test HA Add-on
cd addon
python rootfs/usr/bin/ha-sync.py
```

### Using Docker Compose

```bash
# Start all services
docker-compose up

# View logs
docker-compose logs -f orchestrator

# Rebuild after changes
docker-compose up --build

# Stop all
docker-compose down
```

---

## 📦 Building

### Build Add-on

```bash
cd addon
docker build -t ha-config-sync:dev .
```

### Build Orchestrator

```bash
cd orchestrator
docker build -t ha-config-orchestrator:dev .
```

### Build Dashboard

```bash
cd dashboard
npm run build
# Output in dashboard/dist/
```

---

## 🔐 Environment Variables

### Development `.env`

```bash
# Orchestrator
API_HOST=0.0.0.0
API_PORT=8080
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./test.db

# GitHub
GITHUB_WEBHOOK_SECRET=dev-secret-change-in-prod

# Dashboard
VITE_API_URL=http://localhost:8080
```

### Production `.env`

```bash
# Orchestrator
API_HOST=0.0.0.0
API_PORT=8080
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@db:5432/haconfig

# GitHub
GITHUB_WEBHOOK_SECRET=<secure-random-secret>

# Security
API_SECRET_KEY=<long-random-secret>
ALLOWED_ORIGINS=https://dashboard.example.com

# Dashboard
VITE_API_URL=https://api.example.com
```

---

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vue 3 Documentation](https://vuejs.org/)
- [Home Assistant Add-on Development](https://developers.home-assistant.io/docs/add-ons)
- [Docker Documentation](https://docs.docker.com/)
- [pytest Documentation](https://docs.pytest.org/)

---

## 🤝 Getting Help

- Check existing [GitHub Issues](https://github.com/cmdchar/ha-config-manager/issues)
- Join [Discussions](https://github.com/cmdchar/ha-config-manager/discussions)
- Read the [FAQ](docs/FAQ.md)

---

## ✅ Pre-Release Checklist

Before creating a PR:

- [ ] All tests pass (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] No linting errors (`make lint`)
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Commit messages follow convention
- [ ] Branch is up to date with develop

---

Happy coding! 🎉
