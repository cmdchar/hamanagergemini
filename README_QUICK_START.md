# HA Config Manager - Quick Start 🚀

> Managerul de configurații pentru multiple instanțe Home Assistant

## 🎯 Pornire în 3 Pași

### 1️⃣ Clonează / Deschide proiectul
```bash
cd ha-config-manager
```

### 2️⃣ Pornește aplicația

**Windows** - Dublu-click pe:
```
START_ALL.bat
```

**Linux/Mac**:
```bash
./start_backend.sh    # Terminal 1
./start_frontend.sh   # Terminal 2
```

### 3️⃣ Deschide browserul
```
http://localhost:3000
```

---

## ✨ Ce face această aplicație?

- ✅ **Gestionează multiple servere Home Assistant** dintr-un singur loc
- ✅ **Sincronizează configurații** prin SSH
- ✅ **Testează conexiuni** (SSH + HA API)
- ✅ **Editează fișiere de configurare** direct din browser
- ✅ **Terminal web** pentru comenzi SSH
- ✅ **Backup & Restore** automat
- ✅ **Deployment orchestration** pentru configurații

---

## 📋 Ce ai nevoie

### Pentru Backend:
- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- Dependențe instalate automat de script

### Pentru Frontend:
- **Node.js 18+** ([Download](https://nodejs.org/))
- Dependențe instalate automat de script

### Pentru conexiuni HA:
- **Home Assistant Long-Lived Token**
  - Profilul tău → Long-Lived Access Tokens → Create Token
- **Acces SSH** la serverul Home Assistant
  - Username + parolă SAU cheie SSH

---

## 📚 Documentație Completă

1. **[START_HERE.md](./START_HERE.md)** - Ghid detaliat de pornire + troubleshooting
2. **[FIXES_SUMMARY.md](./FIXES_SUMMARY.md)** - Toate reparațiile tehnice și configurări

---

## 🔧 Verificare Rapidă

După pornire, verifică:

| Serviciu | URL | Status |
|----------|-----|--------|
| Frontend | http://localhost:3000 | Pagina de login |
| Backend API | http://localhost:8081/api/docs | Swagger UI |
| Health Check | http://localhost:8081/health | `{"status": "healthy"}` |

---

## 🎬 Primul Login

1. Click pe **"Register"**
2. Creează cont: `admin` / `admin123`
3. Login cu credențialele create
4. Mergi la **"Servers"** → **"Add Server"**
5. Adaugă primul tău server Home Assistant!

---

## 🆘 Probleme?

### Backend nu pornește?
```bash
cd orchestrator
python --version  # Verifică Python 3.9+
```

### Frontend nu pornește?
```bash
cd dashboard-react
node --version   # Verifică Node.js 18+
```

### Port ocupat?
Backend folosește **8081**, Frontend folosește **3000**.
Vezi [START_HERE.md](./START_HERE.md) pentru cum să eliberezi porturile.

---

## 🎯 Stack Tehnologic

**Backend:**
- FastAPI (Python)
- SQLAlchemy + SQLite/PostgreSQL
- asyncssh pentru conexiuni SSH
- Fernet encryption pentru secrete

**Frontend:**
- Next.js 16 + React 19
- TanStack Query
- Tailwind CSS + shadcn/ui
- Axios pentru API calls

---

## 📦 Structură Proiect

```
├── orchestrator/          # Backend FastAPI
│   ├── app/
│   │   ├── api/v1/       # Endpoint-uri REST
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── utils/        # Helper functions
│   └── .env              # Configurare (auto-generat)
│
├── dashboard-react/       # Frontend Next.js
│   ├── app/              # Pages & routing
│   ├── components/       # React components
│   ├── lib/              # API client
│   └── .env.local        # Frontend config
│
├── START_ALL.bat         # Pornește tot (Windows)
├── start_backend.sh      # Pornește backend (Linux/Mac)
└── start_frontend.sh     # Pornește frontend (Linux/Mac)
```

---

## 🎉 That's it!

Aplicația este configurată automat și gata de folosit.

Pentru mai multe detalii, vezi:
- [START_HERE.md](./START_HERE.md) - Ghid complet
- [FIXES_SUMMARY.md](./FIXES_SUMMARY.md) - Detalii tehnice

**Enjoy managing your Home Assistant configs! 🏠✨**
