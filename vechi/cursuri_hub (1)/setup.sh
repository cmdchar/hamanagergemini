#!/bin/bash

# ============================================
# CURSURI HUB - Automated Setup Script
# For Ubuntu/Debian Linux
# ============================================

set -e # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should NOT be run as root (don't use sudo)"
   exit 1
fi

print_header "CURSURI HUB - Platform Setup"
print_info "This script will install and configure everything needed for the platform"
echo ""

# Confirm before proceeding
read -p "Do you want to continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Installation cancelled"
    exit 1
fi

# ============================================
# 1. SYSTEM UPDATES
# ============================================
print_header "Step 1: Updating System"
sudo apt update && sudo apt upgrade -y
print_success "System updated"

# ============================================
# 2. INSTALL NODE.JS
# ============================================
print_header "Step 2: Installing Node.js 18.x"

if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    print_info "Node.js already installed: $NODE_VERSION"
else
    print_info "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    print_success "Node.js installed: $(node -v)"
fi

print_success "npm version: $(npm -v)"

# ============================================
# 3. INSTALL POSTGRESQL
# ============================================
print_header "Step 3: Installing PostgreSQL 14"

if command -v psql &> /dev/null; then
    print_info "PostgreSQL already installed"
else
    print_info "Installing PostgreSQL..."
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    print_success "PostgreSQL installed and started"
fi

# ============================================
# 4. INSTALL REDIS
# ============================================
print_header "Step 4: Installing Redis"

if command -v redis-cli &> /dev/null; then
    print_info "Redis already installed"
else
    print_info "Installing Redis..."
    sudo apt install -y redis-server
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    print_success "Redis installed and started"
fi

# ============================================
# 5. SETUP DATABASE
# ============================================
print_header "Step 5: Setting up Database"

# Get database credentials
print_info "Please provide database credentials:"
read -p "Database name [cursuri_hub]: " DB_NAME
DB_NAME=${DB_NAME:-cursuri_hub}

read -p "Database user [cursuri_admin]: " DB_USER
DB_USER=${DB_USER:-cursuri_admin}

read -sp "Database password: " DB_PASS
echo ""

if [ -z "$DB_PASS" ]; then
    DB_PASS=$(openssl rand -base64 32)
    print_warning "No password provided. Generated random password: $DB_PASS"
fi

# Create database and user
print_info "Creating database and user..."
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || print_warning "Database already exists"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASS';" 2>/dev/null || print_warning "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER DATABASE $DB_NAME OWNER TO $DB_USER;"

print_success "Database configured"

# ============================================
# 6. INSTALL PROJECT DEPENDENCIES
# ============================================
print_header "Step 6: Installing Project Dependencies"

cd backend
if [ ! -f "package.json" ]; then
    print_info "Creating package.json..."
    npm init -y
fi

print_info "Installing dependencies..."
npm install express pg pg-hstore sequelize bcrypt jsonwebtoken passport passport-jwt \
    dotenv cors helmet express-validator morgan winston socket.io \
    stripe nodemailer twilio bull ioredis \
    --save

npm install nodemon jest supertest eslint --save-dev

print_success "Dependencies installed"

# ============================================
# 7. CREATE .ENV FILE
# ============================================
print_header "Step 7: Creating Environment Configuration"

cat > .env << EOF
# ============================================
# CURSURI HUB - Environment Configuration
# ============================================

# Environment
NODE_ENV=development

# Server
PORT=3000
API_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
DB_HOST=localhost
DB_PORT=5432
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASS=$DB_PASS

# Redis
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# Authentication
JWT_SECRET=$(openssl rand -base64 64)
JWT_EXPIRES_IN=7d
JWT_REFRESH_EXPIRES_IN=30d

# Stripe (TEST MODE - Replace with your keys)
STRIPE_SECRET_KEY=sk_test_REPLACE_WITH_YOUR_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_REPLACE_WITH_YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_REPLACE_WITH_YOUR_SECRET

# AWS S3 (Optional - for file uploads)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=eu-central-1
AWS_BUCKET_NAME=cursuri-hub-uploads

# Email (SendGrid)
SENDGRID_API_KEY=
FROM_EMAIL=noreply@cursurihub.ro
FROM_NAME=Cursuri Hub

# SMS/WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
TWILIO_WHATSAPP_NUMBER=

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3001

# Admin Credentials
ADMIN_EMAIL=admin@cursurihub.ro
ADMIN_PASSWORD=Admin123!

# Platform Settings
PLATFORM_NAME=Cursuri Hub
PLATFORM_CITY=Focșani
PLATFORM_COUNTRY=RO
PLATFORM_CURRENCY=RON
PLATFORM_TIMEZONE=Europe/Bucharest

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100

