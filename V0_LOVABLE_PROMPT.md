# v0 / Lovable Prompt: HA Config Manager Frontend

## Project Overview

Create a comprehensive, enterprise-grade **Home Assistant Configuration & Device Management Platform** frontend using **Vue 3 + TypeScript + Vuetify 3**. The platform manages Home Assistant deployments, smart home devices, AI assistance, backups, and enterprise security features.

---

## Tech Stack Requirements

- **Framework**: Vue 3 with Composition API
- **Language**: TypeScript (strict mode)
- **UI Library**: Vuetify 3 (Material Design)
- **State Management**: Pinia
- **Router**: Vue Router 4
- **HTTP Client**: Axios
- **Build Tool**: Vite
- **Icons**: Material Design Icons (mdi)

---

## Design System

### Colors
- **Primary**: #1976D2 (Blue)
- **Secondary**: #424242 (Dark Grey)
- **Success**: #4CAF50 (Green)
- **Warning**: #FF9800 (Orange)
- **Error**: #F44336 (Red)
- **Info**: #2196F3 (Light Blue)
- **Background (Light)**: #FAFAFA
- **Background (Dark)**: #121212

### Typography
- **Font Family**: 'Roboto', sans-serif
- **Headings**: Roboto Medium
- **Body**: Roboto Regular
- **Code**: 'Roboto Mono', monospace

### Layout
- **Sidebar**: 256px width, collapsible
- **Header**: 64px height, fixed
- **Content**: Max width 1920px, centered
- **Spacing**: 8px base unit (8, 16, 24, 32, 48, 64)
- **Border Radius**: 4px (cards), 28px (buttons), 50% (avatars)

---

## Application Structure

### Layout Components

#### 1. App Shell
```
┌─────────────────────────────────────────┐
│  Header (64px)                          │
│  [Logo] [Search] [User] [Notifications]│
├──────┬──────────────────────────────────┤
│      │                                  │
│ Side │  Main Content Area               │
│ bar  │  (Router View)                   │
│ 256px│                                  │
│      │                                  │
│      │                                  │
└──────┴──────────────────────────────────┘
```

**Header Components:**
- Logo (Home Assistant icon + "HA Config Manager")
- Global search bar
- Notification bell with badge
- User avatar with dropdown menu
- Theme toggle (light/dark)

**Sidebar Navigation:**
- Dashboard (mdi-view-dashboard)
- Servers (mdi-server)
- Deployments (mdi-rocket-launch)
- WLED (mdi-led-strip)
- FPP (mdi-play)
- Tailscale (mdi-vpn)
- ESPHome (mdi-chip)
- Backups (mdi-backup-restore)
- AI Assistant (mdi-robot)
- Secrets (mdi-shield-key)
- Audit Logs (mdi-file-document-outline)

---

## Pages & Features

### 1. Dashboard
**Route**: `/`

**Layout**:
```
┌────────────────┬────────────────┬────────────────┐
│ Total Servers  │ Deployments    │ Active Devices │
│  [Icon] 12     │  [Icon] 24     │  [Icon] 156    │
└────────────────┴────────────────┴────────────────┘

┌──────────────────────────────────────────────────┐
│ Recent Deployments                               │
│ ┌──────────────────────────────────────────────┐ │
│ │ ● server-1 | HA 2024.1 | Running | 2h ago   │ │
│ │ ● server-2 | HA 2023.12 | Stopped | 1d ago  │ │
│ └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘

┌────────────────┬─────────────────────────────────┐
│ Server Status  │ Resource Usage Chart            │
│ ● 10 Online    │ [Line Chart: CPU/Memory/Disk]   │
│ ● 2 Offline    │                                 │
└────────────────┴─────────────────────────────────┘
```

**Components**:
- **Statistics Cards** (4 cards):
  - Total servers, Deployments, Active devices, Backups
  - Icon, number, trend indicator (↑/↓)
- **Recent Activity Timeline**:
  - Last 10 operations with timestamps
  - Color-coded by type (deployment, backup, config change)
- **Server Status List**:
  - Server name, status badge, CPU/Memory bars
  - Click to navigate to server details
- **Resource Usage Charts**:
  - Line charts for CPU, Memory, Disk usage (last 24h)
  - Apexcharts or Chart.js

---

### 2. Servers Management
**Route**: `/servers`

**Features**:
- **Table View** with columns:
  - Name, IP Address, OS, Status, CPU, Memory, Last Seen, Actions
