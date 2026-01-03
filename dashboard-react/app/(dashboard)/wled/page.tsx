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
  Lightbulb,
  Power,
  PowerOff,
  Search,
  Settings,
  BookOpen,
  Wifi,
  Link2,
  Sparkles
} from "lucide-react"
import { toast } from "sonner"
import { WLEDForm } from "@/components/forms/wled-form"
import { Slider } from "@/components/ui/slider"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface WLEDDevice {
  id: number
  name: string
  ip_address: string
  mac_address?: string
  server_id?: number
  version?: string
  led_count: number
  brand?: string
  product?: string
  is_online: boolean
  last_seen?: string
  current_preset?: number
  brightness: number
  is_on: boolean
  presets?: Record<string, any>
  segments?: Record<string, any>
  sync_enabled: boolean
  sync_group?: string
  sync_master: boolean
  created_at: string
  updated_at: string
}

export default function WLEDPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingDevice, setEditingDevice] = useState<WLEDDevice | null>(null)
  const [activeTab, setActiveTab] = useState("devices")
  const [syncGroupName, setSyncGroupName] = useState("christmas")
  const [selectedDevices, setSelectedDevices] = useState<number[]>([])
  const queryClient = useQueryClient()

  const {
    data: devices,
    isLoading,
    error,
  } = useQuery<WLEDDevice[]>({
    queryKey: ["wled-devices"],
    queryFn: async () => {
      const response = await apiClient.get("/wled/devices")
      return response.data
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/wled/devices/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wled-devices"] })
      toast.success("Device deleted successfully")
    },
    onError: () => {
      toast.error("Failed to delete device")
    },
  })

  const controlMutation = useMutation({
    mutationFn: async ({ id, action, value }: { id: number; action: string; value?: any }) => {
      let endpoint = `/wled/devices/${id}/state`
      let payload: any = {}

      if (action === "brightness") {
        payload = { bri: Math.round(value * 2.55) } // Convert 0-100 to 0-255
      } else if (action === "on") {
        payload = { on: true }
      } else if (action === "off") {
        payload = { on: false }
      } else if (action === "preset") {
        payload = { ps: value }
      }

      const response = await apiClient.post(endpoint, payload)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wled-devices"] })
      toast.success("Command sent successfully")
    },
    onError: () => {
      toast.error("Failed to send command")
    },
  })

  const discoverMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post("/wled/discover", { timeout: 10 })
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["wled-devices"] })
      toast.success(`Discovered ${data.devices_found} WLED device(s)`)
    },
    onError: () => {
      toast.error("Device discovery failed")
    },
  })

  const syncMutation = useMutation({
    mutationFn: async ({ deviceIds, syncGroup }: { deviceIds: number[]; syncGroup: string }) => {
      const response = await apiClient.post("/wled/sync", {
        device_ids: deviceIds,
        sync_group: syncGroup
      })
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["wled-devices"] })
      toast.success(data.message)
      setSelectedDevices([])
    },
    onError: () => {
      toast.error("Failed to sync devices")
    },
  })

  const handleEdit = (device: WLEDDevice) => {
    setEditingDevice(device)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingDevice(null)
  }

  const handleBrightnessChange = (deviceId: number, value: number[]) => {
    controlMutation.mutate({ id: deviceId, action: "brightness", value: value[0] })
  }

  const handleDeviceSelection = (deviceId: number) => {
    setSelectedDevices(prev =>
      prev.includes(deviceId)
        ? prev.filter(id => id !== deviceId)
        : [...prev, deviceId]
    )
  }

  const handleSyncDevices = () => {
    if (selectedDevices.length < 2) {
      toast.error("Please select at least 2 devices to sync")
      return
    }
    syncMutation.mutate({ deviceIds: selectedDevices, syncGroup: syncGroupName })
  }

  const syncGroups = devices?.reduce((groups, device) => {
    if (device.sync_enabled && device.sync_group) {
      if (!groups[device.sync_group]) {
        groups[device.sync_group] = []
      }
      groups[device.sync_group].push(device)
    }
    return groups
  }, {} as Record<string, WLEDDevice[]>) || {}

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">WLED Integration</h1>
            <p className="text-muted-foreground">Manage LED controllers</p>
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

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">WLED Integration</h1>
          <p className="text-muted-foreground">Manage LED controllers</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load WLED devices. Please try again.</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">WLED Integration</h1>
          <p className="text-muted-foreground">Discover and control WLED LED controllers</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="devices">
            <Lightbulb className="h-4 w-4 mr-2" />
            Devices
          </TabsTrigger>
          <TabsTrigger value="sync">
            <Link2 className="h-4 w-4 mr-2" />
            Sync Groups
          </TabsTrigger>
          <TabsTrigger value="guide">
            <BookOpen className="h-4 w-4 mr-2" />
            Setup Guide
          </TabsTrigger>
        </TabsList>

        {/* DEVICES TAB */}
        <TabsContent value="devices" className="space-y-4 mt-6">
          <div className="flex gap-3">
            <Button onClick={() => discoverMutation.mutate()} disabled={discoverMutation.isPending}>
              {discoverMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Search className="mr-2 h-4 w-4" />
              )}
              Discover Devices
            </Button>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" onClick={() => setEditingDevice(null)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Manually
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{editingDevice ? "Edit Device" : "Add New WLED Device"}</DialogTitle>
                  <DialogDescription>
                    {editingDevice ? "Update the device configuration" : "Configure a new WLED LED controller"}
                  </DialogDescription>
                </DialogHeader>
                <WLEDForm device={editingDevice} onSuccess={handleCloseDialog} />
              </DialogContent>
            </Dialog>
          </div>

          <Alert>
            <Wifi className="h-4 w-4" />
            <AlertDescription>
              Use <strong>Discover Devices</strong> to automatically find WLED controllers on your network, or add them manually if discovery doesn't work.
            </AlertDescription>
          </Alert>

          {devices && devices.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {devices.map((device) => (
                <Card key={device.id} className={selectedDevices.includes(device.id) ? "ring-2 ring-primary" : ""}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Lightbulb className="h-5 w-5" />
                        <CardTitle className="text-lg">{device.name}</CardTitle>
                      </div>
                      <Badge variant={device.is_online ? "default" : "secondary"}>
                        {device.is_online ? "Online" : "Offline"}
                      </Badge>
                    </div>
                    <CardDescription className="space-y-1">
                      <div className="flex items-center gap-1">
                        <span className="text-xs">{device.ip_address}</span>
                      </div>
                      {device.version && (
                        <div className="text-xs text-muted-foreground">Version: {device.version}</div>
                      )}
                      {device.led_count > 0 && (
                        <div className="text-xs text-muted-foreground">{device.led_count} LEDs</div>
                      )}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {device.sync_enabled && (
                      <Badge variant="outline" className="w-full justify-center">
                        <Link2 className="h-3 w-3 mr-1" />
                        {device.sync_master ? "Master: " : "Synced: "}{device.sync_group}
                      </Badge>
                    )}

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Brightness</span>
                        <span className="font-medium">{Math.round(device.brightness / 2.55)}%</span>
                      </div>
                      <Slider
                        value={[Math.round(device.brightness / 2.55)]}
                        onValueChange={(value) => handleBrightnessChange(device.id, value)}
                        max={100}
                        step={1}
                        disabled={!device.is_online || controlMutation.isPending}
                      />
                    </div>

                    {device.current_preset && device.current_preset > 0 && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Preset</span>
                        <span className="font-medium">#{device.current_preset}</span>
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => controlMutation.mutate({ id: device.id, action: "on" })}
                        disabled={!device.is_online || controlMutation.isPending}
                      >
                        <Power className="mr-2 h-4 w-4" />
                        On
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => controlMutation.mutate({ id: device.id, action: "off" })}
                        disabled={!device.is_online || controlMutation.isPending}
                      >
                        <PowerOff className="mr-2 h-4 w-4" />
                        Off
                      </Button>
                    </div>

                    <div className="flex gap-2 pt-2 border-t">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleDeviceSelection(device.id)}
                      >
                        {selectedDevices.includes(device.id) ? "Deselect" : "Select"}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(device)}
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
                <Lightbulb className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground mb-2">No WLED devices configured yet</p>
                <p className="text-sm text-muted-foreground mb-4">
                  Discover devices on your network or add them manually
                </p>
                <div className="flex gap-2 justify-center">
                  <Button onClick={() => discoverMutation.mutate()}>
                    <Search className="mr-2 h-4 w-4" />
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

        {/* SYNC GROUPS TAB */}
        <TabsContent value="sync" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Create Sync Group</CardTitle>
              <CardDescription>
                Synchronize multiple WLED devices to display the same effects
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="sync-group-name">Sync Group Name</Label>
                <Input
                  id="sync-group-name"
                  value={syncGroupName}
                  onChange={(e) => setSyncGroupName(e.target.value)}
                  placeholder="e.g., christmas, living-room, outdoor"
                />
              </div>

              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Selected {selectedDevices.length} device(s). You need at least 2 devices to create a sync group.
                  {selectedDevices.length > 0 && (
                    <div className="mt-2 text-xs">
                      Go to the <strong>Devices</strong> tab and click "Select" on devices you want to sync.
                    </div>
                  )}
                </AlertDescription>
              </Alert>

              <Button
                onClick={handleSyncDevices}
                disabled={selectedDevices.length < 2 || !syncGroupName || syncMutation.isPending}
                className="w-full"
              >
                {syncMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Link2 className="mr-2 h-4 w-4" />
                )}
                Create Sync Group
              </Button>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Active Sync Groups</h3>
            {Object.keys(syncGroups).length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2">
                {Object.entries(syncGroups).map(([groupName, groupDevices]) => (
                  <Card key={groupName}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base flex items-center gap-2">
                          <Sparkles className="h-4 w-4" />
                          {groupName}
                        </CardTitle>
                        <Badge>{groupDevices.length} devices</Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {groupDevices.map((device) => (
                          <div key={device.id} className="flex items-center justify-between text-sm p-2 rounded bg-muted/50">
                            <div className="flex items-center gap-2">
                              <Lightbulb className="h-3 w-3" />
                              <span>{device.name}</span>
                            </div>
                            {device.sync_master && (
                              <Badge variant="secondary" className="text-xs">Master</Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <Link2 className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">No sync groups configured yet</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Create a sync group to synchronize multiple WLED devices
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* SETUP GUIDE TAB */}
        <TabsContent value="guide" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>WLED Setup Guide</CardTitle>
              <CardDescription>
                Learn how to set up and integrate WLED controllers with your Home Assistant
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="item-1">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">1</span>
                      What is WLED?
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">
                      <strong>WLED</strong> is a fast and feature-rich implementation of an ESP8266/ESP32 webserver to control addressable LED strips (WS2812B, SK6812, APA102, etc.).
                    </p>
                    <div className="text-sm space-y-2">
                      <p><strong>Key Features:</strong></p>
                      <ul className="list-disc list-inside space-y-1 ml-4">
                        <li>100+ effects and palettes built-in</li>
                        <li>Web-based configuration interface</li>
                        <li>Support for multiple LED strips (segments)</li>
                        <li>Sync multiple controllers for synchronized effects</li>
                        <li>JSON API for integration</li>
                        <li>Presets and playlists</li>
                      </ul>
                    </div>
                    <a
                      href="https://kno.wled.ge/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary hover:underline inline-block"
                    >
                      Visit WLED Documentation →
                    </a>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-2">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">2</span>
                      Flash WLED to Your ESP Device
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">
                      You can flash WLED to ESP8266 or ESP32 devices using the web installer (easiest method):
                    </p>
                    <div className="bg-muted p-4 rounded-md space-y-2">
                      <p className="text-sm"><strong>Steps:</strong></p>
                      <ol className="list-decimal list-inside space-y-2 ml-2 text-sm">
                        <li>Visit <a href="https://install.wled.me/" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">install.wled.me</a></li>
                        <li>Connect your ESP device via USB</li>
                        <li>Click "Install" and select your chip type (ESP8266/ESP32)</li>
                        <li>Follow the browser prompts to flash the firmware</li>
                        <li>After flashing, configure WiFi credentials</li>
                      </ol>
                    </div>
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-sm">
                        <strong>Supported browsers:</strong> Chrome, Edge, Opera (not Firefox or Safari)
                      </AlertDescription>
                    </Alert>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-3">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">3</span>
                      Connect LED Strip to ESP Device
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">Basic wiring for WS2812B/SK6812 LED strips:</p>
                    <div className="bg-muted p-4 rounded-md space-y-3">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="font-semibold mb-2">ESP8266 (D1 Mini):</p>
                          <ul className="space-y-1">
                            <li>LED Data → <code className="bg-background px-1 rounded">GPIO2 (D4)</code></li>
                            <li>LED +5V → <code className="bg-background px-1 rounded">VIN or external 5V</code></li>
                            <li>LED GND → <code className="bg-background px-1 rounded">GND</code></li>
                          </ul>
                        </div>
                        <div>
                          <p className="font-semibold mb-2">ESP32:</p>
                          <ul className="space-y-1">
                            <li>LED Data → <code className="bg-background px-1 rounded">GPIO2</code></li>
                            <li>LED +5V → <code className="bg-background px-1 rounded">VIN or external 5V</code></li>
                            <li>LED GND → <code className="bg-background px-1 rounded">GND</code></li>
                          </ul>
                        </div>
                      </div>
                    </div>
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-sm">
                        <strong>Important:</strong> For LED strips with &gt;30 LEDs, use external 5V power supply (not USB). Connect GND of ESP and power supply together.
                      </AlertDescription>
                    </Alert>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-4">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">4</span>
                      Configure WLED Device
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">After flashing and connecting to WiFi:</p>
                    <div className="bg-muted p-4 rounded-md space-y-2">
                      <ol className="list-decimal list-inside space-y-2 ml-2 text-sm">
                        <li>Find the device IP in your router's DHCP client list</li>
                        <li>Open <code className="bg-background px-1 rounded">http://[device-ip]</code> in browser</li>
                        <li>Go to <strong>Config → LED Preferences</strong></li>
                        <li>Set LED count and type (e.g., WS2812B)</li>
                        <li>Set data GPIO pin (default: GPIO2)</li>
                        <li>Configure segments if using multiple LED strips</li>
                        <li>Save and reboot</li>
                      </ol>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-5">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">5</span>
                      Add Device to This Platform
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">Two methods to add WLED devices:</p>
                    <div className="space-y-3">
                      <div className="bg-muted p-4 rounded-md">
                        <p className="font-semibold text-sm mb-2">Method 1: Auto-Discovery (Recommended)</p>
                        <ol className="list-decimal list-inside space-y-1 ml-2 text-sm">
                          <li>Go to the <strong>Devices</strong> tab</li>
                          <li>Click <strong>Discover Devices</strong></li>
                          <li>Wait 5-10 seconds for mDNS discovery</li>
                          <li>Devices will appear automatically</li>
                        </ol>
                      </div>
                      <div className="bg-muted p-4 rounded-md">
                        <p className="font-semibold text-sm mb-2">Method 2: Manual Addition</p>
                        <ol className="list-decimal list-inside space-y-1 ml-2 text-sm">
                          <li>Go to the <strong>Devices</strong> tab</li>
                          <li>Click <strong>Add Manually</strong></li>
                          <li>Enter device name and IP address</li>
                          <li>Save the device</li>
                        </ol>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-6">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">6</span>
                      Using Sync Groups
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <p className="text-sm">Synchronize multiple WLED devices for coordinated effects:</p>
                    <div className="bg-muted p-4 rounded-md space-y-2">
                      <ol className="list-decimal list-inside space-y-2 ml-2 text-sm">
                        <li>Go to the <strong>Devices</strong> tab</li>
                        <li>Click "Select" on 2 or more devices</li>
                        <li>Go to the <strong>Sync Groups</strong> tab</li>
                        <li>Enter a group name (e.g., "christmas", "outdoor")</li>
                        <li>Click <strong>Create Sync Group</strong></li>
                      </ol>
                    </div>
                    <p className="text-sm">
                      The first device becomes the master. All other devices will sync their effects with the master device.
                    </p>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="item-7">
                  <AccordionTrigger className="text-base">
                    <span className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">7</span>
                      Troubleshooting
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <div className="space-y-4">
                      <div>
                        <p className="font-semibold text-sm mb-2">Device not discovered:</p>
                        <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                          <li>Ensure device is on the same network/VLAN</li>
                          <li>Check that mDNS is enabled in WLED config</li>
                          <li>Try adding manually with IP address</li>
                          <li>Check firewall rules allow mDNS (port 5353 UDP)</li>
                        </ul>
                      </div>
                      <div>
                        <p className="font-semibold text-sm mb-2">Device shows offline:</p>
                        <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                          <li>Verify device has power</li>
                          <li>Check WiFi connection is active</li>
                          <li>Ping the device IP to verify network connectivity</li>
                          <li>Restart the WLED device</li>
                        </ul>
                      </div>
                      <div>
                        <p className="font-semibold text-sm mb-2">LEDs not lighting up:</p>
                        <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                          <li>Check power supply (5V with enough amperage)</li>
                          <li>Verify data pin is correctly wired</li>
                          <li>Ensure LED type matches configuration (WS2812B vs SK6812, etc.)</li>
                          <li>Try increasing brightness via WLED web interface</li>
                        </ul>
                      </div>
                      <div>
                        <p className="font-semibold text-sm mb-2">Sync not working:</p>
                        <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                          <li>All devices must be on same network</li>
                          <li>Enable "Receive broadcast" in WLED Sync settings</li>
                          <li>Use same UDP port (default 21324) on all devices</li>
                          <li>Check that network allows UDP broadcast</li>
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
                href="https://kno.wled.ge/"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-primary hover:underline"
              >
                Official WLED Documentation →
              </a>
              <a
                href="https://github.com/Aircoookie/WLED"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-primary hover:underline"
              >
                WLED GitHub Repository →
              </a>
              <a
                href="https://install.wled.me/"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-primary hover:underline"
              >
                WLED Web Installer →
              </a>
              <a
                href="https://www.youtube.com/results?search_query=wled+tutorial"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-primary hover:underline"
              >
                WLED Video Tutorials (YouTube) →
              </a>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
