# 🚀 QUICK START GUIDE

## Pentru Linux (Ubuntu/Debian)

### Instalare Automată (RECOMANDAT)

```bash
# 1. Descarcă și dezarhivează proiectul
cd cursuri-hub-platform

# 2. Rulează scriptul de instalare automată
chmod +x setup.sh
./setup.sh
```

Scriptul va instala automat:
- ✅ Node.js 18.x
- ✅ PostgreSQL 14
- ✅ Redis
- ✅ Toate dependențele npm
- ✅ Database schema
- ✅ Seed data
- ✅ Configurare .env

---

### Instalare Manuală

Dacă preferi să instalezi manual:

#### 1. Instalare Dependențe Sistem

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Redis
sudo apt install -y redis-server

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server
```

#### 2. Configurare Database

```bash
# Create database
sudo -u postgres psql
```

```sql
CREATE DATABASE cursuri_hub;
CREATE USER cursuri_admin WITH ENCRYPTED PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE cursuri_hub TO cursuri_admin;
ALTER DATABASE cursuri_hub OWNER TO cursuri_admin;
\q
```

#### 3. Setup Proiect

```bash
cd backend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

#### 4. Run Migrations

```bash
# Run database migrations
npm run db:migrate

# Seed initial data
npm run db:seed
```

#### 5. Start Development Server

```bash
npm run dev
```

API va fi disponibil la: **http://localhost:3000**

---

## Credențiale Default

După instalare, vei avea:

**Admin User:**
- Email: `admin@cursurihub.ro`
- Password: `Admin123!`

⚠️ **IMPORTANT:** Schimbă password-ul după prima autentificare!

---

## Variabile de Mediu Importante

Editează `backend/.env` și actualizează:

```env
# Stripe (pentru plăți)
STRIPE_SECRET_KEY=sk_test_YOUR_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY

# SendGrid (pentru email)
SENDGRID_API_KEY=YOUR_KEY

# Twilio (pentru SMS/WhatsApp)
TWILIO_ACCOUNT_SID=YOUR_SID
TWILIO_AUTH_TOKEN=YOUR_TOKEN
```

---

## Comenzi Utile

```bash
# Development
npm run dev              # Start cu hot-reload

# Production
npm start                # Start production server

# Database
npm run db:migrate       # Run migrations
npm run db:seed          # Seed data
npm run db:reset         # Reset database

# Testing
npm test                 # Run tests
npm run test:watch       # Watch mode

# Code Quality
npm run lint             # Check code
npm run lint:fix         # Fix issues
```

---

## Structura API Endpoints

```
GET    /api/v1/health                 # Health check
POST   /api/v1/auth/register          # Register user
POST   /api/v1/auth/login             # Login
GET    /api/v1/courses                # List courses
POST   /api/v1/courses                # Create course
GET    /api/v1/courses/:id            # Get course
POST   /api/v1/bookings               # Create booking
GET    /api/v1/bookings               # List bookings
... (multe altele)
```

Documentație completă: `/docs/api/`

---

## Pentru Cursor/Trae

### Import în Cursor

```bash
# 1. Deschide Cursor
# 2. File > Open Folder
# 3. Selectează: cursuri-hub-platform/

# 4. În terminal (Ctrl+`):
cd backend
npm install
npm run dev
```

### Import în Trae

```bash
# Same process - Trae va detecta automat structura proiectului
```

---

## Troubleshooting

### PostgreSQL Connection Error

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Restart if needed
sudo systemctl restart postgresql
```

### Redis Connection Error

```bash
# Check Redis
redis-cli ping
# Should return: PONG

# Restart if needed
sudo systemctl restart redis-server
```

### Port Already in Use

```bash
# Find process on port 3000
sudo lsof -i :3000

# Kill it
kill -9 PID
```

### Permission Errors

```bash
# Fix permissions
sudo chown -R $USER:$USER cursuri-hub-platform
```

---

## Next Steps

1. ✅ Instalează platforma
2. ✅ Configurează API keys în .env
3. ✅ Testează API la http://localhost:3000
4. 📱 Construiește frontend (React/Next.js)
5. 🚀 Deploy pe AWS/DigitalOcean

---

## Support

Probleme? 
- Check `/docs/` pentru documentație
- Review logs în `backend/logs/`
- Database schema în `docs/architecture/database-schema.md`

---

**Succes cu platforma! 🎓🚀**
