# HA Config Sync Add-on

Sincronizare automată a configurațiilor Home Assistant din GitHub.

## Features

- ✅ Auto-sync din GitHub (interval configurabil)
- ✅ Manual sync prin API
- ✅ Validare configurații înainte de restart
- ✅ Webhook support pentru deployment instant
- ✅ Notificări către orchestrator
- ✅ Web UI pentru monitoring
- ✅ Multi-instance support

## Installation

### Method 1: Manual (Development)

1. Copiază folder-ul `ha-config-sync-addon` în `/addons/`
2. Restart Home Assistant
3. Supervisor → Add-on Store → Local Add-ons
4. Instalează "HA Config Sync"

### Method 2: HACS (Production - Coming Soon)

1. HACS → Integrations → "HA Config Sync"
2. Install

## Configuration

```yaml
github_repo: "cmdchar/ha-config"
github_token: "ghp_YOUR_TOKEN"
github_branch: "main"
server_id: "server-1"
orchestrator_url: "http://orchestrator:8080"
auto_sync: true
sync_interval: 300
config_path: "/ha-config"
```

## API Endpoints

- `GET /api/status` - Status add-on
- `POST /api/sync` - Trigger manual sync
- `POST /api/webhook` - GitHub webhook receiver
- `GET /health` - Health check

## Usage

### Automatic Sync

Add-on-ul va sincroniza automat la fiecare `sync_interval` secunde.

### Manual Sync

```bash
curl -X POST http://YOUR_HA_IP:8099/api/sync
```

### Via Orchestrator

Deployment-ul poate fi trigger din Dashboard sau prin API.

## Logs

Verifică logs în:
- Supervisor → HA Config Sync → Logs
- `/config/ha-config-sync.log`

## Support

GitHub: https://github.com/cmdchar/ha-config-sync
