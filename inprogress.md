# 🚧 IN PROGRESS - Implementări Viitoare

**Ultima actualizare:** 1 Ianuarie 2026
**Status platformă:** 95% MVP Complete
**Următorul milestone:** SaaS Platform cu Research Integration

---

## 📊 STATUS ACTUAL

### ✅ Ce Avem Deja Implementat (din Research)

| Feature din Research | Status | Implementare Actuală |
|---------------------|--------|---------------------|
| **Remote Access (VPN)** | ✅ 100% | Tailscale integration completă |
| **Device Discovery** | ✅ 100% | Auto-discovery HA entities via API |
| **Multi-Instance Management** | ✅ 100% | Manage unlimited Raspberry Pi/HA servers |
| **SSH Authentication** | ✅ 100% | Password + SSH keys (OpenSSH + PPK) |
| **Dashboard UI** | ✅ 100% | Card-based layout cu real-time updates |
| **MQTT Support** | ✅ 80% | Broker ready, needs WebSocket integration |
| **Analytics Dashboard** | ✅ 70% | System metrics, needs energy analytics |
| **Automations** | ✅ 60% | Manual creation, needs template library |
| **GitHub Integration** | ✅ 95% | Backend complete, needs OAuth setup |
| **Security (Encryption)** | ✅ 100% | AES-256 credentials, JWT auth |
| **AI Assistant** | ✅ 100% | Deepseek integration for YAML generation |
| **Backup & Rollback** | ✅ 100% | Automated backups with restore |
| **Multi-user Access** | ❌ 0% | Single user only (NEEDS RBAC) |
| **Freemium Model** | ❌ 0% | No pricing tiers yet |
| **Mobile App** | ❌ 0% | Web-only currently |
| **Onboarding Wizard** | ⚠️ 30% | Basic add server form, needs guided wizard |

---

## 🎯 ROADMAP - Implementare Research

### PHASE 1: MVP Polish & SaaS Foundation (Săptămâni 1-4)

#### Sprint 1: User Onboarding (Săptămâna 1)
**Obiectiv:** 10-minute setup (target din research)

**Tasks:**
- [ ] **Onboarding Wizard** (New User Flow)
  - [ ] Backend: `POST /api/v1/onboarding/start`
  - [ ] Segmentation questions (4 întrebări):
    - Role: Homeowner, Renter, Developer
    - Goal: Energy saving, Convenience, Security
    - Home size: Apartment, House, Estate
    - Tech level: Beginner, Intermediate, Advanced
  - [ ] Frontend: `app/(dashboard)/onboarding/page.tsx`
  - [ ] Progress bar: "Step 2 of 5"
  - [ ] Save preferences: `user_preferences` table

- [ ] **Guided Server Connection** (Interactive Tutorial)
  - [ ] Step 1: Detect connection type (Local/Tailscale/VPN)
  - [ ] Step 2: Test connection BEFORE saving
  - [ ] Step 3: Show discovered devices preview
  - [ ] Step 4: Enable recommended integrations
  - [ ] Tooltips cu video tutorials (3-5 min)

- [ ] **Interactive Walkthroughs**
  - [ ] Install `react-joyride` pentru product tours
  - [ ] First login → Dashboard tour
  - [ ] First server → Connection wizard
  - [ ] First automation → Template selector

**Success Metric:** Average setup time < 10 minutes

---

#### Sprint 2: Analytics & Energy Monitoring (Săptămâna 2)
**Obiectiv:** Implement energy analytics din research (Section 9)

**Tasks:**
- [ ] **Energy Consumption Tracking**
  - [ ] Backend: `GET /api/v1/analytics/energy`
  - [ ] Query InfluxDB pentru time-series data
  - [ ] Endpoints:
    - `/energy/current` - Real-time consumption
    - `/energy/hourly` - Last 24h
    - `/energy/daily` - Last 30 days
    - `/energy/monthly` - Last 12 months
    - `/energy/comparison` - YoY, MoM comparisons

- [ ] **Device Energy Dashboard**
  - [ ] Frontend: `app/(dashboard)/analytics/energy/page.tsx`
  - [ ] Charts cu Recharts/Chart.js:
    - Line chart: Consumption trends
    - Bar chart: Per-device usage
    - Pie chart: Device categories (%)
  - [ ] Top consumers list (Section 9.1 din research)
  - [ ] Efficiency recommendations

