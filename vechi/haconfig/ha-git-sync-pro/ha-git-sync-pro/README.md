# HA Git Sync Pro

**Enterprise-grade GitHub synchronization for Home Assistant**

Sincronizează automat configurațiile tale de Home Assistant, ESPHome, Node-RED, Zigbee2MQTT și multe altele direct din GitHub.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🚀 Features

### Core Features
- **Git Integration**: Clone, pull, push automat din/către GitHub, GitLab, Bitbucket
- **Webhook Support**: Sync instant când faci push pe GitHub
- **Multi-Target Sync**: Sincronizează separat HA, ESPHome, Node-RED, etc.
- **Backup System**: Backup automat înainte de fiecare sync
- **Validation**: Validează configurațiile YAML înainte de aplicare
- **Auto-Restart**: Restart automat servicii după modificări

### Supported Targets
| Target | Path | Auto-Restart | Validation |
|--------|------|--------------|------------|
| Home Assistant | `/config` | ✅ | ✅ |
| ESPHome | `/config/esphome` | ✅ | ✅ |
| Node-RED | `/share/nodered` | ✅ | ✅ |
| Zigbee2MQTT | `/share/zigbee2mqtt` | ✅ | ✅ |
| Mosquitto | `/share/mosquitto` | ✅ | ❌ |
| Custom Components | `/config/custom_components` | ✅ | ❌ |
| Themes | `/config/themes` | ❌ | ❌ |
| WWW/Lovelace | `/config/www` | ❌ | ❌ |
| Scripts | `/config/scripts` | ✅ | ✅ |
| Automations | `/config/automations` | ✅ | ✅ |
| Blueprints | `/config/blueprints` | ❌ | ❌ |

### Advanced Features
- **Multi-Device Mode**: Sincronizează mai multe instanțe HA din același repo
- **MQTT Integration**: Publică status și primește comenzi via MQTT
- **Scheduled Sync**: Pull automat la intervale configurabile
- **Web Dashboard**: Interfață grafică completă pentru management
- **Notifications**: Notificări în HA la sync/erori
- **Dry Run Mode**: Testează modificările fără a le aplica

## 📦 Installation

### Method 1: Add Repository
1. În Home Assistant, mergi la **Settings** → **Add-ons** → **Add-on Store**
2. Click pe menu (⋮) → **Repositories**
3. Adaugă URL-ul: `https://github.com/your-repo/ha-addons`
4. Găsește "HA Git Sync Pro" și instalează

### Method 2: Manual Installation
1. Copiază folder-ul `ha-git-sync-pro` în `/addons/`
2. Refresh Add-on Store
3. Instalează add-on-ul

## ⚙️ Configuration

### Basic Configuration
```yaml
git_repository: "https://github.com/username/ha-config"
git_branch: "main"
git_username: "your-username"
git_token: "ghp_xxxxxxxxxxxx"  # GitHub Personal Access Token
```

### Repository Structure
Structura recomandată pentru repo:

```
your-ha-config/
├── ha-config/              # Home Assistant configs
│   ├── configuration.yaml
│   ├── automations.yaml
│   ├── scripts.yaml
│   └── secrets.yaml        # Va fi exclus automat!
├── esphome/                # ESPHome configs
│   ├── living-room.yaml
│   └── bedroom.yaml
├── nodered/                # Node-RED flows
│   └── flows.json
├── zigbee2mqtt/           # Zigbee2MQTT config
│   └── configuration.yaml
├── custom_components/     # Custom integrations
│   └── my_integration/
├── themes/                # Themes
│   └── my-theme.yaml
└── www/                   # Lovelace resources
    └── custom-cards/
```

### Multi-Device Setup
Pentru sincronizarea mai multor instanțe HA:

```yaml
multi_device_mode: true
device_id: "living-room-ha"
device_folder: "devices/living-room"
```

Structura repo:
```
your-ha-config/
├── devices/
│   ├── living-room/
│   │   ├── ha-config/
│   │   └── esphome/
│   ├── bedroom/
│   │   ├── ha-config/
│   │   └── esphome/
│   └── garage/
│       └── ha-config/
└── shared/                # Configs comune
    └── custom_components/
```

### Webhook Setup
1. În GitHub, mergi la repo → **Settings** → **Webhooks**
2. **Payload URL**: `http://your-ha-ip:9877/webhook/github`
3. **Content type**: `application/json`
4. **Secret**: Same as `webhook_secret` în config
5. **Events**: Just the push event

### Full Configuration Options

