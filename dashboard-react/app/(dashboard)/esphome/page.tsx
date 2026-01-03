"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Plus,
  Trash2,
  AlertCircle,
  Loader2,
  Cpu,
  RefreshCw,
  Upload,
  Settings,
  BookOpen,
  Wifi,
  Download,
  BarChart3,
  Play,
  FileCode
} from "lucide-react"
import { toast } from "sonner"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"

interface ESPHomeDevice {
  id: number
  name: string
  friendly_name?: string
  device_class?: string
  ip_address: string
  mac_address?: string
  port: number
  platform?: string
  board?: string
  server_id?: number
  esphome_version?: string
  compilation_time?: string
  firmware_version?: string
  config_hash?: string
  ota_enabled: boolean
  requires_encryption: boolean
  online: boolean
  last_seen?: string
  connection_status?: string
  update_available: boolean
  update_version?: string
  auto_update: boolean
  tags?: string[]
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

interface ESPHomeStatistics {
  total_devices: number
  online_devices: number
  offline_devices: number
  devices_by_platform: Record<string, number>
  total_updates: number
  successful_updates: number
  failed_updates: number
  average_update_time?: number
}

interface OTAUpdate {
  id: number
  device_id: number
  from_version?: string
  to_version: string
  firmware_file?: string
  status: string
  progress: number
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  success: boolean
  error_message?: string
  rollback_performed: boolean
  update_type: string
  triggered_by?: string
  created_at: string
}

export default function ESPHomePage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false)
  const [selectedDevice, setSelectedDevice] = useState<ESPHomeDevice | null>(null)
  const [firmwareFile, setFirmwareFile] = useState<File | null>(null)
  const [otaPassword, setOtaPassword] = useState("")
  const [activeTab, setActiveTab] = useState("devices")
  const [selectedDevices, setSelectedDevices] = useState<number[]>([])
  const queryClient = useQueryClient()

  const {
    data: devices,
    isLoading: devicesLoading,
    error: devicesError,
  } = useQuery<ESPHomeDevice[]>({
    queryKey: ["esphome-devices"],
    queryFn: async () => {
      const response = await apiClient.get("/esphome/devices")
      return response.data
    },
  })

  const {
    data: statistics,
  } = useQuery<ESPHomeStatistics>({
    queryKey: ["esphome-statistics"],
    queryFn: async () => {
      const response = await apiClient.get("/esphome/statistics")
      return response.data
    },
    enabled: activeTab === "devices",
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/esphome/devices/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["esphome-devices"] })
      queryClient.invalidateQueries({ queryKey: ["esphome-statistics"] })
      toast.success("Device deleted successfully")
    },
    onError: () => {
      toast.error("Failed to delete device")
    },
  })

  const discoverMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post("/esphome/discover", { timeout: 10 })
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["esphome-devices"] })
      toast.success(`Discovered ${data.count} ESPHome device(s)`)
    },
    onError: () => {
      toast.error("Device discovery failed")
    },
  })

  const syncDiscoveredMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post("/esphome/discover/sync")
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["esphome-devices"] })
      queryClient.invalidateQueries({ queryKey: ["esphome-statistics"] })
      toast.success(data.message)
    },
    onError: () => {
      toast.error("Failed to sync devices")
    },
  })

  const otaUpdateMutation = useMutation({
    mutationFn: async ({ deviceId, file, password }: { deviceId: number; file: File; password?: string }) => {
      const formData = new FormData()
      formData.append("file", file)
      if (password) {
        formData.append("password", password)
      }
      const response = await apiClient.post(`/esphome/devices/${deviceId}/ota`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["esphome-devices"] })
      queryClient.invalidateQueries({ queryKey: ["esphome-statistics"] })
      toast.success("OTA update started successfully")
      setUpdateDialogOpen(false)
      setFirmwareFile(null)
      setOtaPassword("")
      setSelectedDevice(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to start OTA update")
    },
  })

  const handleOTAUpdate = () => {
    if (selectedDevice && firmwareFile) {
      otaUpdateMutation.mutate({
        deviceId: selectedDevice.id,
        file: firmwareFile,
        password: otaPassword || undefined
      })
    }
  }

  const openOTADialog = (device: ESPHomeDevice) => {
    setSelectedDevice(device)
    setUpdateDialogOpen(true)
  }

  const handleDeviceSelection = (deviceId: number) => {
    setSelectedDevices(prev =>
      prev.includes(deviceId)
        ? prev.filter(id => id !== deviceId)
        : [...prev, deviceId]
    )
  }

  const platformColors: Record<string, string> = {
    esp32: "bg-blue-500",
    esp8266: "bg-green-500",
    rp2040: "bg-purple-500",
  }

  if (devicesLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">ESPHome Integration</h1>
            <p className="text-muted-foreground">Manage ESP devices</p>
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-64 w-full" />
          ))}
        </div>
      </div>
    )
  }

  if (devicesError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">ESPHome Integration</h1>
          <p className="text-muted-foreground">Manage ESP devices</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load ESPHome devices. Please try again.</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">ESPHome Integration</h1>
          <p className="text-muted-foreground">Discover and manage ESP8266/ESP32/RP2040 devices</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="devices">
            <Cpu className="h-4 w-4 mr-2" />
            Devices
          </TabsTrigger>
          <TabsTrigger value="updates">
            <Upload className="h-4 w-4 mr-2" />
            OTA Updates
          </TabsTrigger>
          <TabsTrigger value="guide">
            <BookOpen className="h-4 w-4 mr-2" />
            Setup Guide
          </TabsTrigger>
        </TabsList>

        {/* DEVICES TAB */}
        <TabsContent value="devices" className="space-y-4 mt-6">
          {/* Statistics Cards */}
          {statistics && (
            <div className="grid gap-4 md:grid-cols-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Total Devices</CardDescription>
                  <CardTitle className="text-3xl">{statistics.total_devices}</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Online</CardDescription>
                  <CardTitle className="text-3xl text-green-600">{statistics.online_devices}</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Offline</CardDescription>
                  <CardTitle className="text-3xl text-gray-500">{statistics.offline_devices}</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Total Updates</CardDescription>
                  <CardTitle className="text-3xl">{statistics.total_updates}</CardTitle>
                </CardHeader>
              </Card>
            </div>
          )}

          <div className="flex gap-3">
            <Button onClick={() => discoverMutation.mutate()} disabled={discoverMutation.isPending}>
              {discoverMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Discover Devices
            </Button>
            <Button
              variant="outline"
              onClick={() => syncDiscoveredMutation.mutate()}
              disabled={syncDiscoveredMutation.isPending}
            >
              {syncDiscoveredMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Download className="mr-2 h-4 w-4" />
              )}
              Sync to Database
            </Button>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">
                  <Plus className="mr-2 h-4 w-4" />
                  Add Manually
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add ESPHome Device</DialogTitle>
                  <DialogDescription>
                    Manually configure a new ESPHome device
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="device-name">Device Name</Label>
                    <Input id="device-name" placeholder="my-esp32" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="device-ip">IP Address</Label>
                    <Input id="device-ip" placeholder="192.168.1.100" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="device-platform">Platform</Label>
                    <select id="device-platform" className="w-full rounded-md border px-3 py-2">
                      <option value="esp32">ESP32</option>
                      <option value="esp8266">ESP8266</option>
                      <option value="rp2040">RP2040</option>
                    </select>
                  </div>
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="text-sm">
                      Manual addition is useful when auto-discovery doesn't work. Make sure the device is accessible on your network.
                    </AlertDescription>
                  </Alert>
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button>Add Device</Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          <Alert>
            <Wifi className="h-4 w-4" />
            <AlertDescription>
              Use <strong>Discover Devices</strong> to automatically find ESPHome controllers on your network, then <strong>Sync to Database</strong> to save them.
            </AlertDescription>
          </Alert>

          {devices && devices.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {devices.map((device) => (
                <Card key={device.id} className={selectedDevices.includes(device.id) ? "ring-2 ring-primary" : ""}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Cpu className="h-5 w-5" />
                        <CardTitle className="text-lg">{device.friendly_name || device.name}</CardTitle>
                      </div>
                      <Badge variant={device.online ? "default" : "secondary"}>
                        {device.online ? "Online" : "Offline"}
                      </Badge>
                    </div>
                    <CardDescription className="space-y-1">
                      <div className="flex items-center gap-1">
                        <span className="text-xs">{device.ip_address}:{device.port}</span>
                      </div>
                      {device.platform && (
                        <div className="flex items-center gap-2 mt-1">
                          <div className={`h-2 w-2 rounded-full ${platformColors[device.platform] || 'bg-gray-500'}`} />
                          <span className="text-xs text-muted-foreground uppercase">{device.platform}</span>
                        </div>
                      )}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2 text-sm">
                      {device.esphome_version && (
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">ESPHome Version</span>
                          <span className="font-medium text-xs">{device.esphome_version}</span>
                        </div>
                      )}
                      {device.firmware_version && (
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Firmware</span>
                          <span className="font-medium text-xs">{device.firmware_version}</span>
                        </div>
                      )}
                      {device.board && (
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Board</span>
                          <span className="font-medium text-xs">{device.board}</span>
                        </div>
                      )}
                      {device.mac_address && (
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">MAC</span>
                          <span className="font-mono text-xs">{device.mac_address}</span>
                        </div>
                      )}
                    </div>

                    {device.update_available && (
                      <Badge variant="outline" className="w-full justify-center text-yellow-600 border-yellow-600">
                        Update Available: {device.update_version}
                      </Badge>
                    )}

                    {device.ota_enabled && (
                      <Badge variant="outline" className="w-full justify-center">
                        <Upload className="h-3 w-3 mr-1" />
                        OTA Enabled
                      </Badge>
                    )}

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => openOTADialog(device)}
                        disabled={!device.online || !device.ota_enabled}
                      >
                        <Upload className="mr-2 h-4 w-4" />
                        Update
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeviceSelection(device.id)}
                      >
                        {selectedDevices.includes(device.id) ? "Deselect" : "Select"}
                      </Button>
                    </div>

                    <div className="flex gap-2 pt-2 border-t">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => toast.info("Device settings coming soon")}
                      >
                        <Settings className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => deleteMutation.mutate(device.id)}
                        disabled={deleteMutation.isPending}
                      >
                        {deleteMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <Cpu className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground mb-2">No ESPHome devices configured yet</p>
                <p className="text-sm text-muted-foreground mb-4">
                  Discover devices on your network or add them manually
                </p>
                <div className="flex gap-2 justify-center">
                  <Button onClick={() => discoverMutation.mutate()}>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Discover Devices
                  </Button>
                  <Button variant="outline" onClick={() => setDialogOpen(true)}>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Manually
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* OTA UPDATES TAB */}
        <TabsContent value="updates" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>OTA Update Statistics</CardTitle>
              <CardDescription>
                Over-The-Air firmware update history and statistics
              </CardDescription>
            </CardHeader>
            <CardContent>
              {statistics && (
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">Total Updates</p>
                    <p className="text-3xl font-bold">{statistics.total_updates}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">Successful</p>
                    <p className="text-3xl font-bold text-green-600">{statistics.successful_updates}</p>
                    {statistics.total_updates > 0 && (
                      <Progress
                        value={(statistics.successful_updates / statistics.total_updates) * 100}
                        className="h-2"
                      />
                    )}
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">Failed</p>
                    <p className="text-3xl font-bold text-red-600">{statistics.failed_updates}</p>
                    {statistics.total_updates > 0 && (
                      <Progress
                        value={(statistics.failed_updates / statistics.total_updates) * 100}
                        className="h-2"
                      />
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Bulk OTA Update</CardTitle>
              <CardDescription>
                Update multiple devices simultaneously or sequentially
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Selected {selectedDevices.length} device(s). Select devices from the Devices tab first.
                  {selectedDevices.length > 0 && (
                    <div className="mt-2 text-xs">
                      Go to the <strong>Devices</strong> tab and click "Select" on devices you want to update.
                    </div>
                  )}
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                <Label htmlFor="bulk-firmware">Firmware File (.bin)</Label>
                <Input
                  id="bulk-firmware"
                  type="file"
                  accept=".bin"
                  onChange={(e) => setFirmwareFile(e.target.files?.[0] || null)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="bulk-password">OTA Password (optional)</Label>
                <Input
                  id="bulk-password"
                  type="password"
                  placeholder="Leave empty if not set"
                  value={otaPassword}
                  onChange={(e) => setOtaPassword(e.target.value)}
                />
              </div>

              <Button
                disabled={selectedDevices.length === 0 || !firmwareFile}
                className="w-full"
                onClick={() => toast.info("Bulk update feature coming soon")}
              >
                <Upload className="mr-2 h-4 w-4" />
                Start Bulk Update ({selectedDevices.length} devices)
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Platform Distribution</CardTitle>
              <CardDescription>
                Device count by platform type
              </CardDescription>
            </CardHeader>
            <CardContent>
              {statistics && Object.keys(statistics.devices_by_platform).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(statistics.devices_by_platform).map(([platform, count]) => (
                    <div key={platform} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`h-3 w-3 rounded-full ${platformColors[platform] || 'bg-gray-500'}`} />
                        <span className="font-medium uppercase text-sm">{platform}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <Progress value={(count / statistics.total_devices) * 100} className="w-32 h-2" />
                        <span className="text-sm font-bold w-8 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">No devices to display</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* SETUP GUIDE TAB */}
        <TabsContent value="guide" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>ESPHome Setup Guide</CardTitle>
              <CardDescription>
                Learn how to set up and integrate ESPHome devices with your Home Assistant
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="item-1">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">1</span>
                      What is ESPHome?
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">
                      <strong>ESPHome</strong> is a system to control your ESP8266/ESP32/RP2040 by simple yet powerful configuration files and control them remotely through Home Automation systems.
                    </p>
                    <div className="text-sm space-y-2">
                      <p><strong>Key Features:</strong></p>
                      <ul className="list-disc list-inside space-y-1 ml-4">
                        <li>Configuration via YAML files (no programming required)</li>
                        <li>OTA (Over-The-Air) updates</li>
                        <li>Native Home Assistant integration</li>
                        <li>150+ supported sensors and components</li>
                        <li>Web server for debugging</li>
                        <li>Powerful automation engine</li>
                        <li>Active community and extensive documentation</li>
                      </ul>
                    </div>
                    <a
                      href="https://esphome.io/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary hover:underline inline-block"
                    >
                      Visit ESPHome Documentation →
                    </a>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-2">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">2</span>
                      Install ESPHome Dashboard
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">
                      Install ESPHome Dashboard as a Home Assistant Add-on or standalone:
                    </p>
                    <div className="bg-muted p-4 rounded-md space-y-2">
                      <p className="text-sm"><strong>Method 1: Home Assistant Add-on (Recommended)</strong></p>
                      <ol className="list-decimal list-inside space-y-2 ml-2 text-sm">
                        <li>Go to Settings → Add-ons → Add-on Store</li>
                        <li>Search for "ESPHome"</li>
                        <li>Click Install</li>
                        <li>Start the add-on</li>
                        <li>Access via Supervisor → ESPHome</li>
                      </ol>
                    </div>
                    <div className="bg-muted p-4 rounded-md space-y-2">
                      <p className="text-sm"><strong>Method 2: Docker (Standalone)</strong></p>
                      <code className="block p-2 bg-background rounded text-xs">
                        docker run --rm -v &quot;$PWD&quot;:/config -p 6052:6052 esphome/esphome
                      </code>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-3">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">3</span>
                      Create Your First Device
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">Create a new ESPHome device configuration:</p>
                    <div className="bg-muted p-4 rounded-md space-y-2">
                      <ol className="list-decimal list-inside space-y-2 ml-2 text-sm">
                        <li>Open ESPHome Dashboard</li>
                        <li>Click <strong>+ New Device</strong></li>
                        <li>Click <strong>Continue</strong> on the wizard</li>
                        <li>Enter a name (e.g., "living-room-sensor")</li>
                        <li>Select your device type (ESP32, ESP8266, or RP2040)</li>
                        <li>Enter WiFi credentials</li>
                        <li>Click <strong>Next</strong> to generate configuration</li>
                      </ol>
                    </div>
                    <p className="text-sm">Example minimal configuration:</p>
                    <code className="block p-3 bg-background rounded text-xs overflow-x-auto">
{`esphome:
  name: living-room-sensor
  platform: ESP32
  board: nodemcu-32s

wifi:
  ssid: "YourWiFiSSID"
  password: "YourWiFiPassword"

api:
  encryption:
    key: "your-32-char-encryption-key"

ota:
  password: "your-ota-password"`}
                    </code>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-4">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">4</span>
                      Flash Firmware to Device
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">First time setup requires USB connection:</p>
                    <div className="bg-muted p-4 rounded-md space-y-2">
                      <ol className="list-decimal list-inside space-y-2 ml-2 text-sm">
                        <li>Connect ESP device to computer via USB</li>
                        <li>In ESPHome Dashboard, click the 3 dots on your device</li>
                        <li>Click <strong>Install</strong></li>
                        <li>Choose <strong>Plug into this computer</strong></li>
                        <li>Select the COM port (e.g., COM3 or /dev/ttyUSB0)</li>
                        <li>Wait for compilation and upload (~2-3 minutes)</li>
                        <li>Device will reboot and connect to WiFi</li>
                      </ol>
                    </div>
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-sm">
                        <strong>First flash:</strong> Must be done via USB. Subsequent updates can be done Over-The-Air (OTA).
                      </AlertDescription>
                    </Alert>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-5">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">5</span>
                      Add Sensors and Components
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">Enhance your device with sensors and components:</p>
                    <div className="space-y-3">
                      <div className="bg-muted p-4 rounded-md">
                        <p className="font-semibold text-sm mb-2">Example: DHT22 Temperature/Humidity Sensor</p>
                        <code className="block p-2 bg-background rounded text-xs overflow-x-auto">
{`sensor:
  - platform: dht
    pin: GPIO4
    temperature:
      name: "Living Room Temperature"
    humidity:
      name: "Living Room Humidity"
    update_interval: 60s`}
                        </code>
                      </div>
                      <div className="bg-muted p-4 rounded-md">
                        <p className="font-semibold text-sm mb-2">Example: Binary Motion Sensor</p>
                        <code className="block p-2 bg-background rounded text-xs overflow-x-auto">
{`binary_sensor:
  - platform: gpio
    pin: GPIO5
    name: "Motion Sensor"
    device_class: motion`}
                        </code>
                      </div>
                      <div className="bg-muted p-4 rounded-md">
                        <p className="font-semibold text-sm mb-2">Example: Relay Switch</p>
                        <code className="block p-2 bg-background rounded text-xs overflow-x-auto">
{`switch:
  - platform: gpio
    pin: GPIO12
    name: "Living Room Light"
    id: living_room_light`}
                        </code>
                      </div>
                    </div>
                    <a
                      href="https://esphome.io/components/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary hover:underline inline-block"
                    >
                      Browse 150+ Supported Components →
                    </a>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-6">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">6</span>
                      Add Device to This Platform
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">Two methods to add ESPHome devices:</p>
                    <div className="space-y-3">
                      <div className="bg-muted p-4 rounded-md">
                        <p className="font-semibold text-sm mb-2">Method 1: Auto-Discovery (Recommended)</p>
                        <ol className="list-decimal list-inside space-y-1 ml-2 text-sm">
                          <li>Ensure your ESPHome devices are online and connected to WiFi</li>
                          <li>Go to the <strong>Devices</strong> tab in this platform</li>
                          <li>Click <strong>Discover Devices</strong></li>
                          <li>Wait 5-10 seconds for mDNS discovery</li>
                          <li>Click <strong>Sync to Database</strong> to save found devices</li>
                        </ol>
                      </div>
                      <div className="bg-muted p-4 rounded-md">
                        <p className="font-semibold text-sm mb-2">Method 2: Manual Addition</p>
                        <ol className="list-decimal list-inside space-y-1 ml-2 text-sm">
                          <li>Go to the <strong>Devices</strong> tab</li>
                          <li>Click <strong>Add Manually</strong></li>
                          <li>Enter device name and IP address</li>
                          <li>Select platform (ESP32/ESP8266/RP2040)</li>
                          <li>Save the device</li>
                        </ol>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-7">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">7</span>
                      OTA Updates
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">Update firmware wirelessly after initial USB flash:</p>
                    <div className="bg-muted p-4 rounded-md space-y-2">
                      <ol className="list-decimal list-inside space-y-2 ml-2 text-sm">
                        <li>Make changes to your device YAML configuration</li>
                        <li>In ESPHome Dashboard, click <strong>Install → Wirelessly</strong></li>
                        <li>Or use this platform's <strong>OTA Updates</strong> tab</li>
                        <li>Select device and upload compiled .bin file</li>
                        <li>Enter OTA password if configured</li>
                        <li>Click <strong>Upload & Update</strong></li>
                        <li>Wait for upload and device reboot (~30-60 seconds)</li>
                      </ol>
                    </div>
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-sm">
                        <strong>Tip:</strong> Always set an OTA password in your config for security. You can also enable automatic rollback if update fails.
                      </AlertDescription>
                    </Alert>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-8">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">8</span>
                      Troubleshooting
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <div className="space-y-4">
                      <div>
                        <p className="font-semibold text-sm mb-2">Device not discovered:</p>
                        <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                          <li>Ensure device is on the same network/VLAN</li>
                          <li>Check that mDNS is enabled (it's on by default)</li>
                          <li>Verify WiFi credentials in YAML are correct</li>
                          <li>Try adding device manually with IP address</li>
                          <li>Check firewall rules allow mDNS (port 5353 UDP)</li>
                        </ul>
                      </div>
                      <div>
                        <p className="font-semibold text-sm mb-2">Device shows offline:</p>
                        <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                          <li>Check device has power</li>
                          <li>Verify WiFi connection (check router DHCP leases)</li>
                          <li>Look at device logs in ESPHome Dashboard</li>
                          <li>Ping the device IP to verify network connectivity</li>
                          <li>Restart the device (power cycle)</li>
                        </ul>
                      </div>
                      <div>
                        <p className="font-semibold text-sm mb-2">OTA update fails:</p>
                        <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                          <li>Verify OTA password is correct</li>
                          <li>Ensure device has stable WiFi connection</li>
                          <li>Check that firmware file matches platform (ESP32 vs ESP8266)</li>
                          <li>Make sure device has enough free memory</li>
                          <li>Try uploading via USB if OTA consistently fails</li>
                        </ul>
                      </div>
                      <div>
                        <p className="font-semibold text-sm mb-2">Compilation errors:</p>
                        <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                          <li>Check YAML syntax (indentation matters!)</li>
                          <li>Verify component names are correct</li>
                          <li>Ensure board type matches your hardware</li>
                          <li>Update ESPHome to latest version</li>
                          <li>Check component documentation for required parameters</li>
                        </ul>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Additional Resources</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <a
                href="https://esphome.io/"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-primary hover:underline"
              >
                Official ESPHome Documentation →
              </a>
              <a
                href="https://esphome.io/components/"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-primary hover:underline"
              >
                Component Index (150+ components) →
              </a>
              <a
                href="https://esphome.io/guides/getting_started_hassio.html"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-primary hover:underline"
              >
                Getting Started with Home Assistant Add-on →
              </a>
              <a
                href="https://community.home-assistant.io/c/esphome/36"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-primary hover:underline"
              >
                ESPHome Community Forum →
              </a>
              <a
                href="https://discord.gg/KhAMKrd"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-primary hover:underline"
              >
                ESPHome Discord Community →
              </a>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* OTA Update Dialog */}
      <Dialog open={updateDialogOpen} onOpenChange={setUpdateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>OTA Update</DialogTitle>
            <DialogDescription>
              Upload firmware to {selectedDevice?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="firmware">Firmware File (.bin)</Label>
              <Input
                id="firmware"
                type="file"
                accept=".bin"
                onChange={(e) => setFirmwareFile(e.target.files?.[0] || null)}
              />
              <p className="text-xs text-muted-foreground">
                Compile your firmware in ESPHome Dashboard and download the .bin file
              </p>
            </div>
            {selectedDevice?.ota_enabled && (
              <div className="space-y-2">
                <Label htmlFor="ota-password">OTA Password (if configured)</Label>
                <Input
                  id="ota-password"
                  type="password"
                  placeholder="Leave empty if not set"
                  value={otaPassword}
                  onChange={(e) => setOtaPassword(e.target.value)}
                />
              </div>
            )}
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-sm">
                OTA update will reboot the device. Make sure it has a stable WiFi connection.
              </AlertDescription>
            </Alert>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => {
                setUpdateDialogOpen(false)
                setFirmwareFile(null)
                setOtaPassword("")
                setSelectedDevice(null)
              }}>
                Cancel
              </Button>
              <Button onClick={handleOTAUpdate} disabled={!firmwareFile || otaUpdateMutation.isPending}>
                {otaUpdateMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload & Update
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