- [ ] **Energy Goals & Alerts**
  - [ ] Set monthly energy budget
  - [ ] Alert când >90% budget reached
  - [ ] Smart recommendations: "Reduce AC temp by 2°C → Save 15%"

**Success Metric:** Energy dashboard functional, accurate predictions ±5%

---

#### Sprint 3: Automation Templates Library (Săptămâna 3)
**Obiectiv:** Template library din research (Section 8.2)

**Tasks:**
- [ ] **Template Database**
  - [ ] Model: `automation_templates` table
    ```sql
    CREATE TABLE automation_templates (
        id UUID PRIMARY KEY,
        name VARCHAR(200),
        description TEXT,
        category VARCHAR(100), -- energy, security, comfort, etc.
        difficulty ENUM('beginner', 'intermediate', 'advanced'),
        yaml_template TEXT,
        required_entities JSON, -- What devices needed
        estimated_savings VARCHAR(50), -- "Save 20% energy"
        popularity_score INT DEFAULT 0,
        created_at TIMESTAMP
    );
    ```

- [ ] **Pre-built Templates** (Minimum 20)
  - [ ] Energy Saving:
    - "Night mode" (reduce heating/cooling)
    - "Away mode" (turn off everything)
    - "Smart thermostat" (adaptive temp)
  - [ ] Security:
    - "Perimeter alarm" (motion sensors)
    - "Camera recording on motion"
    - "Lights flash on doorbell"
  - [ ] Convenience:
    - "Morning routine" (lights, coffee, news)
    - "Movie mode" (dim lights, close curtains)
    - "Goodnight" (lock, arm, lights off)

- [ ] **Template Selector UI**
  - [ ] Frontend: `app/(dashboard)/automations/templates/page.tsx`
  - [ ] Filter by:
    - Category (energy, security, comfort, etc.)
    - Difficulty (beginner, intermediate, advanced)
    - Available devices (show only compatible templates)
  - [ ] Preview YAML before applying
  - [ ] One-click "Apply Template"
  - [ ] Customize template variables

**Success Metric:** 50%+ automations created from templates

---

#### Sprint 4: RBAC & Multi-User (Săptămâna 4)
**Obiectiv:** Multi-user access din research (Section 3.1)

**Tasks:**
- [ ] **User Roles System**
  - [ ] Database models:
    ```sql
    CREATE TABLE roles (
        id UUID PRIMARY KEY,
        name VARCHAR(50) UNIQUE, -- admin, editor, viewer
        permissions JSON -- {servers: [read, write], automations: [read, write, execute]}
    );

    CREATE TABLE user_roles (
        user_id UUID REFERENCES users(id),
        role_id UUID REFERENCES roles(id),
        server_id UUID REFERENCES servers(id), -- Per-server permissions
        granted_by UUID REFERENCES users(id),
        granted_at TIMESTAMP
    );
    ```

  - [ ] Predefined roles:
    - **Admin:** Full access (delete, modify, invite)
    - **Editor:** Create/edit automations, deploy configs
    - **Viewer:** Read-only dashboard access
    - **Custom:** Granular permissions per feature

- [ ] **Invitation System**
  - [ ] Backend: `POST /api/v1/invitations`
  - [ ] Email invite link (magic link, expires 48h)
  - [ ] Invited user signup flow
  - [ ] Set role during invitation

- [ ] **Permission Middleware**
  - [ ] Check permissions before API calls
  - [ ] Frontend: Hide UI elements based on role
  - [ ] Audit log: Who did what

**Success Metric:** 3+ users can collaborate on 1 server

---

### PHASE 2: Advanced Features & Monetization (Săptămâni 5-8)

#### Sprint 5: Pricing Tiers & Freemium (Săptămâna 5)
**Obiectiv:** Implement freemium model din research (Section 10.1)

**Tasks:**
- [ ] **Subscription Plans**
  - [ ] Database:
    ```sql
    CREATE TABLE subscriptions (
        id UUID PRIMARY KEY,
        user_id UUID REFERENCES users(id),
        plan VARCHAR(50), -- free, pro, enterprise
        status VARCHAR(50), -- active, cancelled, expired
        started_at TIMESTAMP,
        expires_at TIMESTAMP,
        features JSON -- What's enabled
    );
    ```

  - [ ] Plans:
    ```
    FREE:
    - 1 Raspberry Pi
    - Device monitoring
    - Basic automations (10 max)
    - Community templates
    - Email support (24h)

    PRO ($9/month):
    - 5 Raspberry Pi
    - Unlimited automations
    - Advanced analytics
    - Energy reports
    - Priority support (2h)
    - Multi-user (3 users)

    ENTERPRISE (Custom):
    - Unlimited instances
    - White-label
    - Dedicated support
    - On-premise option
    - API unlimited
    ```

