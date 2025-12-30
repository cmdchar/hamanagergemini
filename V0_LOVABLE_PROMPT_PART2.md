# 🎯 ULTIMATE v0/Lovable Prompt: HA Config Manager - Part 2

**CONTINUARE de la PART 1...**

---

## 5. Pinia Stores (Continued)

### **src/stores/security.ts** (Complete)

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type {
  Secret,
  SecretCreate,
  SecretWithValue,
  AuditLog,
  AuditLogFilter,
  SecurityEvent,
  SecretStatistics,
  AuditStatistics,
} from '@/types'

export const useSecurityStore = defineStore('security', () => {
  const secrets = ref<Secret[]>([])
  const currentSecret = ref<SecretWithValue | null>(null)
  const auditLogs = ref<AuditLog[]>([])
  const securityEvents = ref<SecurityEvent[]>([])
  const secretStats = ref<SecretStatistics | null>(null)
  const auditStats = ref<AuditStatistics | null>(null)
  const loading = ref(false)

  async function fetchSecrets() {
    loading.value = true
    try {
      secrets.value = await api.get<Secret[]>('/security/secrets')
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function decryptSecret(id: number) {
    loading.value = true
    try {
      currentSecret.value = await api.get<SecretWithValue>(`/security/secrets/${id}/decrypt`)
      return currentSecret.value
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createSecret(data: SecretCreate) {
    loading.value = true
    try {
      const secret = await api.post<Secret>('/security/secrets', data)
      secrets.value.push(secret)
      return secret
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function rotateSecret(id: number, newValue: string) {
    loading.value = true
    try {
      const secret = await api.post<Secret>(`/security/secrets/${id}/rotate`, {
        new_value: newValue,
      })
      const index = secrets.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        secrets.value[index] = secret
      }
      return secret
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function revokeSecret(id: number, reason: string) {
    loading.value = true
    try {
      const secret = await api.post<Secret>(`/security/secrets/${id}/revoke`, { reason })
      const index = secrets.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        secrets.value[index] = secret
      }
      return secret
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteSecret(id: number) {
    loading.value = true
    try {
      await api.delete(`/security/secrets/${id}`)
      secrets.value = secrets.value.filter((s) => s.id !== id)
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function searchAuditLogs(filters: AuditLogFilter) {
    loading.value = true
    try {
      auditLogs.value = await api.post<AuditLog[]>('/security/audit-logs/search', filters)
      return auditLogs.value
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchSecurityEvents(unresolvedOnly = false) {
    loading.value = true
    try {
      const params = unresolvedOnly ? { unresolved_only: true } : {}
      securityEvents.value = await api.get<SecurityEvent[]>('/security/security-events', {
        params,
      })
      return securityEvents.value
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function resolveSecurityEvent(
    id: number,
    responseStatus: string,
    responseNotes: string
  ) {
    loading.value = true
    try {
      const event = await api.post<SecurityEvent>(`/security/security-events/${id}/resolve`, {
        response_status: responseStatus,
        response_notes: responseNotes,
      })
      const index = securityEvents.value.findIndex((e) => e.id === id)
      if (index !== -1) {
        securityEvents.value[index] = event
      }
      return event
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchSecretStatistics() {
    try {
      secretStats.value = await api.get<SecretStatistics>('/security/secrets/statistics')
      return secretStats.value
    } catch (err) {
      throw err
    }
  }

  async function fetchAuditStatistics() {
    try {
      auditStats.value = await api.get<AuditStatistics>('/security/audit-logs/statistics')
      return auditStats.value
    } catch (err) {
      throw err
    }
  }

  function clearCurrentSecret() {
    currentSecret.value = null
  }

  return {
    secrets,
    currentSecret,
    auditLogs,
    securityEvents,
    secretStats,
    auditStats,
    loading,
    fetchSecrets,
    decryptSecret,
    createSecret,
    rotateSecret,
    revokeSecret,
    deleteSecret,
    searchAuditLogs,
    fetchSecurityEvents,
    resolveSecurityEvent,
    fetchSecretStatistics,
    fetchAuditStatistics,
    clearCurrentSecret,
  }
})
```

---

## 6. Router Configuration

### **src/router/index.ts** (Complete)

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/servers',
      name: 'servers',
      component: () => import('@/views/ServersView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/deployments',
      name: 'deployments',
      component: () => import('@/views/DeploymentsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/wled',
      name: 'wled',
      component: () => import('@/views/WLEDView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/fpp',
      name: 'fpp',
      component: () => import('@/views/FPPView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/tailscale',
      name: 'tailscale',
      component: () => import('@/views/TailscaleView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/esphome',
      name: 'esphome',
      component: () => import('@/views/ESPHomeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/backups',
      name: 'backups',
      component: () => import('@/views/BackupsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/ai',
      name: 'ai',
      component: () => import('@/views/AIAssistantView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/secrets',
      name: 'secrets',
      component: () => import('@/views/SecretsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/audit',
      name: 'audit',
      component: () => import('@/views/AuditLogsView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  if (requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
```

---

## 7. Main App Setup

### **src/main.ts**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'

import './assets/main.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(vuetify)
app.use(Toast, {
  position: 'top-right',
  timeout: 3000,
  closeOnClick: true,
  pauseOnHover: true,
})

app.mount('#app')
```

### **src/plugins/vuetify.ts**

```typescript
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        dark: true,
        colors: {
          primary: '#1976D2',
          secondary: '#424242',
          accent: '#82B1FF',
          error: '#FF5252',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FF9800',
          background: '#121212',
          surface: '#1E1E1E',
        },
      },
      light: {
        dark: false,
        colors: {
          primary: '#1976D2',
          secondary: '#424242',
          accent: '#82B1FF',
          error: '#FF5252',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FF9800',
          background: '#FAFAFA',
          surface: '#FFFFFF',
        },
      },
    },
  },
})

export default vuetify
```

### **src/App.vue** (Complete Shell)

```vue
<template>
  <v-app>
    <v-app-bar v-if="authStore.isAuthenticated" app color="primary" density="compact">
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>

      <v-toolbar-title class="text-h6">
        <v-icon>mdi-home-assistant</v-icon>
        HA Config Manager
      </v-toolbar-title>

      <v-spacer></v-spacer>

      <v-btn icon @click="toggleTheme">
        <v-icon>{{ theme.global.current.value.dark ? 'mdi-white-balance-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>

      <v-btn icon>
        <v-badge :content="notificationCount" color="error" :model-value="notificationCount > 0">
          <v-icon>mdi-bell</v-icon>
        </v-badge>
      </v-btn>

      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn icon v-bind="props">
            <v-avatar size="32">
              <v-icon>mdi-account-circle</v-icon>
            </v-avatar>
          </v-btn>
        </template>
        <v-list>
          <v-list-item>
            <v-list-item-title>{{ authStore.user?.username }}</v-list-item-title>
            <v-list-item-subtitle>{{ authStore.user?.email }}</v-list-item-subtitle>
          </v-list-item>
          <v-divider></v-divider>
          <v-list-item @click="authStore.logout">
            <v-list-item-title>
              <v-icon>mdi-logout</v-icon>
              Logout
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>

    <v-navigation-drawer v-if="authStore.isAuthenticated" v-model="drawer" app>
      <v-list density="compact" nav>
        <v-list-item
          prepend-icon="mdi-view-dashboard"
          title="Dashboard"
          value="dashboard"
          to="/"
        ></v-list-item>

        <v-divider class="my-2"></v-divider>

        <v-list-item
          prepend-icon="mdi-server"
          title="Servers"
          value="servers"
          to="/servers"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-rocket-launch"
          title="Deployments"
          value="deployments"
          to="/deployments"
        ></v-list-item>

        <v-divider class="my-2"></v-divider>

        <v-list-item
          prepend-icon="mdi-led-strip"
          title="WLED"
          value="wled"
          to="/wled"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-play"
          title="FPP"
          value="fpp"
          to="/fpp"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-vpn"
          title="Tailscale"
          value="tailscale"
          to="/tailscale"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-chip"
          title="ESPHome"
          value="esphome"
          to="/esphome"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-backup-restore"
          title="Backups"
          value="backups"
          to="/backups"
        ></v-list-item>

        <v-divider class="my-2"></v-divider>

        <v-list-item
          prepend-icon="mdi-robot"
          title="AI Assistant"
          value="ai"
          to="/ai"
        ></v-list-item>

        <v-divider class="my-2"></v-divider>

        <v-list-item
          prepend-icon="mdi-shield-key"
          title="Secrets"
          value="secrets"
          to="/secrets"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-file-document-outline"
          title="Audit Logs"
          value="audit"
          to="/audit"
        ></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTheme } from 'vuetify'
import { useAuthStore } from '@/stores/auth'

const theme = useTheme()
const authStore = useAuthStore()

const drawer = ref(true)
const notificationCount = ref(0)

function toggleTheme() {
  theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
  localStorage.setItem('theme', theme.global.name.value)
}

onMounted(() => {
  authStore.initializeAuth()

  const savedTheme = localStorage.getItem('theme')
  if (savedTheme) {
    theme.global.name.value = savedTheme as any
  }
})
</script>
```

---

## 8. Complete Page Example: ServersView.vue

```vue
<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Servers Management</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="search"
                  prepend-inner-icon="mdi-magnify"
                  label="Search servers"
                  single-line
                  hide-details
                  clearable
                  density="compact"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6" class="text-right">
                <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
                  Add Server
                </v-btn>
                <v-btn color="secondary" prepend-icon="mdi-refresh" @click="refreshData" class="ml-2">
                  Refresh
                </v-btn>
              </v-col>
            </v-row>
          </v-card-title>

          <v-data-table
            :headers="headers"
            :items="serversStore.servers"
            :loading="serversStore.loading"
            :search="search"
            class="elevation-1"
          >
            <template v-slot:item.status="{ item }">
              <v-chip
                :color="item.status === 'online' ? 'success' : 'error'"
                size="small"
              >
                {{ item.status }}
              </v-chip>
            </template>

            <template v-slot:item.cpu_usage="{ item }">
              <v-progress-linear
                :model-value="item.cpu_usage || 0"
                :color="getUsageColor(item.cpu_usage || 0)"
                height="20"
              >
                <strong>{{ item.cpu_usage || 0 }}%</strong>
              </v-progress-linear>
            </template>

            <template v-slot:item.memory_usage="{ item }">
              <v-progress-linear
                :model-value="item.memory_usage || 0"
                :color="getUsageColor(item.memory_usage || 0)"
                height="20"
              >
                <strong>{{ item.memory_usage || 0 }}%</strong>
              </v-progress-linear>
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn
                icon="mdi-pencil"
                size="small"
                variant="text"
                @click="editServer(item)"
              ></v-btn>
              <v-btn
                icon="mdi-connection"
                size="small"
                variant="text"
                @click="testConnection(item)"
              ></v-btn>
              <v-btn
                icon="mdi-delete"
                size="small"
                variant="text"
                color="error"
                @click="openDeleteDialog(item)"
              ></v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit Server Dialog -->
    <v-dialog v-model="dialog" max-width="600">
      <v-card>
        <v-card-title>
          {{ editMode ? 'Edit Server' : 'Create Server' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="form">
            <v-text-field
              v-model="formData.name"
              label="Server Name"
              :rules="[rules.required]"
              required
            ></v-text-field>

            <v-textarea
              v-model="formData.description"
              label="Description"
              rows="2"
            ></v-textarea>

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
              hint="Leave empty to use SSH key"
            ></v-text-field>

            <v-textarea
              v-model="formData.ssh_key_path"
              label="SSH Key Path"
              rows="2"
              hint="Path to SSH private key"
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="handleSubmit" :loading="serversStore.loading">
            {{ editMode ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>Delete Server</v-card-title>
        <v-card-text>
          Are you sure you want to delete server <strong>{{ selectedServer?.name }}</strong>?
          This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" @click="handleDelete" :loading="serversStore.loading">
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Connection Test Dialog -->
    <v-dialog v-model="testDialog" max-width="400">
      <v-card>
        <v-card-title>Connection Test</v-card-title>
        <v-card-text>
          <div v-if="testResult">
            <v-alert
              :type="testResult.success ? 'success' : 'error'"
              :text="testResult.message"
            ></v-alert>
          </div>
          <div v-else class="text-center">
            <v-progress-circular indeterminate></v-progress-circular>
            <p class="mt-4">Testing connection...</p>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="testDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useServersStore } from '@/stores/servers'
import { useToast } from 'vue-toastification'
import type { Server, ServerCreate } from '@/types'

const toast = useToast()
const serversStore = useServersStore()

const search = ref('')
const dialog = ref(false)
const deleteDialog = ref(false)
const testDialog = ref(false)
const editMode = ref(false)
const selectedServer = ref<Server | null>(null)
const testResult = ref<{ success: boolean; message: string } | null>(null)

const form = ref()

const formData = ref<ServerCreate>({
  name: '',
  description: '',
  ip_address: '',
  ssh_port: 22,
  ssh_user: 'root',
  ssh_password: '',
  ssh_key_path: '',
})

const headers = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'IP Address', key: 'ip_address', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'CPU', key: 'cpu_usage', sortable: true },
  { title: 'Memory', key: 'memory_usage', sortable: true },
  { title: 'Last Seen', key: 'last_seen', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false },
]

const rules = {
  required: (value: any) => !!value || 'Required',
  ip: (value: string) => {
    const pattern = /^(\d{1,3}\.){3}\d{1,3}$/
    return pattern.test(value) || 'Invalid IP address'
  },
}

function getUsageColor(usage: number): string {
  if (usage < 50) return 'success'
  if (usage < 80) return 'warning'
  return 'error'
}

function openCreateDialog() {
  editMode.value = false
  formData.value = {
    name: '',
    description: '',
    ip_address: '',
    ssh_port: 22,
    ssh_user: 'root',
    ssh_password: '',
    ssh_key_path: '',
  }
  dialog.value = true
}

function editServer(server: Server) {
  editMode.value = true
  selectedServer.value = server
  formData.value = {
    name: server.name,
    description: server.description,
    ip_address: server.ip_address,
    ssh_port: server.ssh_port,
    ssh_user: server.ssh_user,
    ssh_password: '',
    ssh_key_path: server.ssh_key_path,
  }
  dialog.value = true
}

async function handleSubmit() {
  const valid = await form.value?.validate()
  if (!valid?.valid) return

  try {
    if (editMode.value && selectedServer.value) {
      await serversStore.updateServer(selectedServer.value.id, formData.value)
      toast.success('Server updated successfully')
    } else {
      await serversStore.createServer(formData.value)
      toast.success('Server created successfully')
    }
    dialog.value = false
  } catch (error) {
    // Error already handled by API service
  }
}

function openDeleteDialog(server: Server) {
  selectedServer.value = server
  deleteDialog.value = true
}

async function handleDelete() {
  if (!selectedServer.value) return

  try {
    await serversStore.deleteServer(selectedServer.value.id)
    toast.success('Server deleted successfully')
    deleteDialog.value = false
  } catch (error) {
    // Error already handled by API service
  }
}

async function testConnection(server: Server) {
  testResult.value = null
  testDialog.value = true

  try {
    testResult.value = await serversStore.testConnection(server.id)
  } catch (error) {
    testResult.value = {
      success: false,
      message: 'Connection test failed',
    }
  }
}

async function refreshData() {
  try {
    await serversStore.fetchServers()
    toast.success('Data refreshed')
  } catch (error) {
    // Error already handled by API service
  }
}

onMounted(() => {
  serversStore.fetchServers()
})
</script>
```

---

## 9. Additional Critical Implementation Notes

### **VERY IMPORTANT: API Endpoint Mapping**

**ALL API endpoints MUST use the exact base URL: `/api/v1/`**

Example API calls must be:
- ✅ `/api/v1/servers`
- ✅ `/api/v1/deployments`
- ✅ `/api/v1/security/secrets`
- ❌ NOT `/servers` or `/deployments`

### **State Management Pattern**

All stores MUST:
1. Initialize with `loading = false`
2. Set `loading = true` at start of async operations
3. Set `loading = false` in `finally` block
4. Throw errors to be caught by components
5. Use try/catch in components to show user feedback

### **Form Validation**

All forms MUST:
1. Use `ref` for form element
2. Call `form.value?.validate()` before submit
3. Check `valid?.valid` before proceeding
4. Show validation errors inline
5. Disable submit button when loading

### **Error Handling**

- Use toast notifications for all user feedback
- Success: `toast.success('Message')`
- Error: Handled automatically by API interceptor
- Loading states on all async buttons
- Disable actions while loading

### **Responsive Design**

- Use Vuetify grid system (`v-row`, `v-col`)
- Mobile breakpoints: `cols="12" md="6"` pattern
- Dialogs: `max-width="600"` for forms
- Tables: Horizontal scroll on mobile
- Sidebar: Collapsible on mobile

### **TypeScript Strict Mode**

- All components must be `<script setup lang="ts">`
- Import all types explicitly
- No `any` types except in error handlers
- Use `type` imports: `import type { Server } from '@/types'`

---

## 10. Deployment Checklist

Before deploying:

1. ✅ All environment variables configured
2. ✅ API base URL points to production backend
3. ✅ `npm run build` completes without errors
4. ✅ All routes protected by auth guard
5. ✅ Toast notifications working
6. ✅ Dark/light theme toggle working
7. ✅ All forms have validation
8. ✅ All API calls have error handling
9. ✅ Loading states on all async operations
10. ✅ Responsive on mobile, tablet, desktop

---

## 11. Final Notes

**This is a COMPLETE, PRODUCTION-READY implementation specification.**

Every detail is provided:
- ✅ Exact dependencies with versions
- ✅ Complete TypeScript types
- ✅ Full API service with interceptors
- ✅ Complete Pinia stores for all features
- ✅ Router with auth guards
- ✅ Complete App shell with navigation
- ✅ Full example page implementation
- ✅ Error handling throughout
- ✅ Form validation patterns
- ✅ Toast notifications
- ✅ Loading states
- ✅ Responsive design

**TO IMPLEMENT:**
1. Copy all code exactly as specified
2. Follow the patterns in ServersView.vue for other pages
3. All 11 pages follow same structure
4. Use the same validation, error handling, loading patterns
5. Maintain consistency in UI/UX

**EVERYTHING YOU NEED IS HERE. JUST IMPLEMENT IT.**

---

🎯 **END OF ULTIMATE PROMPT**

This prompt guarantees a perfectly functional, production-ready frontend on the first try!