- **Add Server Button** (floating action button)
- **Search & Filter**:
  - Search by name/IP
  - Filter by status (online/offline)
  - Filter by OS
- **Actions**:
  - Edit, Delete, Test Connection, View Logs

**Dialogs**:
- **Add/Edit Server Dialog**:
  ```
  Name: [text field]
  IP Address: [text field]
  SSH Port: [number field] (default: 22)
  SSH User: [text field]
  SSH Password: [password field]
  SSH Key: [file upload or textarea]

  [Test Connection] [Cancel] [Save]
  ```
- **Delete Confirmation Dialog**
- **Connection Test Results Dialog**

---

### 3. Deployments
**Route**: `/deployments`

**Features**:
- **Card Grid View** (3-4 columns):
  ```
  ┌────────────────────────────┐
  │ server-1                   │
  │ HA Version: 2024.1.5       │
  │ Status: ● Running          │
  │ Port: 8123                 │
  │ ────────────────────────   │
  │ [Restart] [Logs] [Update]  │
  └────────────────────────────┘
  ```
- **Create Deployment Button**
- **Filters**: Status, HA Version, Server
- **Actions**: Restart, View Logs, Update, Delete

**Create Deployment Dialog**:
```
Server: [Select from list]
HA Version: [Dropdown: 2024.1, 2023.12, etc.]
Port: [number] (default: 8123)
Domain: [text] (optional)
Config Path: [text]
Auto Start: [checkbox]

[Cancel] [Deploy]
```

**Logs Dialog**:
- Real-time log streaming
- Auto-scroll toggle
- Download logs button
- Search/filter logs

---

### 4. WLED Controllers
**Route**: `/wled`

**Features**:
- **Device Cards** with controls:
  ```
  ┌─────────────────────────────┐
  │ Living Room LED             │
  │ ● Online | 192.168.1.100    │
  │                             │
  │ On/Off: [Toggle]            │
  │ Brightness: [Slider 0-255]  │
  │ Color: [Color Picker]       │
  │ Effect: [Dropdown]          │
  │ ─────────────────────────   │
  │ [Presets] [Schedule]        │
  └─────────────────────────────┘
  ```
- **Add Device**, **Bulk Actions**
- **Presets Management**:
  - Save current state as preset
  - Apply preset to single/multiple devices
- **Schedules**:
  - Time-based automation
  - Cron expression builder

---

### 5. FPP Controllers
**Route**: `/fpp`

**Features**:
- **Controller Cards**:
  - Status, IP, Current Playlist
  - Play/Pause/Stop buttons
  - Volume slider
- **Playlist Management**:
  - Create, Edit, Delete playlists
  - Add/remove sequences
  - Reorder items
- **Schedule Shows**:
  - Date/Time picker
  - Repeat options

---

### 6. Tailscale VPN
**Route**: `/tailscale`

**Features**:
- **Device List**:
  - Device name, IP (100.x.x.x), Status, Last Seen
  - Operating System icon
- **Connection Status**:
  - Connected/Disconnected badge
  - Connection quality indicator
- **Actions**:
  - Connect, Disconnect, Remove device

---

### 7. ESPHome Devices
**Route**: `/esphome`

**Features**:
- **Device Discovery**:
  - "Discover Devices" button (mDNS scan)
  - Progress indicator during scan
  - Auto-refresh device list
- **Device Table**:
  - Name, IP, Platform (ESP32/ESP8266), Version, Status
  - Actions: OTA Update, Logs, Delete
- **OTA Update Dialog**:
  ```
  Device: ESP32-001
  Current Version: 2023.12.0

  Firmware File: [File Upload]

  Password (if required): [Password field]

  [Upload Progress Bar]

  [Cancel] [Upload]
  ```
- **Real-time Logs**:
  - WebSocket connection
  - Color-coded log levels (DEBUG, INFO, WARNING, ERROR)
  - Auto-scroll, search, download

**Bulk Update**:
- Select multiple devices
- Upload single firmware to all
- Progress for each device

---

### 8. Backups
**Route**: `/backups`

**Three Tabs**:

#### Tab 1: Node-RED
```
┌─────────────────────────────────────────┐
│ Node-RED Instances                      │
│ ┌─────────────────────────────────────┐ │
│ │ Main Node-RED                       │ │
│ │ URL: http://192.168.1.50:1880       │ │
│ │ Last Backup: 2h ago                 │ │
│ │ [Backup Now] [Configure]            │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Backup History                          │
│ ┌─────────────────────────────────────┐ │
│ │ 2024-01-15 02:00 | 1.2MB | ✓       │ │
│ │ 2024-01-14 02:00 | 1.1MB | ✓       │ │
│ │ [Restore] [Download] [Delete]       │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### Tab 2: Zigbee2MQTT
- Same structure as Node-RED
- Shows Zigbee coordinator backup status

#### Tab 3: Schedules
```
┌─────────────────────────────────────────┐
│ Backup Schedules                        │
│ ┌─────────────────────────────────────┐ │
│ │ Daily at 2:00 AM                    │ │
│ │ Type: Node-RED                      │ │
│ │ Retention: 30 days                  │ │
│ │ Status: ● Active                    │ │
│ │ [Edit] [Delete]                     │ │
│ └─────────────────────────────────────┘ │
│ [+ Create Schedule]                     │
└─────────────────────────────────────────┘
```

**Create Schedule Dialog**:
- Config selection
- Backup type (Node-RED/Zigbee2MQTT)
- Cron expression (with visual builder)
- Retention days
- Active toggle

**Restore Dialog**:
- Backup selection
- Target path
- Overwrite confirmation
- Rollback option

---

### 9. AI Assistant
**Route**: `/ai`

**Layout**:
```
┌────────────────────────────────────────────┐
│ Conversation: "Server Management"         │
│ ┌────────────────────────────────────────┐ │
│ │ [Chat Messages]                        │ │
│ │                                        │ │
│ │ User: Create a server at 192.168.1.10 │ │
│ │ AI: I'll create a new server...       │ │
│ │                                        │ │
│ │ ┌────────────────────────────────────┐ │ │
│ │ │ Suggested Actions:                 │ │ │
│ │ │ ● Create server: production-1      │ │ │
│ │ │   IP: 192.168.1.10                 │ │ │
│ │ │   [Execute] [Cancel]               │ │ │
│ │ └────────────────────────────────────┘ │ │
│ └────────────────────────────────────────┘ │
│ [Type your message...]          [Send]     │
└────────────────────────────────────────────┘
```

**Features**:
- **Conversation List** (left sidebar, 200px):
  - Recent conversations
  - New conversation button
- **Chat Interface**:
  - Message bubbles (user: right-aligned, AI: left-aligned)
  - Markdown support in AI responses
  - Code blocks with syntax highlighting
- **Suggested Actions Panel**:
  - Action type, parameters
  - Execute button (requires confirmation)
  - Cancel button
- **Context Display**:
  - Current server, deployment (if any)
  - Shown at top of chat

**Action Confirmation Dialog**:
```
Execute Action?

Action: Create Server
Parameters:
  Name: production-1
  IP: 192.168.1.10
  SSH User: root

This action will:
- Create a new server entry
- Test SSH connection
- Add to server list

[Cancel] [Execute]
```

---

### 10. Secrets Management
**Route**: `/secrets`

**Statistics Cards** (top):
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Total        │ Active       │ Revoked      │ Rotation Req │
│ [Icon] 45    │ [Icon] 42    │ [Icon] 3     │ [Icon] 5     │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**Secrets Table**:
```
┌────────────────────────────────────────────────────────────┐
│ Name          │ Type     │ Status │ Last Accessed │ Actions │
│─────────────────────────────────────────────────────────────│
│ mqtt_password │ password │ Active │ 2h ago        │ [👁 🔄 ❌]│
│ api_key_prod  │ api_key  │ Active │ 1d ago        │ [👁 🔄 ❌]│
│ old_token     │ token    │Revoked │ 30d ago       │ [❌]    │
└────────────────────────────────────────────────────────────┘
```

**Actions**:
- 👁 **Decrypt & View**: Shows decrypted value with password toggle
- 🔄 **Rotate**: Update secret value
- ❌ **Revoke**: Mark as revoked (requires reason)
- ✏️ **Edit**: Update metadata only
- 🗑️ **Delete**: Permanent deletion

**Create Secret Dialog**:
```
Name: [text]
Type: [Select: API Key, Password, Token, Certificate, SSH Key]
Value: [Password field with toggle]
Description: [textarea]
Rotation Interval: [number] days (optional)
Tags: [Multi-select chips]

[Cancel] [Create]
```

**Decrypt Dialog**:
```
Secret: mqtt_password
Type: password

Decrypted Value:
[super-secret-password]  [👁 Show/Hide]

Access Count: 142
Last Accessed: 2 hours ago

[Close]
```

**Rotate Dialog**:
```
Rotate Secret: mqtt_password