- [ ] **Stripe Integration**
  - [ ] Backend: `POST /api/v1/billing/subscribe`
  - [ ] Stripe Checkout session
  - [ ] Webhook: `/api/v1/webhooks/stripe`
  - [ ] Handle events:
    - `checkout.session.completed` → Activate plan
    - `invoice.payment_failed` → Downgrade to free
    - `customer.subscription.deleted` → Cancel

- [ ] **Feature Gating**
  - [ ] Middleware: Check plan limits
  - [ ] Frontend: Show "Upgrade to Pro" banners
  - [ ] Usage tracking:
    - Servers count
    - Automations count
    - API calls per month

**Success Metric:** 5-10% free → pro conversion rate

---

#### Sprint 6: Mobile PWA (Săptămâna 6)
**Obiectiv:** Progressive Web App din research (Section 11.2)

**Tasks:**
- [ ] **PWA Configuration**
  - [ ] `next.config.js`: Enable PWA
  - [ ] `manifest.json`:
    ```json
    {
      "name": "HA Config Manager",
      "short_name": "HACM",
      "description": "Manage your smart home from anywhere",
      "start_url": "/dashboard",
      "display": "standalone",
      "background_color": "#ffffff",
      "theme_color": "#3b82f6",
      "icons": [
        {
          "src": "/icon-192.png",
          "sizes": "192x192",
          "type": "image/png"
        },
        {
          "src": "/icon-512.png",
          "sizes": "512x512",
          "type": "image/png"
        }
      ]
    }
    ```

- [ ] **Service Worker**
  - [ ] Install `next-pwa`
  - [ ] Cache strategies:
    - Dashboard: Cache-first
    - API calls: Network-first
    - Static assets: Cache-first
  - [ ] Offline mode: Show cached data + banner

- [ ] **Push Notifications**
  - [ ] Backend: Web Push API
  - [ ] Subscribe user to push
  - [ ] Send notifications:
    - Deployment success/fail
    - Device offline
    - Automation triggered
    - Energy goal reached

- [ ] **Install Prompt**
  - [ ] Detect iOS/Android
  - [ ] Show "Add to Home Screen" prompt
  - [ ] Save dismiss preference

**Success Metric:** 30%+ users install PWA

---

#### Sprint 7: AI Automation Suggestions (Săptămâna 7)
**Obiectiv:** AI-powered recommendations din research (Section 5.2)

**Tasks:**
- [ ] **Pattern Detection**
  - [ ] Analyze user behavior:
    - When lights are turned on/off
    - Temperature preferences per time
    - Device usage patterns
  - [ ] ML model (scikit-learn):
    ```python
    from sklearn.ensemble import RandomForestClassifier

    # Train on historical data
    model.fit(features, labels)

    # Predict next automation
    suggestion = model.predict(current_state)
    ```

- [ ] **Smart Suggestions**
  - [ ] Backend: `GET /api/v1/ai/suggestions`
  - [ ] Suggestions format:
    ```json
    {
      "type": "automation",
      "confidence": 0.87,
      "title": "Auto-turn off living room lights at 23:00",
      "reason": "You manually turn them off at this time 85% of nights",
      "template": "{ yaml automation }",
      "estimated_savings": "Save 2 kWh/month"
    }
    ```

- [ ] **Suggestions UI**
  - [ ] Dashboard card: "Smart Suggestions (3)"
  - [ ] Click → Preview automation
  - [ ] One-click "Apply"
  - [ ] Dismiss with feedback: "Not useful" / "Already doing this"

**Success Metric:** 40%+ suggestions accepted

---

#### Sprint 8: Advanced Security (Săptămâna 8)
**Obiectiv:** Zero-trust security din research (Section 3.1)

**Tasks:**
- [ ] **Two-Factor Authentication (2FA)**
  - [ ] Backend: `speakeasy` library pentru TOTP
  - [ ] Endpoints:
    - `POST /api/v1/auth/2fa/enable`
    - `POST /api/v1/auth/2fa/verify`
    - `POST /api/v1/auth/2fa/disable`
  - [ ] Frontend: QR code setup
  - [ ] Backup codes (10 single-use codes)