```yaml
# Git Configuration
git_repository: ""           # Repository URL (required)
git_branch: "main"           # Branch to sync
git_username: ""             # Git username
git_token: ""                # Personal access token
git_auto_pull: true          # Enable automatic pulling
git_pull_interval: 300       # Pull interval in seconds (60-3600)
git_auto_commit: false       # Auto-commit local changes
git_commit_message: "Auto-commit from HA Git Sync Pro"

# Webhook Configuration
webhook_enabled: true
webhook_secret: ""           # GitHub webhook secret
webhook_port: 9877

# Sync Targets - customize what to sync
sync_targets:
  - name: "homeassistant"
    enabled: true
    source_path: "/ha-config"
    dest_path: "/config"
    restart_on_change: true
    validate_before_apply: true
    
  - name: "esphome"
    enabled: true
    source_path: "/esphome"
    dest_path: "/config/esphome"
    compile_on_change: false

# Backup Configuration
backup_enabled: true
backup_before_sync: true
backup_retention_days: 7
backup_path: "/backup/git-sync"

# Notifications
notify_on_sync: true
notify_on_error: true
notify_service: "persistent_notification"

# Advanced
dry_run: false              # Test mode - don't apply changes
verbose_logging: false
exclude_patterns:           # Files to never sync
  - "*.log"
  - "*.db"
  - "__pycache__"
  - ".git"
  - "secrets.yaml"
  - "home-assistant_v2.db*"

# Multi-Device Mode
device_id: ""               # Unique device identifier
device_folder: ""           # Folder in repo for this device
multi_device_mode: false

# Security
encrypt_secrets: false
secrets_key: ""

# Web UI
web_ui_enabled: true
web_ui_port: 9876
web_ui_auth: true
```

## 🖥️ Web Dashboard

Accesează dashboard-ul la `http://your-ha-ip:9876` sau prin Ingress în HA.

### Features
- **Repository Status**: Vezi branch-ul curent, ultimul commit, status
- **Sync Targets**: Management individual per target
- **Recent Commits**: Istoricul ultimelor commit-uri
- **System Health**: Status componente sistem
- **Scheduled Jobs**: Vezi și controlează job-urile programate
- **Backups**: Creează, restaurează, șterge backup-uri
- **Sync History**: Istoricul tuturor operațiunilor de sync

## 🔗 MQTT Integration

Publică automat pe MQTT:
- `ha-git-sync/status` - Online/offline status
- `ha-git-sync/sync/result` - Rezultate sync
- `ha-git-sync/heartbeat` - Heartbeat periodic

Comenzi via MQTT:
- `ha-git-sync/command/sync` - Trigger sync
- `ha-git-sync/command/pull` - Trigger pull

### Home Assistant Discovery
Add-on-ul publică automat configurație MQTT Discovery pentru:
- Binary sensor pentru status conexiune
- Sensor pentru ultimul sync
- Sensor pentru fișiere modificate
- Button pentru trigger sync

## 🛡️ Security

### Best Practices
1. **Nu stoca `secrets.yaml` în repo** - e exclus automat
2. **Folosește GitHub Personal Access Token** cu permisiuni minime (repo only)
3. **Setează webhook secret** pentru a preveni trigger-e neautorizate
4. **Activează `encrypt_secrets`** pentru fișiere sensibile

### Token Permissions
GitHub PAT necesită doar:
- `repo` - Full control of private repositories

## 📊 Monetization Ideas

Dacă vrei să monetizezi acest add-on:

### Freemium Model
- **Free**: 1 target, manual sync, basic backup
- **Pro ($5/mo)**: Unlimited targets, auto-sync, webhooks
- **Enterprise ($15/mo)**: Multi-device, priority support, custom integrations

### Features pentru versiunea plătită:
- Multi-device sync
- ESPHome auto-compile
- Slack/Discord notifications
- Advanced diff viewer
- Configuration versioning
- Rollback to any commit
- Team collaboration
- Custom webhook integrations

## 🐛 Troubleshooting

### Common Issues

**Git clone fails**
- Verifică URL-ul repository-ului
- Verifică token-ul (trebuie să aibă permisiuni `repo`)
- Pentru repo private, asigură-te că username-ul e corect

**Webhook not triggering**
- Verifică că portul 9877 e accesibil
- Verifică secret-ul în GitHub matches config
- Check webhook deliveries în GitHub

**Sync fails validation**
- Check logs pentru erori YAML specifice
- Folosește `dry_run: true` pentru a testa

**Services not restarting**
- Verifică că add-on-ul are `hassio_api: true`
- Check SUPERVISOR_TOKEN e setat

### Logs
```bash
# În SSH/Terminal
docker logs addon_local_ha-git-sync-pro

# Sau în UI
Settings → Add-ons → HA Git Sync Pro → Log
```

## 📝 License

MIT License - vezi [LICENSE](LICENSE)

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/ha-git-sync-pro/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/ha-git-sync-pro/discussions)

---

Made with ❤️ by [Cursuri Hub](https://cursurihub.ro)