Current value will be replaced.
This action is logged.

New Value: [Password field]

[Cancel] [Rotate]
```

**Revoke Dialog**:
```
Revoke Secret: old_token

⚠️ This action cannot be undone.
The secret will no longer be accessible.

Reason: [textarea, required]
Examples: Compromised, No longer needed, Security incident

[Cancel] [Revoke]
```

---

### 11. Audit Logs
**Route**: `/audit`

**Three Tabs**:

#### Tab 1: Audit Logs
```
┌────────────────────────────────────────────┐
│ Filters                                    │
│ Action: [Select]  Category: [Select]       │
│ Severity: [Select]  Status: [Select]       │
│ User: [Select]  Resource: [Select]         │
│ Date Range: [From] - [To]                  │
│ [Search] [Clear]                           │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ Timestamp      │ Action       │ User │ Status │ Details│
│────────────────────────────────────────────────────────│
│ 2024-01-15     │ create_      │admin │ Success│ [View] │
│ 10:30:15       │ server       │      │        │        │
│────────────────────────────────────────────────────────│
│ 2024-01-15     │ decrypt_     │user1 │ Success│ [View] │
│ 09:15:22       │ secret       │      │        │        │
└────────────────────────────────────────────────────────┘
```

**Audit Log Detail Dialog**:
```
Action: create_server
Category: server
Severity: info
Status: success

User: admin
Timestamp: 2024-01-15 10:30:15
IP Address: 192.168.1.50

Resource: Server #12 (production-1)

Changes:
  name: production-1
  ip_address: 192.168.1.10
  ssh_port: 22

[Close]
```

#### Tab 2: Security Events
```
┌────────────────────────────────────────────────────────┐
│ Type              │ Severity │ Status      │ Actions   │
│────────────────────────────────────────────────────────│
│ Unauthorized      │ HIGH     │ Unresolved  │ [Resolve] │
│ Access Attempt    │          │             │           │
│────────────────────────────────────────────────────────│
│ Brute Force       │ CRITICAL │ Investigating│ [Resolve]│
│ Detection         │          │             │           │
└────────────────────────────────────────────────────────┘
```

**Resolve Security Event Dialog**:
```
Event: Unauthorized Access Attempt
Severity: HIGH

Response Status: [Select: Investigating, Resolved, False Positive]

Response Notes: [textarea]
Explain what was found and what action was taken.

[Cancel] [Resolve]
```

#### Tab 3: Statistics
```
┌──────────────┬──────────────┬──────────────┐
│ Total Events │ Events Today │ Errors Today │
│ [Icon] 1,234 │ [Icon] 45    │ [Icon] 2     │
└──────────────┴──────────────┴──────────────┘

┌─────────────────────┬─────────────────────┐
│ Events by Category  │ Events by Severity  │
│ [Pie Chart]         │ [Donut Chart]       │
│                     │                     │
│ auth: 35%           │ info: 60%           │
│ server: 25%         │ warning: 25%        │
│ secret: 20%         │ error: 10%          │
│ deployment: 20%     │ critical: 5%        │
└─────────────────────┴─────────────────────┘
```

---

## UI Components Library

### 1. Data Display

**StatCard** - Statistics card with icon and number
```vue
<stat-card
  icon="mdi-server"
  title="Total Servers"
  value="12"
  trend="+2"
  color="primary"
/>
```

**StatusBadge** - Status indicator
```vue
<status-badge status="online" />
<!-- Colors: online=green, offline=grey, error=red -->
```

**DataTable** - Enhanced Vuetify table
```vue
<data-table
  :headers="headers"
  :items="items"
  :loading="loading"
  :search="search"
  @row-click="handleRowClick"
>
  <template #actions="{ item }">
    <v-btn icon="mdi-pencil" @click="edit(item)" />
    <v-btn icon="mdi-delete" @click="remove(item)" />
  </template>
</data-table>
```

### 2. Forms

**FormDialog** - Reusable dialog for forms
```vue
<form-dialog
  v-model="dialog"
  title="Create Server"
  :loading="loading"
  @submit="handleSubmit"
>
  <v-text-field label="Name" v-model="form.name" />
  <v-text-field label="IP Address" v-model="form.ip" />
</form-dialog>
```

**ConfirmDialog** - Confirmation dialog
```vue
<confirm-dialog
  v-model="confirmDialog"
  title="Delete Server"
  message="Are you sure you want to delete this server?"
  @confirm="handleDelete"
