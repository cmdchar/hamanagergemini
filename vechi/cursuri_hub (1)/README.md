# 🎓 CURSURI HUB - Platforma Națională de Cursuri Fizice

Hub național pentru conectarea părinților cu profesori și organizații care oferă cursuri fizice pentru copii.

## 🎯 Despre Proiect

**Model Business:** Sawyer Hybrid - profesorii aleg între:
- **Opțiunea A:** Abonament software (100-300 RON/lună) + Comision redus (10-15%)
- **Opțiunea B:** Zero abonament + Comision mai mare (20-25%)

**Oraș Pilot:** Focșani, România

## 🏗️ Arhitectură

### Tech Stack
- **Backend:** Node.js + Express
- **Database:** PostgreSQL + Redis
- **Authentication:** JWT + Passport.js
- **Payments:** Stripe Connect
- **Storage:** AWS S3 / Cloudinary
- **Email:** SendGrid
- **SMS/WhatsApp:** Twilio
- **Real-time:** Socket.io
- **Queue:** Bull (Redis-based)

### Frontend (După MVP backend)
- **Web:** React + Next.js
- **Mobile:** React Native / PWA
- **Admin:** React Admin
- **UI Library:** Tailwind CSS + shadcn/ui

## 📁 Structura Proiect

```
cursuri-hub-platform/
├── backend/
│   ├── src/
│   │   ├── api/              # API routes
│   │   ├── config/           # Configuration
│   │   ├── controllers/      # Business logic
│   │   ├── middleware/       # Express middleware
│   │   ├── models/           # Database models
│   │   ├── services/         # Business services
│   │   ├── utils/            # Utilities
│   │   ├── validators/       # Input validation
│   │   └── app.js           # App initialization
│   ├── migrations/           # Database migrations
│   ├── seeds/                # Seed data
│   ├── tests/                # Tests
│   └── package.json
├── frontend/                 # (Fază 2)
├── mobile/                   # (Fază 2)
├── admin/                    # (Fază 2)
├── docs/                     # Documentation
│   ├── api/                  # API documentation
│   ├── architecture/         # Architecture diagrams
│   └── guides/               # Setup guides
└── docker/                   # Docker configs

```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Stripe Account

### Installation

```bash
# Clone repository
git clone <repo-url>
cd cursuri-hub-platform

# Install dependencies
cd backend
npm install

# Setup environment variables
cp .env.example .env
# Edit .env with your credentials

# Setup database
npm run db:create
npm run db:migrate
npm run db:seed

# Start development server
npm run dev
```

### Environment Variables

```env
# Server
NODE_ENV=development
PORT=3000
API_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/cursuri_hub
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRES_IN=7d

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# AWS S3
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=eu-central-1
AWS_BUCKET_NAME=

# Email (SendGrid)
SENDGRID_API_KEY=
FROM_EMAIL=noreply@cursurihub.ro

# SMS (Twilio)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Admin
ADMIN_EMAIL=admin@cursurihub.ro
ADMIN_PASSWORD=change-this-in-production
```

## 📊 Database Schema

Voir `docs/architecture/database-schema.md`

## 🔌 API Documentation

API documentation disponibilă la: `http://localhost:3000/api-docs`

Voir `docs/api/` pentru detalii complete.

## 🧪 Testing

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run specific test
npm test -- path/to/test.js
```

## 📦 Deployment

```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🎯 Roadmap MVP

### ✅ Faza 1: Backend Foundation (CURRENT)
- [x] Project structure
- [x] Database schema
- [x] Authentication system
- [x] User management
- [x] Course management
- [x] Booking system
- [x] Payment integration
- [x] Admin panel API
- [x] Notification system

### 🔄 Faza 2: Frontend Development
- [ ] Landing page
- [ ] Parent dashboard
- [ ] Teacher dashboard
- [ ] Admin panel UI
- [ ] Search & discovery
- [ ] Booking flow
- [ ] Payment flow

### 🔄 Faza 3: Mobile & Enhancement
- [ ] PWA
- [ ] Mobile apps (React Native)
- [ ] AI recommendations
- [ ] Advanced analytics
- [ ] Chat system
- [ ] Community features

## 👥 Roles & Permissions

### Parent
- Browse and search courses
- Book courses for children
- Make payments
- Leave reviews
- Manage family profile

### Teacher (Individual)
- Create and manage courses
- Set availability
- Manage bookings
- View earnings
- Communicate with parents

### Organization
- All teacher features
- Multi-location management
- Multi-teacher management
- Advanced analytics

### Admin
- System configuration
- User management
- Content moderation
- Financial oversight
- Analytics & reporting

## 📝 License

Proprietary - All rights reserved

## 🤝 Contributing

Ce projet est privé. Pour contribuer, contactez l'équipe.

## 📧 Contact

- **Email:** contact@cursurihub.ro
- **Website:** https://cursurihub.ro

---

**Built with ❤️ in Romania**
