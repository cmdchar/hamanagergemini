"use client"

import { useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import {
  ArrowLeft,
  Server,
  Activity,
  FileText,
  Terminal as TerminalIcon,
  RefreshCw,
  Power,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Clock,
  Cpu,
  HardDrive,
  Wifi,
  Home,
  PlayCircle,
  StopCircle,
} from "lucide-react"
import Link from "next/link"
import { WebTerminal } from "@/components/terminal/web-terminal"

interface Server {
  id: number
  name: string
  host: string
  port: number
  ssh_host: string
  ssh_port: number
  ssh_user: string
  ha_username?: string
  ha_url: string
  ha_version?: string
  is_online: boolean
  last_check?: string
  created_at: string
  updated_at: string
}

interface SystemInfo {
  hostname: string
  uptime: string
  load_average: string
  memory_usage: string
  disk_usage: string
  cpu_count: number
}

interface HaConfig {
  id: string
  path: string
  content: string
  updated_at: string
}

export default function ServerDetailPage() {
  const params = useParams()
  const router = useRouter()
  const serverId = params.id as string
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState("overview")

  // Fetch server details
  const { data: server, isLoading: serverLoading } = useQuery<Server>({
    queryKey: ["server", serverId],
    queryFn: async () => {
      const response = await apiClient.get(`/servers/${serverId}`)
      return response.data
    },
  })

  // Fetch system info
  const { data: systemInfo, isLoading: systemInfoLoading, refetch: refetchSystemInfo } = useQuery<SystemInfo>({
    queryKey: ["server-system-info", serverId],
    queryFn: async () => {
      const response = await apiClient.get(`/servers/${serverId}/system-info`)
      return response.data
    },
    enabled: !!server,
    refetchInterval: 30000, // Refresh every 30s
  })

  // Fetch configs count
  const { data: configs } = useQuery<HaConfig[]>({
    queryKey: ["server-configs", serverId],
    queryFn: async () => {
      const response = await apiClient.get(`/ha-config/servers/${serverId}/configs`)
      return response.data
    },
    enabled: !!server,
  })

  // Test connection mutation
  const testConnectionMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/servers/${serverId}/test`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["server", serverId] })
      toast.success("Connection test successful")
    },
    onError: (error: any) => {
      toast.error(`Connection test failed: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Restart HA mutation
  const restartHaMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/servers/${serverId}/ha/restart`)
      return response.data
    },
    onSuccess: () => {
      toast.success("Home Assistant restart initiated")
    },
    onError: (error: any) => {
      toast.error(`Restart failed: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Check config mutation
  const checkConfigMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/servers/${serverId}/ha/check-config`)
      return response.data
    },
    onSuccess: (data) => {
      if (data.valid) {
        toast.success("Configuration is valid")
      } else {
        toast.error(`Configuration has errors: ${data.errors}`)
      }
    },
    onError: (error: any) => {
      toast.error(`Config check failed: ${error.response?.data?.detail || error.message}`)
    },
  })

  if (serverLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!server) {
    return (
      <div className="flex flex-col items-center justify-center h-screen space-y-4">
        <XCircle className="h-12 w-12 text-destructive" />
        <p className="text-lg text-muted-foreground">Server not found</p>
        <Button onClick={() => router.push("/servers")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Servers
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/servers">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight">{server.name}</h1>
              <Badge variant={server.is_online ? "default" : "destructive"}>
                {server.is_online ? "Online" : "Offline"}
              </Badge>
            </div>
            <p className="text-muted-foreground">
              {server.host}:{server.port} • SSH: {server.ssh_user}@{server.ssh_host}:{server.ssh_port}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => testConnectionMutation.mutate()}
            disabled={testConnectionMutation.isPending}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${testConnectionMutation.isPending ? "animate-spin" : ""}`} />
            Test Connection
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">HA Version</CardTitle>
            <Home className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{server.ha_version || "Unknown"}</div>
            <p className="text-xs text-muted-foreground">Home Assistant</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Config Files</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{configs?.length || 0}</div>
            <p className="text-xs text-muted-foreground">Tracked files</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Uptime</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemInfo?.uptime || "N/A"}</div>
            <p className="text-xs text-muted-foreground">System uptime</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {server.is_online ? (
                <CheckCircle2 className="h-8 w-8 text-green-500" />
              ) : (
                <XCircle className="h-8 w-8 text-red-500" />
              )}
            </div>
            <p className="text-xs text-muted-foreground">Connection status</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="actions">Quick Actions</TabsTrigger>
          <TabsTrigger value="terminal">Terminal</TabsTrigger>
          <TabsTrigger value="system">System Info</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Server Info Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="h-5 w-5" />
                  Server Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Name:</span>
                  <span className="text-sm text-muted-foreground">{server.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Host:</span>
                  <span className="text-sm text-muted-foreground">{server.host}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Port:</span>
                  <span className="text-sm text-muted-foreground">{server.port}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">SSH User:</span>
                  <span className="text-sm text-muted-foreground">{server.ssh_user}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">SSH Host:</span>
                  <span className="text-sm text-muted-foreground">{server.ssh_host}:{server.ssh_port}</span>
                </div>
                {server.ha_username && (
                  <div className="flex justify-between border-t pt-2 mt-2">
                    <span className="text-sm font-medium">HA Username:</span>
                    <span className="text-sm text-muted-foreground">{server.ha_username}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-sm font-medium">HA URL:</span>
                  <a
                    href={server.ha_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-500 hover:underline"
                  >
                    {server.ha_url}
                  </a>
                </div>
              </CardContent>
            </Card>

            {/* Quick Links Card */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Links</CardTitle>
                <CardDescription>Access server features</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <Link href={`/servers/${serverId}/config`}>
                  <Button variant="outline" className="w-full justify-start">
                    <FileText className="mr-2 h-4 w-4" />
                    Configuration Editor
                  </Button>
                </Link>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setActiveTab("terminal")}
                >
                  <TerminalIcon className="mr-2 h-4 w-4" />
                  SSH Terminal
                </Button>
                <a href={server.ha_url} target="_blank" rel="noopener noreferrer" className="block">
                  <Button variant="outline" className="w-full justify-start">
                    <Home className="mr-2 h-4 w-4" />
                    Open Home Assistant
                  </Button>
                </a>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Quick Actions Tab */}
        <TabsContent value="actions" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Home className="h-5 w-5" />
                  Home Assistant Actions
                </CardTitle>
                <CardDescription>Control your Home Assistant instance</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  onClick={() => restartHaMutation.mutate()}
                  disabled={restartHaMutation.isPending}
                >
                  <RotateCcw className={`mr-2 h-4 w-4 ${restartHaMutation.isPending ? "animate-spin" : ""}`} />
                  Restart Home Assistant
                </Button>
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  onClick={() => checkConfigMutation.mutate()}
                  disabled={checkConfigMutation.isPending}
                >
                  <CheckCircle2 className={`mr-2 h-4 w-4 ${checkConfigMutation.isPending ? "animate-spin" : ""}`} />
                  Check Configuration
                </Button>
                <Link href={`/servers/${serverId}/config`}>
                  <Button variant="outline" className="w-full justify-start">
                    <FileText className="mr-2 h-4 w-4" />
                    Edit Configuration Files
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="h-5 w-5" />
                  System Actions
                </CardTitle>
                <CardDescription>System-level operations</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  onClick={() => refetchSystemInfo()}
                  disabled={systemInfoLoading}
                >
                  <RefreshCw className={`mr-2 h-4 w-4 ${systemInfoLoading ? "animate-spin" : ""}`} />
                  Refresh System Info
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setActiveTab("terminal")}
                >
                  <TerminalIcon className="mr-2 h-4 w-4" />
                  Open Terminal
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => testConnectionMutation.mutate()}
                  disabled={testConnectionMutation.isPending}
                >
                  <Wifi className={`mr-2 h-4 w-4 ${testConnectionMutation.isPending ? "animate-spin" : ""}`} />
                  Test Connection
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Terminal Tab */}
        <TabsContent value="terminal" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TerminalIcon className="h-5 w-5" />
                SSH Terminal
              </CardTitle>
              <CardDescription>
                Interactive SSH session to {server.ssh_user}@{server.ssh_host}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <WebTerminal serverId={serverId} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Info Tab */}
        <TabsContent value="system" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5" />
                  System Resources
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {systemInfoLoading ? (
                  <div className="flex items-center justify-center p-8">
                    <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : systemInfo ? (
                  <>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Hostname:</span>
                      <span className="text-sm text-muted-foreground">{systemInfo.hostname}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">CPU Cores:</span>
                      <span className="text-sm text-muted-foreground">{systemInfo.cpu_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Load Average:</span>
                      <span className="text-sm text-muted-foreground">{systemInfo.load_average}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Memory Usage:</span>
                      <span className="text-sm text-muted-foreground">{systemInfo.memory_usage}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Disk Usage:</span>
                      <span className="text-sm text-muted-foreground">{systemInfo.disk_usage}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Uptime:</span>
                      <span className="text-sm text-muted-foreground">{systemInfo.uptime}</span>
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    System information not available
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Connection Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Status:</span>
                  <Badge variant={server.is_online ? "default" : "destructive"}>
                    {server.is_online ? "Online" : "Offline"}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Last Check:</span>
                  <span className="text-sm text-muted-foreground">
                    {server.last_check ? new Date(server.last_check).toLocaleString() : "Never"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Created:</span>
                  <span className="text-sm text-muted-foreground">
                    {new Date(server.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Updated:</span>
                  <span className="text-sm text-muted-foreground">
                    {new Date(server.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