/>
```

### 3. Feedback

**LoadingOverlay** - Full-page loading
```vue
<loading-overlay :loading="loading" message="Deploying..." />
```

**Toast** - Success/Error notifications
```typescript
toast.success('Server created successfully');
toast.error('Failed to connect to server');
toast.warning('Server is offline');
toast.info('Deployment started');
```

**ProgressBar** - For file uploads, deployments
```vue
<progress-bar :value="progress" :text="`${progress}% uploaded`" />
```

### 4. Navigation

**Breadcrumbs** - Page navigation
```vue
<v-breadcrumbs :items="breadcrumbs" />
<!-- [Home] > [Servers] > [server-1] -->
```

**PageHeader** - Page title with actions
```vue
<page-header title="Servers" subtitle="Manage your HA servers">
  <template #actions>
    <v-btn color="primary" prepend-icon="mdi-plus">
      Add Server
    </v-btn>
  </template>
</page-header>
```

---

## API Integration

### Axios Setup

```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
});

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      router.push('/login');
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Store Example (Pinia)

```typescript
// src/stores/servers.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '@/services/api';

export const useServersStore = defineStore('servers', () => {
  const servers = ref<Server[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchServers() {
    loading.value = true;
    error.value = null;
    try {
      const response = await api.get('/servers');
      servers.value = response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch servers';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function createServer(data: ServerCreate) {
    loading.value = true;
    try {
      const response = await api.post('/servers', data);
      servers.value.push(response.data);
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create server';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  return {
    servers,
    loading,
    error,
    fetchServers,
    createServer,
  };
});
```

---

## Responsive Design

### Breakpoints
- **xs**: < 600px (mobile)
- **sm**: 600px - 960px (tablet portrait)
- **md**: 960px - 1264px (tablet landscape)
- **lg**: 1264px - 1904px (desktop)
- **xl**: > 1904px (large desktop)

### Mobile Adaptations
- Sidebar: Hidden on mobile, accessible via hamburger menu
- Tables: Horizontal scroll or card view on mobile
- Dialogs: Full-screen on mobile
- Charts: Stacked on mobile, side-by-side on desktop
- Form fields: Full width on mobile

---

## Accessibility

- **ARIA Labels**: All interactive elements
- **Keyboard Navigation**: Full tab support
- **Focus Indicators**: Visible focus rings
- **Color Contrast**: WCAG AA compliant
- **Screen Reader**: Alt text for images, ARIA labels

---

## Performance

- **Code Splitting**: Route-based lazy loading
- **Virtual Scrolling**: For long lists (1000+ items)
- **Debounce**: Search inputs (300ms)
- **Memoization**: Computed properties for expensive operations
- **Image Optimization**: WebP format, lazy loading

---

## Security

- **XSS Protection**: Sanitize user input
- **CSRF Tokens**: For state-changing operations
- **Secure Storage**: Encrypt sensitive data in localStorage
- **Auth Token**: HttpOnly cookies (if possible) or secure localStorage
- **Input Validation**: Client-side validation before API calls

---

## Additional Features

### Dark Mode
- Toggle in header
- Persisted in localStorage
- Smooth transition between themes
- All colors have dark mode variants

### Notifications
- Real-time notifications (WebSocket or polling)
- Badge count on bell icon
- Mark as read functionality
- Notification types: info, success, warning, error

### Search
- Global search in header
- Searches: servers, deployments, devices, secrets
- Recent searches dropdown
- Keyboard shortcut: Cmd/Ctrl + K

### Help & Documentation
- Help icon in header
- Context-sensitive help tooltips
- Link to documentation
- Keyboard shortcuts guide (? key)

---

## Example Page Implementation