- [ ] **IP Whitelist**
  - [ ] Table: `user_ip_whitelist`
  - [ ] Block access from non-whitelisted IPs
  - [ ] Email notification on new IP login

- [ ] **Session Management**
  - [ ] Active sessions list
  - [ ] Revoke specific sessions
  - [ ] Force logout all devices

- [ ] **Audit Trail Enhancement**
  - [ ] Log ALL actions:
    - Login/logout
    - Server added/removed
    - Automation created/deleted
    - File edited
    - Settings changed
  - [ ] Frontend: Audit log viewer
  - [ ] Filter by user, action, date
  - [ ] Export to CSV

**Success Metric:** Zero security incidents

---

### PHASE 3: Scale & Enterprise (Săptămâni 9-12)

#### Sprint 9: Matter Protocol Support (Săptămâna 9)
**Obiectiv:** Future-proof compatibility din research (Section 8.1)

**Tasks:**
- [ ] **Matter Server Integration**
  - [ ] Backend: Matter controller library
  - [ ] Auto-discover Matter devices
  - [ ] Commission new devices
  - [ ] Control Matter devices via API

- [ ] **Matter Device UI**
  - [ ] Show Matter devices separate tab
  - [ ] Commission wizard
  - [ ] QR code scanning

**Success Metric:** Discover & control 5+ Matter devices

---

#### Sprint 10: Marketplace & Integrations (Săptămâna 10)
**Obiectiv:** Integration marketplace din research (Section 12.3)

**Tasks:**
- [ ] **Integration Store**
  - [ ] Database: `integrations` table
  - [ ] Categories:
    - Voice assistants (Alexa, Google, Siri)
    - Smart speakers (Sonos, Bose)
    - Security (Ring, Nest, Wyze)
    - Energy (Tesla Powerwall, solar)
    - Climate (Nest, Ecobee)

- [ ] **One-Click Install**
  - [ ] Frontend: Browse integrations
  - [ ] Click "Install" → Configure credentials
  - [ ] Auto-discover new devices

**Success Metric:** 20+ integrations available, 50%+ users install ≥1

---

#### Sprint 11: White-Label Option (Săptămâna 11)
**Obiectiv:** Enterprise feature din research (Section 10.1)

**Tasks:**
- [ ] **Branding Customization**
  - [ ] Custom logo upload
  - [ ] Custom color scheme
  - [ ] Custom domain (CNAME)
  - [ ] Remove "Powered by HACM"

- [ ] **Multi-Tenancy**
  - [ ] Tenant isolation (separate databases)
  - [ ] Tenant-specific settings
  - [ ] Resource quotas per tenant

**Success Metric:** 1+ enterprise customer using white-label

---

#### Sprint 12: On-Premise Deployment (Săptămâna 12)
**Obiectiv:** Enterprise option din research (Section 10.1)

**Tasks:**
- [ ] **Docker Compose for Enterprise**
  - [ ] Production-ready docker-compose
  - [ ] All services included:
    - Backend API
    - Frontend
    - PostgreSQL
    - Redis
    - InfluxDB
    - MQTT broker
  - [ ] Environment configuration
  - [ ] SSL/TLS certificates

- [ ] **Helm Chart (Kubernetes)**
  - [ ] Kubernetes deployment
  - [ ] Auto-scaling
  - [ ] Load balancing
  - [ ] Persistent volumes

**Success Metric:** Deploy on customer infrastructure in <1 hour

---

## 📝 BACKLOG (După MVP)

### From Research - Nice to Have
- [ ] **Thread Network Support** (IoT mesh networking)
- [ ] **Zigbee2MQTT Advanced** (full firmware management)
- [ ] **Node-RED Integration** (visual automation builder)
- [ ] **Voice Control** (Alexa, Google Assistant, Siri)
- [ ] **Grafana Dashboards** (advanced metrics visualization)
- [ ] **Docker Compose Management** (manage HA containers)
- [ ] **Configuration Cleanup** (detect dead automations)
- [ ] **Marketplace Revenue Share** (community integrations)
- [ ] **Professional Services** (consulting, setup help)
- [ ] **API Webhooks** (custom integrations)

### Platform Improvements
- [ ] **Performance Optimization**
  - [ ] Database query optimization
  - [ ] Frontend bundle size reduction
  - [ ] Image optimization (WebP, lazy loading)
  - [ ] Redis caching layer

