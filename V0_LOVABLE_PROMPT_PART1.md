# 🎯 ULTIMATE v0/Lovable Prompt: HA Config Manager - Perfect Frontend

> **OBIECTIV**: Creează un frontend Vue 3 + TypeScript + Vuetify 3 complet funcțional, production-ready, care se conectează la API-ul HA Config Manager și oferă toate funcționalitățile necesare pentru management Home Assistant.

---

## 📋 Table of Contents

1. [Project Setup & Dependencies](#1-project-setup--dependencies)
2. [Environment & Configuration](#2-environment--configuration)
3. [TypeScript Types & Interfaces](#3-typescript-types--interfaces)
4. [API Service Layer](#4-api-service-layer)
5. [Pinia Stores (Complete)](#5-pinia-stores-complete)
6. [Router Configuration](#6-router-configuration)
7. [Layout & Shell Components](#7-layout--shell-components)
8. [All 11 Pages (Complete Implementation)](#8-all-11-pages-complete-implementation)
9. [Reusable Components](#9-reusable-components)
10. [Styling & Theming](#10-styling--theming)
11. [Error Handling & Validation](#11-error-handling--validation)
12. [Testing Requirements](#12-testing-requirements)

---

## 1. Project Setup & Dependencies

### **package.json** (Complete)

```json
{
  "name": "ha-config-manager-dashboard",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix --ignore-path .gitignore",
    "type-check": "vue-tsc --noEmit"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "vuetify": "^3.5.0",
    "axios": "^1.6.0",
    "@mdi/font": "^7.4.0",
    "chart.js": "^4.4.0",
    "vue-chartjs": "^5.3.0",
    "date-fns": "^3.0.0",
    "vue-toastification": "^2.0.0-rc.5"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "@vitejs/plugin-vue": "^5.0.0",
    "@vue/eslint-config-typescript": "^12.0.0",
    "eslint": "^8.55.0",
    "eslint-plugin-vue": "^9.19.0",
    "typescript": "~5.3.0",
    "vite": "^5.0.0",
    "vite-plugin-vuetify": "^2.0.0",
    "vue-tsc": "^1.8.27"
  }
}
```

### **vite.config.ts**

```typescript
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'

export default defineConfig({
  plugins: [
    vue(),
    vuetify({ autoImport: true }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### **tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

## 2. Environment & Configuration

### **.env.development**

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=HA Config Manager
VITE_APP_VERSION=1.0.0
```

### **.env.production**

```bash
VITE_API_BASE_URL=/api/v1
VITE_APP_TITLE=HA Config Manager
VITE_APP_VERSION=1.0.0
```

---

## 3. TypeScript Types & Interfaces

### **src/types/index.ts** (Complete Types)

```typescript
// ============================================
// USER & AUTH TYPES
// ============================================

export interface User {
  id: number
  email: string
  username: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
}

// ============================================
// SERVER TYPES
// ============================================

export interface Server {
  id: number
  name: string
  description?: string
  ip_address: string
  ssh_port: number
  ssh_user: string
  ssh_password?: string
  ssh_key_path?: string
  os_type?: string
  os_version?: string
  status: 'online' | 'offline' | 'unknown'
  last_seen?: string
  cpu_usage?: number
  memory_usage?: number
  disk_usage?: number
  uptime?: number
  created_at: string
  updated_at: string
}

export interface ServerCreate {
  name: string
  description?: string
  ip_address: string
  ssh_port: number
  ssh_user: string
  ssh_password?: string
  ssh_key_path?: string
}

export interface ServerUpdate {
  name?: string
  description?: string
  ip_address?: string
  ssh_port?: number
  ssh_user?: string
  ssh_password?: string
}

// ============================================
// DEPLOYMENT TYPES
// ============================================

export interface Deployment {
  id: number
  name: string
  server_id: number
  ha_version: string
  port: number
  domain?: string
  ssl_enabled: boolean
  auto_restart: boolean
  status: 'running' | 'stopped' | 'error' | 'deploying'
  config_path: string
  install_path: string
  pm2_id?: string
  last_restart?: string
  error_message?: string
  created_at: string
  updated_at: string
  server?: Server
}

export interface DeploymentCreate {
  name: string
  server_id: number
  ha_version: string
  port: number
  domain?: string
  ssl_enabled: boolean
  auto_restart: boolean
  config_path?: string
}

export interface DeploymentUpdate {
  name?: string
  ha_version?: string
  port?: number
  domain?: string
  auto_restart?: boolean
}

// ============================================
// WLED TYPES
// ============================================

export interface WLEDDevice {
  id: number
  name: string
  ip_address: string
  port: number
  mac_address?: string
  version?: string
  status: 'online' | 'offline'
  brightness: number
  is_on: boolean
  current_preset?: number
  current_effect?: string
  color_primary?: string
  created_at: string
  updated_at: string
}

export interface WLEDDeviceCreate {
  name: string
  ip_address: string
  port: number
}

export interface WLEDState {
  on: boolean
  brightness: number
  color?: { r: number; g: number; b: number }
  effect?: string
  preset?: number
}

export interface WLEDPreset {
  id: number
  name: string
  device_id?: number
  brightness: number
  effect: string
  color_primary: string
  color_secondary?: string
  speed: number
  intensity: number
  created_at: string
}

export interface WLEDSchedule {
  id: number
  name: string
  device_id: number
  preset_id: number
  time: string
  days: number[]
  is_active: boolean
  created_at: string
}

// ============================================
// ESPHOME TYPES
// ============================================

export interface ESPHomeDevice {
  id: number
  name: string
  ip_address: string
  mac_address: string
  platform: 'esp32' | 'esp8266'
  version: string
  status: 'online' | 'offline' | 'updating'
  created_at: string
  updated_at: string
}

export interface ESPHomeOTAUpdate {
  id: number
  device_id: number
  firmware_id: number
  status: 'pending' | 'uploading' | 'installing' | 'completed' | 'failed'
  progress_percent: number
  error_message?: string
  started_at: string
  completed_at?: string
}

export interface ESPHomeFirmware {
  id: number
  device_id?: number
  version: string
  file_path: string
  file_size: number
  checksum: string
  created_at: string
}

// ============================================
// BACKUP TYPES
// ============================================

export interface NodeREDConfig {
  id: number
  name: string
  url: string
  flows_path: string
  credentials_path?: string
  settings_path?: string
  created_at: string
}

export interface Zigbee2MQTTConfig {
  id: number
  name: string
  config_path: string
  data_path: string
  mqtt_server: string
  created_at: string
}

export interface Backup {
  id: number
  backup_type: 'nodered' | 'zigbee2mqtt'
  config_id: number
  file_path: string
  file_size: number
  checksum: string
  status: 'pending' | 'completed' | 'failed'
  error_message?: string
  created_at: string
}

export interface BackupSchedule {
  id: number
  config_id: number
  backup_type: 'nodered' | 'zigbee2mqtt'
  cron_expression: string
  retention_days: number
  is_active: boolean
  last_run?: string
  next_run?: string
  created_at: string
}

export interface BackupRestore {
  id: number
  backup_id: number
  target_path: string
  status: 'pending' | 'restoring' | 'completed' | 'failed' | 'rolled_back'
  pre_restore_backup_id?: number
  error_message?: string
  created_at: string
}

// ============================================
// AI ASSISTANT TYPES
// ============================================

export interface AIConversation {
  id: number
  title: string
  user_id: number
  deployment_id?: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AIMessage {
  id: number
  conversation_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  suggested_actions?: AIAction[]
  created_at: string
}

export interface AIAction {
  id: number
  conversation_id: number
  action_type: string
  parameters: Record<string, any>
  result?: Record<string, any>
  status: 'pending' | 'executing' | 'completed' | 'failed'
  requires_confirmation: boolean
  error_message?: string
  created_at: string
}

export interface AIChatRequest {
  message: string
  context?: Record<string, any>
}

export interface AIChatResponse {
  message: AIMessage
  suggested_actions?: AIAction[]
  requires_confirmation: boolean
}

// ============================================
// SECURITY TYPES
// ============================================

export interface Secret {
  id: number
  name: string
  description?: string
  secret_type: 'api_key' | 'password' | 'token' | 'certificate' | 'ssh_key' | 'other'
  encryption_version: number
  encryption_algorithm: string
  server_id?: number
  deployment_id?: number
  expires_at?: string
  last_rotated?: string
  rotation_interval_days?: number
  rotation_required: boolean
  last_accessed?: string
  access_count: number
  is_active: boolean
  is_revoked: boolean
  revoked_at?: string
  revoked_reason?: string
  tags?: string[]
  created_at: string
  updated_at: string
}

export interface SecretCreate {
  name: string
  value: string
  secret_type: string
  description?: string
  rotation_interval_days?: number
  tags?: string[]
}

export interface SecretWithValue extends Secret {
  value: string
}

export interface AuditLog {
  id: number
  action: string
  category: string
  severity: 'info' | 'warning' | 'error' | 'critical'
  status: 'success' | 'failure' | 'partial'
  user_id?: number
  service?: string
  resource_type?: string
  resource_id?: number
  resource_name?: string
  description: string
  changes?: Record<string, any>
  error_details?: string
  ip_address?: string
  user_agent?: string
  created_at: string
}

export interface AuditLogFilter {
  action?: string
  category?: string
  severity?: string
  status?: string
  user_id?: number
  resource_type?: string
  resource_id?: number
  start_date?: string
  end_date?: string
}

export interface SecurityEvent {
  id: number
  event_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  description: string
  source_ip?: string
  source_user_id?: number
  response_required: boolean
  response_status?: 'pending' | 'investigating' | 'resolved' | 'false_positive'
  responded_at?: string
  response_notes?: string
  created_at: string
}

// ============================================
// STATISTICS TYPES
// ============================================

export interface DashboardStats {
  total_servers: number
  online_servers: number
  offline_servers: number
  total_deployments: number
  running_deployments: number
  total_devices: number
  total_backups: number
  recent_deployments: Deployment[]
  recent_activities: ActivityItem[]
}

export interface ActivityItem {
  id: number
  type: string
  description: string
  timestamp: string
  user?: string
  status: 'success' | 'error' | 'warning'
}

export interface SecretStatistics {
  total_secrets: number
  active_secrets: number
  revoked_secrets: number
  secrets_by_type: Record<string, number>
  secrets_requiring_rotation: number
  total_accesses_today: number
}

export interface AuditStatistics {
  total_events: number
  events_by_category: Record<string, number>
  events_by_severity: Record<string, number>
  events_today: number
  errors_today: number
}

// ============================================
// API RESPONSE TYPES
// ============================================

export interface ApiError {
  detail: string
  status_code: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}
```

---

## 4. API Service Layer

### **src/services/api.ts** (Complete API Client)

```typescript
import axios, { type AxiosInstance, type AxiosError } from 'axios'
import router from '@/router'
import { useToast } from 'vue-toastification'

const toast = useToast()

class ApiService {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor - handle errors globally
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response) {
          switch (error.response.status) {
            case 401:
              // Unauthorized - redirect to login
              localStorage.removeItem('access_token')
              localStorage.removeItem('user')
              router.push('/login')
              toast.error('Session expired. Please login again.')
              break
            case 403:
              toast.error('You do not have permission to perform this action.')
              break
            case 404:
              toast.error('Resource not found.')
              break
            case 422:
              // Validation error
              const detail = (error.response.data as any)?.detail
              if (Array.isArray(detail)) {
                detail.forEach((err: any) => {
                  toast.error(`${err.loc.join('.')}: ${err.msg}`)
                })
              } else {
                toast.error(detail || 'Validation error')
              }
              break
            case 500:
              toast.error('Server error. Please try again later.')
              break
            default:
              toast.error('An unexpected error occurred.')
          }
        } else if (error.request) {
          toast.error('No response from server. Please check your connection.')
        } else {
          toast.error('Request error. Please try again.')
        }
        return Promise.reject(error)
      }
    )
  }

  // Generic HTTP methods
  async get<T>(url: string, config = {}) {
    const response = await this.client.get<T>(url, config)
    return response.data
  }

  async post<T>(url: string, data = {}, config = {}) {
    const response = await this.client.post<T>(url, data, config)
    return response.data
  }

  async put<T>(url: string, data = {}, config = {}) {
    const response = await this.client.put<T>(url, data, config)
    return response.data
  }

  async patch<T>(url: string, data = {}, config = {}) {
    const response = await this.client.patch<T>(url, data, config)
    return response.data
  }

  async delete<T>(url: string, config = {}) {
    const response = await this.client.delete<T>(url, config)
    return response.data
  }

  // File upload
  async upload<T>(url: string, formData: FormData, onProgress?: (percent: number) => void) {
    const response = await this.client.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      },
    })
    return response.data
  }

  // Download file
  async download(url: string, filename: string) {
    const response = await this.client.get(url, {
      responseType: 'blob',
    })

    const blob = new Blob([response.data])
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    link.click()
    URL.revokeObjectURL(link.href)
  }
}

export default new ApiService()
```

---

## 5. Pinia Stores (Complete)

### **src/stores/auth.ts**

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import type { User, LoginRequest, RegisterRequest, LoginResponse } from '@/types'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  async function login(credentials: LoginRequest) {
    loading.value = true
    try {
      const formData = new FormData()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)

      const response = await api.post<LoginResponse>('/auth/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      token.value = response.access_token
      user.value = response.user

      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))

      router.push('/')
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterRequest) {
    loading.value = true
    try {
      await api.post('/auth/register', data)
      await login({ username: data.username, password: data.password })
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  function initializeAuth() {
    const savedToken = localStorage.getItem('access_token')
    const savedUser = localStorage.getItem('user')

    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = JSON.parse(savedUser)
    }
  }

  return {
    user,
    token,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    initializeAuth,
  }
})
```

### **src/stores/servers.ts**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { Server, ServerCreate, ServerUpdate } from '@/types'

export const useServersStore = defineStore('servers', () => {
  const servers = ref<Server[]>([])
  const currentServer = ref<Server | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchServers() {
    loading.value = true
    error.value = null
    try {
      servers.value = await api.get<Server[]>('/servers')
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getServer(id: number) {
    loading.value = true
    try {
      currentServer.value = await api.get<Server>(`/servers/${id}`)
      return currentServer.value
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createServer(data: ServerCreate) {
    loading.value = true
    try {
      const server = await api.post<Server>('/servers', data)
      servers.value.push(server)
      return server
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateServer(id: number, data: ServerUpdate) {
    loading.value = true
    try {
      const server = await api.patch<Server>(`/servers/${id}`, data)
      const index = servers.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        servers.value[index] = server
      }
      return server
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteServer(id: number) {
    loading.value = true
    try {
      await api.delete(`/servers/${id}`)
      servers.value = servers.value.filter((s) => s.id !== id)
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function testConnection(id: number) {
    loading.value = true
    try {
      const result = await api.post<{ success: boolean; message: string }>(
        `/servers/${id}/test`
      )
      return result
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    servers,
    currentServer,
    loading,
    error,
    fetchServers,
    getServer,
    createServer,
    updateServer,
    deleteServer,
    testConnection,
  }
})
```

### **src/stores/deployments.ts**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { Deployment, DeploymentCreate, DeploymentUpdate } from '@/types'

export const useDeploymentsStore = defineStore('deployments', () => {
  const deployments = ref<Deployment[]>([])
  const currentDeployment = ref<Deployment | null>(null)
  const logs = ref<string[]>([])
  const loading = ref(false)

  async function fetchDeployments() {
    loading.value = true
    try {
      deployments.value = await api.get<Deployment[]>('/deployments')
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getDeployment(id: number) {
    loading.value = true
    try {
      currentDeployment.value = await api.get<Deployment>(`/deployments/${id}`)
      return currentDeployment.value
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createDeployment(data: DeploymentCreate) {
    loading.value = true
    try {
      const deployment = await api.post<Deployment>('/deployments', data)
      deployments.value.push(deployment)
      return deployment
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateDeployment(id: number, data: DeploymentUpdate) {
    loading.value = true
    try {
      const deployment = await api.patch<Deployment>(`/deployments/${id}`, data)
      const index = deployments.value.findIndex((d) => d.id === id)
      if (index !== -1) {
        deployments.value[index] = deployment
      }
      return deployment
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteDeployment(id: number) {
    loading.value = true
    try {
      await api.delete(`/deployments/${id}`)
      deployments.value = deployments.value.filter((d) => d.id !== id)
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function restartDeployment(id: number) {
    loading.value = true
    try {
      const result = await api.post<Deployment>(`/deployments/${id}/restart`)
      const index = deployments.value.findIndex((d) => d.id === id)
      if (index !== -1) {
        deployments.value[index] = result
      }
      return result
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchLogs(id: number) {
    try {
      const result = await api.get<{ logs: string[] }>(`/deployments/${id}/logs`)
      logs.value = result.logs
      return result.logs
    } catch (err) {
      throw err
    }
  }

  return {
    deployments,
    currentDeployment,
    logs,
    loading,
    fetchDeployments,
    getDeployment,
    createDeployment,
    updateDeployment,
    deleteDeployment,
    restartDeployment,
    fetchLogs,
  }
})
```

**CONTINUĂ ÎN PARTEA 2...**

Promptul e prea mare! Îl împart în 2 fișiere. Îți dau PARTEA 2 acum!
