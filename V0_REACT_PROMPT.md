# 🎯 v0.dev ULTIMATE Prompt: HA Config Manager - React Edition

**Repository**: https://github.com/cmdchar/v0-vue-3-ha-config-manager.git

> Create a complete, production-ready admin dashboard for **HA Config Manager** - a comprehensive Home Assistant configuration and device management platform.

---

## 🎨 Tech Stack (Exactly what v0 provides)

```typescript
Frontend Framework: React 18 + TypeScript
UI Library: shadcn/ui + Tailwind CSS
State Management:
  - TanStack Query (React Query) for server state
  - Zustand for client state
Routing: React Router v6
Forms: React Hook Form + Zod validation
Charts: Recharts (already installed)
Notifications: Sonner
HTTP Client: Axios with interceptors
Icons: Lucide React
```

---

## 🏗️ Project Overview

**What is HA Config Manager?**

An enterprise-grade platform for managing multiple Home Assistant deployments, smart home devices, AI assistance, automated backups, and security features.

**Backend**: FastAPI (Python) - Already built and running
**API Base URL**: `http://localhost:8000/api/v1`

**11 Main Pages**:
1. Dashboard - Overview with stats and charts
2. Servers - SSH server management
3. Deployments - Home Assistant deployment automation
4. WLED - LED controller management
5. FPP - Falcon Player (Christmas lights)
6. Tailscale - VPN management
7. ESPHome - ESP32/ESP8266 OTA updates
8. Backups - Node-RED & Zigbee2MQTT backups
9. AI Assistant - Chat with AI that executes actions
10. Secrets - Encrypted secrets with AES-256-GCM
11. Audit Logs - System-wide audit trail

---

## 📋 Complete API Specification

### Authentication

```typescript
POST /api/v1/auth/login
Content-Type: multipart/form-data
Body: { username: string, password: string }
Response: { access_token: string, token_type: "bearer", user: User }

POST /api/v1/auth/register
Body: { email: string, username: string, password: string }
Response: User

// Add Bearer token to all subsequent requests:
Authorization: Bearer {access_token}
```

### Servers

```typescript
GET    /api/v1/servers
POST   /api/v1/servers
GET    /api/v1/servers/{id}
PATCH  /api/v1/servers/{id}
DELETE /api/v1/servers/{id}
POST   /api/v1/servers/{id}/test

// Server Type
interface Server {
  id: number
  name: string
  description?: string
  ip_address: string
  ssh_port: number
  ssh_user: string
  os_type?: string
  status: 'online' | 'offline' | 'unknown'
  cpu_usage?: number
  memory_usage?: number
  disk_usage?: number
  last_seen?: string
  created_at: string
  updated_at: string
}
```

### Deployments

```typescript
GET    /api/v1/deployments
POST   /api/v1/deployments
GET    /api/v1/deployments/{id}
PATCH  /api/v1/deployments/{id}
DELETE /api/v1/deployments/{id}
POST   /api/v1/deployments/{id}/restart
GET    /api/v1/deployments/{id}/logs

interface Deployment {
  id: number
  name: string
  server_id: number
  ha_version: string
  port: number
  domain?: string
  status: 'running' | 'stopped' | 'error' | 'deploying'
  created_at: string
  server?: Server
}
```

### WLED

```typescript
GET    /api/v1/wled/devices
POST   /api/v1/wled/devices
POST   /api/v1/wled/devices/{id}/state
GET    /api/v1/wled/presets
POST   /api/v1/wled/presets
GET    /api/v1/wled/schedules

interface WLEDDevice {
  id: number
  name: string
  ip_address: string
  status: 'online' | 'offline'
  brightness: number
  is_on: boolean
  current_effect?: string
}

interface WLEDState {
  on: boolean
  brightness: number
  color?: { r: number; g: number; b: number }
  effect?: string
}
```

### ESPHome

```typescript
POST   /api/v1/esphome/devices/discover
GET    /api/v1/esphome/devices
POST   /api/v1/esphome/devices/{id}/ota
POST   /api/v1/esphome/devices/bulk-update
GET    /api/v1/esphome/devices/{id}/logs

interface ESPHomeDevice {
  id: number
  name: string
  ip_address: string
  platform: 'esp32' | 'esp8266'
  version: string
  status: 'online' | 'offline' | 'updating'
}
```