# Session
SESSION_SECRET=$(openssl rand -base64 64)

# File Upload
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=image/jpeg,image/png,image/gif,application/pdf

# Feature Flags
ENABLE_CHAT=true
ENABLE_AI_RECOMMENDATIONS=true
ENABLE_GROUPS=false
ENABLE_WAITLIST=true

# Development
DEBUG=true
LOG_LEVEL=debug
EOF

print_success ".env file created"
print_warning "IMPORTANT: Update .env with your Stripe, SendGrid, and Twilio credentials!"

# ============================================
# 8. RUN DATABASE MIGRATIONS
# ============================================
print_header "Step 8: Running Database Migrations"

print_info "Running schema migrations..."
PGPASSWORD=$DB_PASS psql -h localhost -U $DB_USER -d $DB_NAME -f migrations/001_initial_schema.sql
print_success "Initial schema created"

PGPASSWORD=$DB_PASS psql -h localhost -U $DB_USER -d $DB_NAME -f migrations/002_additional_tables.sql
print_success "Additional tables created"

# ============================================
# 9. SEED DATABASE
# ============================================
print_header "Step 9: Seeding Database"

print_info "Inserting seed data..."
PGPASSWORD=$DB_PASS psql -h localhost -U $DB_USER -d $DB_NAME -f seeds/001_initial_data.sql
print_success "Seed data inserted"

# ============================================
# 10. CREATE DIRECTORY STRUCTURE
# ============================================
print_header "Step 10: Creating Project Structure"

mkdir -p src/{api,config,controllers,middleware,models,services,utils,validators}
mkdir -p tests/{unit,integration}
mkdir -p logs
mkdir -p uploads/{images,documents,temp}

print_success "Directory structure created"

# ============================================
# 11. SETUP GIT (if not already)
# ============================================
print_header "Step 11: Git Configuration"

if [ ! -d "../.git" ]; then
    cd ..
    git init
    
    # Create .gitignore
    cat > .gitignore << 'EOF'
# Dependencies
node_modules/
package-lock.json

# Environment
.env
.env.local
.env.*.local

# Logs
logs/
*.log
npm-debug.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage
coverage/
.nyc_output

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Build
dist/
build/

# Uploads
uploads/
!uploads/.gitkeep

# Temp files
tmp/
temp/
*.tmp

# Database
*.sqlite
*.db
EOF
    
    print_success "Git initialized"
else
    print_info "Git already initialized"
fi

# ============================================
# 12. CREATE START SCRIPTS
# ============================================
print_header "Step 12: Creating Start Scripts"

cd backend

# Update package.json scripts
cat > package.json.tmp << 'EOF'
{
  "name": "cursuri-hub-backend",
  "version": "1.0.0",
  "description": "Cursuri Hub Platform - Backend API",
  "main": "src/app.js",
  "scripts": {
    "start": "node src/app.js",
    "dev": "nodemon src/app.js",
    "test": "jest --coverage",
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix",
    "db:migrate": "psql $DATABASE_URL -f migrations/001_initial_schema.sql && psql $DATABASE_URL -f migrations/002_additional_tables.sql",
    "db:seed": "psql $DATABASE_URL -f seeds/001_initial_data.sql",
    "db:reset": "npm run db:migrate && npm run db:seed"
  },
  "keywords": ["education", "courses", "marketplace"],
  "author": "Cursuri Hub",
  "license": "UNLICENSED"
}
EOF

# Merge with existing package.json if it exists
if [ -f "package.json" ]; then
    # This is a simple merge, you might want to use a proper JSON merge tool
    mv package.json.tmp package.json
fi

print_success "Package scripts configured"

# ============================================
# INSTALLATION COMPLETE
# ============================================
print_header "Installation Complete! 🎉"

echo ""
print_success "Platform successfully set up!"
echo ""
print_info "Database Details:"
echo "  - Name: $DB_NAME"
echo "  - User: $DB_USER"
echo "  - Host: localhost:5432"
echo ""
print_info "Default Admin Login:"
echo "  - Email: admin@cursurihub.ro"
echo "  - Password: Admin123!"
echo ""
print_warning "NEXT STEPS:"
echo "  1. Edit backend/.env and add your API keys (Stripe, SendGrid, Twilio)"
echo "  2. cd backend"
echo "  3. npm run dev (to start development server)"
echo "  4. API will be available at: http://localhost:3000"
echo ""
print_info "Documentation:"
echo "  - API Docs: /docs/api/"
echo "  - Architecture: /docs/architecture/"
echo ""
print_warning "Security Reminder:"
echo "  - Change the admin password after first login!"
echo "  - Never commit .env to git!"
echo "  - Update all SECRET keys before production!"
echo ""
print_success "Happy coding! 🚀"
echo ""