```vue
<!-- src/views/ServersView.vue -->
<template>
  <v-container fluid>
    <page-header title="Servers" subtitle="Manage your HA servers">
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
          Add Server
        </v-btn>
      </template>
    </page-header>

    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Search servers"
              single-line
              hide-details
              clearable
            ></v-text-field>
          </v-card-title>

          <v-data-table
            :headers="headers"
            :items="serversStore.servers"
            :loading="serversStore.loading"
            :search="search"
            class="elevation-1"
          >
            <template v-slot:item.status="{ item }">
              <status-badge :status="item.status" />
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn icon="mdi-pencil" size="small" @click="edit(item)"></v-btn>
              <v-btn icon="mdi-delete" size="small" @click="remove(item)" color="error"></v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit Dialog -->
    <form-dialog
      v-model="dialog"
      :title="editMode ? 'Edit Server' : 'Create Server'"
      @submit="handleSubmit"
    >
      <v-form ref="form">
        <v-text-field
          v-model="formData.name"
          label="Server Name"
          :rules="[rules.required]"
          required
        ></v-text-field>

        <v-text-field
          v-model="formData.ip_address"
          label="IP Address"
          :rules="[rules.required, rules.ip]"
          required
        ></v-text-field>

        <v-text-field
          v-model.number="formData.ssh_port"
          label="SSH Port"
          type="number"
          :rules="[rules.required]"
        ></v-text-field>

        <v-text-field
          v-model="formData.ssh_user"
          label="SSH User"
          :rules="[rules.required]"
        ></v-text-field>

        <v-text-field
          v-model="formData.ssh_password"
          label="SSH Password"
          type="password"
        ></v-text-field>
      </v-form>
    </form-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useServersStore } from '@/stores/servers';

const serversStore = useServersStore();

const search = ref('');
const dialog = ref(false);
const editMode = ref(false);
const formData = ref({
  name: '',
  ip_address: '',
  ssh_port: 22,
  ssh_user: 'root',
  ssh_password: '',
});

const headers = [
  { title: 'Name', key: 'name' },
  { title: 'IP Address', key: 'ip_address' },
  { title: 'Status', key: 'status' },
  { title: 'CPU', key: 'cpu_usage' },
  { title: 'Memory', key: 'memory_usage' },
  { title: 'Actions', key: 'actions', sortable: false },
];

const rules = {
  required: (value: any) => !!value || 'Required',
  ip: (value: string) => {
    const pattern = /^(\d{1,3}\.){3}\d{1,3}$/;
    return pattern.test(value) || 'Invalid IP address';
  },
};

function openCreateDialog() {
  editMode.value = false;
  formData.value = {
    name: '',
    ip_address: '',
    ssh_port: 22,
    ssh_user: 'root',
    ssh_password: '',
  };
  dialog.value = true;
}

async function handleSubmit() {
  try {
    await serversStore.createServer(formData.value);
    dialog.value = false;
    toast.success('Server created successfully');
  } catch (error) {
    toast.error('Failed to create server');
  }
}

onMounted(() => {
  serversStore.fetchServers();
});
</script>
```

---

## Testing Requirements

- **Unit Tests**: Vitest for components and stores
- **E2E Tests**: Playwright or Cypress
- **Coverage**: Minimum 70%
- **Accessibility Tests**: axe-core integration

---

## Build & Deployment

```bash
# Development
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Lint
npm run lint
```

---

## File Structure

```
dashboard/
├── public/
│   ├── manifest.json
│   ├── service-worker.js
│   └── icons/
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── common/
│   │   │   ├── StatCard.vue
│   │   │   ├── StatusBadge.vue
│   │   │   ├── DataTable.vue
│   │   │   └── ...
│   │   └── forms/
│   │       ├── FormDialog.vue
│   │       ├── ConfirmDialog.vue
│   │       └── ...
│   ├── views/
│   │   ├── DashboardView.vue
│   │   ├── ServersView.vue
│   │   ├── DeploymentsView.vue
│   │   └── ...
│   ├── stores/
│   │   ├── auth.ts
│   │   ├── servers.ts
│   │   ├── deployments.ts
│   │   └── ...
│   ├── router/
│   │   └── index.ts
│   ├── services/
│   │   ├── api.ts
│   │   └── toast.ts
│   ├── types/
│   │   ├── server.ts
│   │   ├── deployment.ts
│   │   └── ...
│   ├── App.vue
│   └── main.ts
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

---

## Priority Features (MVP)

1. ✅ Dashboard with statistics
2. ✅ Servers management (CRUD)
3. ✅ Deployments management
4. ✅ Dark mode toggle
5. ✅ Responsive sidebar
6. ✅ Authentication (login/register)

## Phase 2 Features

1. ✅ WLED control
2. ✅ FPP control
3. ✅ Tailscale integration
4. ✅ Real-time status updates

## Phase 3 Features

1. ✅ AI Assistant chat
2. ✅ ESPHome OTA updates
3. ✅ Backups management
4. ✅ Secrets management
5. ✅ Audit logs

---

This comprehensive prompt provides all the details needed to create a production-ready, enterprise-grade frontend for HA Config Manager using v0 or Lovable. Follow Material Design principles, maintain consistency across all pages, and ensure excellent UX/UI quality throughout the application.