### Backups

```typescript
POST   /api/v1/backup/nodered/configs
POST   /api/v1/backup/nodered/backups
POST   /api/v1/backup/zigbee2mqtt/configs
POST   /api/v1/backup/zigbee2mqtt/backups
POST   /api/v1/backup/schedules
GET    /api/v1/backup/backups
POST   /api/v1/backup/backups/{id}/restore

interface Backup {
  id: number
  backup_type: 'nodered' | 'zigbee2mqtt'
  file_size: number
  status: 'completed' | 'failed'
  created_at: string
}

interface BackupSchedule {
  id: number
  backup_type: string
  cron_expression: string
  retention_days: number
  is_active: boolean
}
```

### AI Assistant

```typescript
POST   /api/v1/ai/conversations
POST   /api/v1/ai/conversations/{id}/chat
POST   /api/v1/ai/actions/execute
GET    /api/v1/ai/conversations

interface AIMessage {
  role: 'user' | 'assistant'
  content: string
  suggested_actions?: AIAction[]
}

interface AIAction {
  id: number
  action_type: string
  parameters: Record<string, any>
  status: 'pending' | 'completed' | 'failed'
  requires_confirmation: boolean
}
```

### Secrets

```typescript
GET    /api/v1/security/secrets
POST   /api/v1/security/secrets
GET    /api/v1/security/secrets/{id}/decrypt
POST   /api/v1/security/secrets/{id}/rotate
POST   /api/v1/security/secrets/{id}/revoke
DELETE /api/v1/security/secrets/{id}
GET    /api/v1/security/secrets/statistics

interface Secret {
  id: number
  name: string
  secret_type: 'api_key' | 'password' | 'token' | 'certificate' | 'ssh_key'
  is_revoked: boolean
  rotation_required: boolean
  access_count: number
  last_accessed?: string
  created_at: string
}
```

### Audit Logs

```typescript
POST   /api/v1/security/audit-logs/search
GET    /api/v1/security/security-events
POST   /api/v1/security/security-events/{id}/resolve
GET    /api/v1/security/audit-logs/statistics

interface AuditLog {
  id: number
  action: string
  category: string
  severity: 'info' | 'warning' | 'error' | 'critical'
  status: 'success' | 'failure'
  description: string
  user_id?: number
  resource_type?: string
  created_at: string
}
```

---

## 🎨 Design System

### Colors (Tailwind)

```typescript
Primary: blue-600 (#2563eb)
Secondary: slate-700 (#334155)
Success: green-600 (#16a34a)
Warning: orange-500 (#f97316)
Error: red-600 (#dc2626)
Info: sky-500 (#0ea5e9)

Background:
  Light: slate-50 (#f8fafc)
  Dark: slate-950 (#020617)

Surface:
  Light: white (#ffffff)
  Dark: slate-900 (#0f172a)
```

### Typography

```
Font Family: Inter (from Tailwind)
Headings: font-bold text-2xl to text-4xl
Body: text-sm to text-base
Code: font-mono
```

### Spacing

Use Tailwind spacing scale: 4, 8, 12, 16, 24, 32, 48, 64

---

## 🧩 App Structure

### Layout

```
┌─────────────────────────────────────────┐
│  Header (64px)                          │
│  [Logo] [Search] [Notifications] [User]│
├──────┬──────────────────────────────────┤
│      │                                  │
│ Side │  Main Content                    │
│ bar  │  (Router Outlet)                 │
│ 256px│                                  │
│      │                                  │
└──────┴──────────────────────────────────┘
```

### Header Components

- Logo with Home Assistant icon
- Global search (Command + K)
- Notification bell with badge
- User dropdown menu (profile, settings, logout)
- Theme toggle (light/dark)

### Sidebar Navigation

Use shadcn/ui Sidebar component with:

```typescript
Dashboard (Home icon)
---
Servers (Server icon)
Deployments (Rocket icon)
---
WLED (Lightbulb icon)
FPP (Play icon)
Tailscale (Shield icon)
ESPHome (Cpu icon)
Backups (Database icon)
---
AI Assistant (Bot icon)
---
Secrets (Key icon)
Audit Logs (FileText icon)
```

---

## 🔧 Setup Instructions

### 1. Axios Client Setup

```typescript
// lib/api.ts
import axios from 'axios'
import { toast } from 'sonner'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
})

// Request interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
      toast.error('Session expired. Please login again.')
    } else if (error.response?.status === 422) {
      const detail = error.response.data?.detail
      if (Array.isArray(detail)) {
        detail.forEach((err) => toast.error(err.msg))
      } else {
        toast.error(detail || 'Validation error')
      }
    } else {
      toast.error(error.response?.data?.detail || 'An error occurred')
    }
    return Promise.reject(error)
  }
)

export default api
```

### 2. React Query Setup

```typescript
// lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000, // 30 seconds
      gcTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: true,
      retry: 3,
    },
  },
})
```

### 3. Zustand Auth Store

```typescript
// stores/authStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  email: string
  username: string
}

interface AuthState {
  user: User | null
  token: string | null
  setAuth: (user: User, token: string) => void
  logout: () => void
  isAuthenticated: boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setAuth: (user, token) => {
        localStorage.setItem('access_token', token)
        set({ user, token, isAuthenticated: true })
      },
      logout: () => {
        localStorage.removeItem('access_token')
        set({ user: null, token: null, isAuthenticated: false })
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)
```

---

## 📄 Page Implementations

### 1. Login Page

```typescript
// Features:
- Email/username field
- Password field (with show/hide toggle)
- "Remember me" checkbox
- Login button (with loading state)
- Link to register page
- Error display for failed login

// Use React Hook Form + Zod validation
// On success: call useAuthStore.setAuth() and redirect to /
```

### 2. Dashboard Page

```typescript
// Layout:
Row 1: 4 stat cards (servers, deployments, devices, backups)
Row 2: Recent activity timeline (left) + Server status chart (right)
Row 3: Resource usage charts (CPU, Memory, Disk)

// Use React Query:
const { data: stats } = useQuery({
  queryKey: ['dashboard-stats'],
  queryFn: () => api.get('/dashboard/stats'),
})

// Stat Cards:
- Icon + Number + Trend (up/down arrow)
- Click to navigate to respective page

// Charts:
- Use Recharts for LineChart, BarChart
- Real-time data (refetch every 30s)
```

### 3. Servers Page

```typescript
// Features:
- Data table with columns: Name, IP, Status, CPU, Memory, Actions
- Search bar (filters table)
- "Add Server" button (opens dialog)
- Row actions: Edit, Test Connection, Delete

// Table Component (use shadcn/ui Table):
<DataTable
  columns={columns}
  data={servers}
  searchKey="name"
/>

// Add/Edit Dialog:
- Form with React Hook Form
- Fields: name, ip_address, ssh_port, ssh_user, ssh_password
- Zod validation:
  * name: required, min 3 chars
  * ip_address: required, IP format
  * ssh_port: required, 1-65535
  * ssh_user: required
- Submit: useMutation to POST/PATCH /servers
- On success: invalidate 'servers' query, close dialog, show toast

// Delete Dialog:
- Confirmation: "Are you sure you want to delete {name}?"
- useMutation to DELETE /servers/{id}
- On success: invalidate query, show toast

// Test Connection Dialog:
- useMutation to POST /servers/{id}/test
- Show loading spinner
- Display result: success (green checkmark) or error (red X + message)
```

### 4. Deployments Page

```typescript
// Layout: Card grid (3 columns on desktop, 1 on mobile)

// Each Card:
- Deployment name (h3)
- Server name (badge)
- HA version (badge)
- Status badge: running (green), stopped (gray), error (red)
- Port number
- Action buttons: Restart, Logs, Update, Delete

// Create Deployment Dialog:
- Select server (dropdown from servers query)
- HA version (dropdown: 2024.1, 2023.12, etc.)
- Port (number input, default 8123)
- Domain (text input, optional)
- Auto restart (checkbox)

// Logs Dialog:
- Full-screen dialog
- Streaming logs (use Server-Sent Events or polling)
- Auto-scroll to bottom
- Search/filter logs
- Download logs button
```

