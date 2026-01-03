# 🚀 START HERE - Pornire Rapidă

## Metoda Simplă (Recomandată pentru Windows)

### Pornește Totul Automat
Dublu-click pe:
```
START_ALL.bat
```
Acest script va deschide 2 ferestre:
- **Backend** (portul 8081)
- **Frontend** (portul 3000)

### Sau Pornește Individual

**Backend:**
```
START_BACKEND.bat
```

**Frontend:**
```
START_FRONTEND.bat
```

---

## Pentru Linux/Mac

### Backend
```bash
chmod +x start_backend.sh
./start_backend.sh
```

### Frontend (terminal nou)
```bash
chmod +x start_frontend.sh
./start_frontend.sh
```

---

## 📝 Ce se întâmplă la prima rulare?

### Backend (prima dată durează ~2-3 minute)
1. ✅ Creează virtual environment Python
2. ✅ Instalează toate dependințele (FastAPI, SQLAlchemy, etc.)
3. ✅ Inițializează baza de date SQLite
4. ✅ Pornește serverul pe http://localhost:8081

### Frontend (prima dată durează ~1-2 minute)
1. ✅ Instalează dependențele Node.js (Next.js, React, etc.)
2. ✅ Pornește serverul de dezvoltare
3. ✅ Deschide automat browserul pe http://localhost:3000

---

## ✅ Verificare Funcționare

După pornire, deschide:

1. **Frontend**: http://localhost:3000
   - Ar trebui să vezi pagina de login

2. **Backend API Docs**: http://localhost:8081/api/docs
   - Swagger UI cu toate endpoint-urile

3. **Backend Health**: http://localhost:8081/health
   - Ar trebui să returneze `{"status": "healthy"}`

---

## 🔧 Troubleshooting

### Backend nu pornește?
```bash
cd orchestrator
# Verifică dacă Python 3.9+ este instalat
python --version

# Șterge virtual environment și încearcă din nou
rm -rf venv  # sau rmdir /s venv pe Windows
```

### Frontend nu pornește?
```bash
cd dashboard-react
# Verifică dacă Node.js 18+ este instalat
node --version

# Șterge node_modules și încearcă din nou
rm -rf node_modules  # sau rmdir /s node_modules pe Windows
npm install
```

### Port deja folosit?
Dacă primești eroare că portul 8081 sau 3000 este deja folosit:

**Windows:**
```cmd
# Găsește procesul care folosește portul
netstat -ano | findstr :8081
# Oprește procesul (înlocuiește PID cu numărul găsit)
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
# Găsește și oprește procesul
lsof -ti:8081 | xargs kill -9
```

---

## 📚 Următorii Pași

După ce aplicația pornește:

1. **Creează un utilizator** (prima dată)
   - Click pe "Register" în pagina de login
   - Folosește: username=`admin`, password=`admin123`

2. **Adaugă un server Home Assistant**
   - Mergi la "Servers" din meniu
   - Click "Add Server"
   - Completează:
     - **Name**: numele serverului (ex: "HA Production")
     - **Host**: IP-ul Home Assistant (ex: 192.168.1.100)
     - **Port**: 8123 (sau portul tău HA)
     - **Access Token**: long-lived token din HA
     - **SSH User**: utilizatorul SSH (ex: root)
     - **SSH Password**: parola SSH

3. **Testează conexiunea**
   - Click pe iconița "Test" (becher de laborator)
   - Ar trebui să vezi latență și versiunea HA

---

## 🎯 Linkuri Utile

- **Documentație completă**: [FIXES_SUMMARY.md](./FIXES_SUMMARY.md)
- **Cum să obții HA Access Token**: Secțiunea din FIXES_SUMMARY.md
- **Probleme cunoscute**: Vezi consolele browser (F12) și terminal

---

## 🆘 Ajutor

Dacă întâmpini probleme:
1. Verifică consolele (terminal backend + frontend + browser F12)
2. Citește [FIXES_SUMMARY.md](./FIXES_SUMMARY.md) pentru detalii tehnice
3. Verifică că toate configurările din `.env` sunt corecte

---

**Enjoy! 🎉**