- [ ] **Testing Coverage**
  - [ ] Unit tests: 80%+ coverage
  - [ ] Integration tests
  - [ ] E2E tests (Playwright)
  - [ ] Load testing (k6)

- [ ] **Documentation**
  - [ ] API documentation (Swagger/OpenAPI)
  - [ ] User guides per feature
  - [ ] Video tutorials
  - [ ] Developer documentation

---

## 🎯 SUCCESS METRICS (From Research Section 16)

### Growth Metrics
- [ ] Monthly Active Users: 10K în year 1
- [ ] User Retention (30-day): 60%+
- [ ] Signup-to-Active: 40%+
- [ ] NPS Score: 50+

### Product Metrics
- [ ] Average setup time: < 10 min
- [ ] Automation success rate: 99%+
- [ ] API latency p95: < 500ms
- [ ] Dashboard load time: < 2s

### Business Metrics
- [ ] LTV/CAC ratio: 3:1+
- [ ] Free-to-Pro conversion: 5-10%
- [ ] MRR growth: 20%/month (year 1)
- [ ] Cost per user: < $1/user/year

---

## 🔧 TECH DEBT & REFACTORING

### Current Issues to Address
- [ ] **Logging Standardization**
  - [ ] Replace multiple logging libs cu Loguru consistent
  - [ ] Structured logging (JSON format)
  - [ ] Log levels consistent (DEBUG, INFO, WARNING, ERROR)

- [ ] **Error Handling**
  - [ ] Consistent error responses
  - [ ] User-friendly error messages
  - [ ] Error tracking (Sentry integration)

- [ ] **Code Quality**
  - [ ] ESLint + Prettier pentru frontend
  - [ ] Black + isort pentru backend
  - [ ] Pre-commit hooks
  - [ ] CI/CD pipeline (GitHub Actions)

---

## 📚 LEARNING & RESEARCH TASKS

### Continuous Learning
- [ ] **Research Updates** (Quarterly)
  - [ ] New Home Assistant features
  - [ ] Matter protocol updates
  - [ ] Security best practices
  - [ ] SaaS pricing trends

- [ ] **Community Engagement**
  - [ ] Home Assistant forums
  - [ ] Reddit r/homeassistant
  - [ ] Discord communities
  - [ ] YouTube channels

- [ ] **Competitor Analysis** (Monthly)
  - [ ] Nabu Casa features
  - [ ] Homeway updates
  - [ ] New players in market

---

## 🤝 COLLABORATION & TEAM

### If/When Team Grows
- [ ] **Roles to Hire**
  - [ ] Frontend developer (React specialist)
  - [ ] Backend developer (Python/FastAPI)
  - [ ] DevOps engineer (Kubernetes, AWS)
  - [ ] UI/UX designer
  - [ ] Technical writer (docs)
  - [ ] Customer support (part-time)

- [ ] **Processes to Setup**
  - [ ] Agile sprints (2-week cycles)
  - [ ] Daily standups
  - [ ] Code reviews mandatory
  - [ ] Design reviews
  - [ ] Weekly retros

---

## ✅ COMPLETED (Archive)

### Recent Completions (Ianuarie 2026)
- [x] GitHub integration backend complete
- [x] GitHub integration UI created
- [x] Sidebar updated with GitHub link
- [x] Docker rebuilt with git
- [x] Comprehensive documentation created
- [x] Discovery analysis complete
- [x] Research integration planning

---

## 📊 PRIORITY MATRIX

```
HIGH PRIORITY + HIGH IMPACT:
├─ Onboarding wizard (Sprint 1)
├─ Freemium pricing (Sprint 5)
├─ Automation templates (Sprint 3)
└─ Energy analytics (Sprint 2)

HIGH PRIORITY + MEDIUM IMPACT:
├─ RBAC & multi-user (Sprint 4)
├─ Mobile PWA (Sprint 6)
└─ AI suggestions (Sprint 7)

MEDIUM PRIORITY + HIGH IMPACT:
├─ Advanced security (Sprint 8)
├─ Marketplace (Sprint 10)
└─ Matter support (Sprint 9)

LOW PRIORITY (Later):
├─ White-label (Sprint 11)
├─ On-premise (Sprint 12)
└─ Voice control
```

---

**Next Review:** Weekly Monday morning
**Owner:** Development Team
**Stakeholders:** Users, Beta Testers, Community

**Questions/Feedback:** Create issue in GitHub repo or Discord