### 5. WLED Page

```typescript
// Layout: Card grid with device controls

// Each Card:
- Device name + status badge
- On/Off toggle switch
- Brightness slider (0-255)
- Color picker (react-colorful)
- Effect dropdown
- "Save as Preset" button
- "Schedules" button

// Add Device Dialog:
- name, ip_address, port

// Presets Tab:
- List of saved presets
- Apply preset to device(s)
- Edit/Delete preset

// Schedules Tab:
- Time-based automation
- Cron expression builder (use react-cron-generator)
```

### 6. ESPHome Page

```typescript
// Features:
- "Discover Devices" button (triggers mDNS scan)
- Device table: Name, IP, Platform, Version, Status, Actions
- OTA Update action (opens dialog with file upload)
- Bulk update (select multiple, upload once)
- Real-time logs (opens drawer)

// OTA Update Dialog:
- Device name (read-only)
- File upload (drag & drop or click)
- Password field (optional)
- Progress bar during upload
- useMutation with onUploadProgress callback

// Logs Drawer:
- WebSocket connection (or polling)
- Color-coded log levels (DEBUG=gray, INFO=blue, WARN=orange, ERROR=red)
- Auto-scroll toggle
- Search
```

### 7. Backups Page

```typescript
// 3 Tabs: Node-RED, Zigbee2MQTT, Schedules

// Node-RED Tab:
- List of configs
- "Create Backup Now" button
- Backup history table
- Actions: Restore, Download, Delete

// Zigbee2MQTT Tab:
- Same structure

// Schedules Tab:
- List of scheduled backups
- Cron expression display
- Active/Inactive toggle
- Edit/Delete actions
- "Create Schedule" dialog with cron builder

// Restore Dialog:
- Backup selection (dropdown)
- Target path (text input)
- Warning: "This will overwrite existing files"
- Rollback option checkbox
```

### 8. AI Assistant Page

```typescript
// Layout: Chat interface

// Left Sidebar (200px):
- List of conversations
- "New Conversation" button
- Click to switch conversations

// Main Area:
- Chat messages (user right-aligned, AI left-aligned)
- Markdown rendering for AI responses
- Syntax highlighting for code blocks

// Suggested Actions Panel:
- When AI suggests an action, show card with:
  * Action type
  * Parameters (formatted JSON)
  * "Execute" button (opens confirmation dialog)
  * "Cancel" button

// Input Area:
- Text input with auto-resize
- Send button
- File attachment (optional)

// Action Confirmation Dialog:
- "Execute this action?"
- Show parameters
- Explain what will happen
- Execute/Cancel buttons
```

### 9. Secrets Page

```typescript
// Top: 4 stat cards (total, active, revoked, rotation required)

// Table:
- Columns: Name, Type, Status, Last Accessed, Access Count, Actions
- Search + filters (type, status)

// Actions:
- View (decrypt): Opens dialog with decrypted value + show/hide toggle
- Rotate: Opens dialog with new value input
- Revoke: Opens confirmation with reason textarea
- Delete: Confirmation dialog

// Create Secret Dialog:
- name (text)
- type (select: api_key, password, token, etc.)
- value (password input with show/hide)
- description (textarea)
- rotation_interval_days (number, optional)
- tags (multi-select or chips input)

// Decrypt Dialog:
- Secret name (read-only)
- Type (read-only)
- Decrypted value (with show/hide toggle)
- Access count + last accessed
- Copy button
```

### 10. Audit Logs Page

```typescript
// 3 Tabs: Audit Logs, Security Events, Statistics

// Audit Logs Tab:
- Advanced filter form:
  * Action (text)
  * Category (select)
  * Severity (select: info, warning, error, critical)
  * Status (select)
  * Date range (date pickers)
  * User (select)
  * Resource type (select)
- Table with filtered results
- Click row to see details dialog

// Security Events Tab:
- Table: Type, Severity, Title, Status, Timestamp
- "Show Unresolved Only" toggle
- Resolve button (opens dialog with status + notes)

// Statistics Tab:
- Stats cards: Total Events, Events Today, Errors Today
- Pie charts: Events by Category, Events by Severity
- Use Recharts PieChart component
```

---

## 🎯 Critical Requirements

### Error Handling

```typescript
// EVERY mutation must have error handling:
const mutation = useMutation({
  mutationFn: (data) => api.post('/endpoint', data),
  onSuccess: () => {
    queryClient.invalidateQueries(['queryKey'])
    toast.success('Success message')
    closeDialog()
  },
  onError: (error) => {
    // Error already handled by interceptor
    // Just ensure loading state resets
  },
})
```

### Loading States

```typescript
// EVERY async operation must show loading:
- Buttons: disabled={mutation.isPending}
- Tables: skeleton rows while query.isLoading
- Forms: disabled fields while submitting
- Dialogs: prevent close while loading
```

### Form Validation

```typescript
// Use Zod schemas:
const serverSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters'),
  ip_address: z.string().ip('Invalid IP address'),
  ssh_port: z.number().min(1).max(65535),
  ssh_user: z.string().min(1, 'SSH user is required'),
})

// With React Hook Form:
const form = useForm({
  resolver: zodResolver(serverSchema),
  defaultValues: { ... },
})
```

### Responsive Design

```typescript
// Mobile-first approach:
- Tables: Horizontal scroll on mobile
- Dialogs: Full-screen on mobile (sm:max-w-md on desktop)
- Sidebar: Hidden on mobile (hamburger menu)
- Card grids: 1 col mobile, 2 md, 3 lg
```

### Dark Mode

```typescript
// Use next-themes:
import { ThemeProvider } from 'next-themes'

// Toggle in header:
<Button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
  {theme === 'dark' ? <Sun /> : <Moon />}
</Button>

// Persist preference in localStorage
```

---

## 🚀 Implementation Order

**Phase 1: Foundation**
1. Setup Axios client with interceptors
2. Setup React Query
3. Setup Zustand auth store
4. Create app shell (header, sidebar, router)
5. Create auth pages (login, register)
6. Create protected route wrapper

**Phase 2: Core Pages**
7. Dashboard page
8. Servers page (full CRUD)
9. Deployments page

**Phase 3: Integrations**
10. WLED page
11. FPP page
12. Tailscale page
13. ESPHome page
14. Backups page

**Phase 4: Advanced**
15. AI Assistant page
16. Secrets page
17. Audit Logs page

**Phase 5: Polish**
18. Error boundaries
19. Loading skeletons
20. Toast notifications everywhere
21. Responsive design refinements
22. Dark mode polish

---

## ✅ Acceptance Criteria

Before considering the app complete:

- [ ] All 11 pages implemented
- [ ] All forms have validation
- [ ] All tables have search
- [ ] All async operations show loading
- [ ] All errors show toast notifications
- [ ] All mutations invalidate queries
- [ ] Dark mode works everywhere
- [ ] Responsive on mobile/tablet/desktop
- [ ] Auth guards on all protected routes
- [ ] 401 redirects to login
- [ ] Can create, read, update, delete on all resources
- [ ] Real-time data updates (refetch)
- [ ] No TypeScript errors
- [ ] No console errors

---

## 🎨 UI Components to Use (shadcn/ui)

```
Layout: Sidebar, Header
Forms: Form, Input, Select, Checkbox, Switch, Textarea
Data: Table, Card, Badge, Avatar
Feedback: Dialog, Alert, Toast, Progress, Skeleton
Navigation: Tabs, DropdownMenu, Command
Charts: Use Recharts (LineChart, BarChart, PieChart)
```

---

## 📦 Final Notes

**This is a COMPLETE specification** for building HA Config Manager with v0.dev.

Everything you need is here:
- ✅ Exact API endpoints
- ✅ Complete data types
- ✅ Detailed page layouts
- ✅ Error handling patterns
- ✅ State management setup
- ✅ Form validation examples
- ✅ Responsive design rules
- ✅ Dark mode support

**Start with Phase 1 and work through systematically.**

**Good luck! 🚀**
