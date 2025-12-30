"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, Loader2, Cpu, RefreshCw, Upload } from "lucide-react"
import { toast } from "sonner"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface ESPDevice {
  id: string
  name: string
  ip: string
  platform: string
  version: string
  status: "online" | "offline"
  mac: string
  last_seen: string
}

export default function ESPHomePage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedDevice, setSelectedDevice] = useState<ESPDevice | null>(null)
  const [firmwareFile, setFirmwareFile] = useState<File | null>(null)
  const queryClient = useQueryClient()

  const {
    data: devices,
    isLoading,
    error,
  } = useQuery<ESPDevice[]>({
    queryKey: ["esphome-devices"],
    queryFn: async () => {
      const response = await apiClient.get("/esphome/devices")
      return response.data
    },
  })

  const discoverMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post("/esphome/discover")
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["esphome-devices"] })
      toast.success("Discovery complete")
    },
    onError: () => {
      toast.error("Failed to discover devices")
    },
  })

  const otaUpdateMutation = useMutation({
    mutationFn: async ({ deviceId, file }: { deviceId: string; file: File }) => {
      const formData = new FormData()
      formData.append("firmware", file)
      const response = await apiClient.post(`/esphome/${deviceId}/ota`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["esphome-devices"] })
      toast.success("OTA update started")
      setDialogOpen(false)
      setFirmwareFile(null)
    },
    onError: () => {
      toast.error("Failed to start OTA update")
    },
  })

  const handleOTAUpdate = () => {
    if (selectedDevice && firmwareFile) {
      otaUpdateMutation.mutate({ deviceId: selectedDevice.id, file: firmwareFile })
    }
  }

  const openOTADialog = (device: ESPDevice) => {
    setSelectedDevice(device)
    setDialogOpen(true)
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">ESPHome</h1>
            <p className="text-muted-foreground">Manage ESP devices</p>
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-48 w-full" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">ESPHome</h1>
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
          <h1 className="text-3xl font-bold">ESPHome</h1>
          <p className="text-muted-foreground">Manage ESP devices</p>
        </div>
        <Button onClick={() => discoverMutation.mutate()} disabled={discoverMutation.isPending}>
          {discoverMutation.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Discover Devices
        </Button>
      </div>

      {devices && devices.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {devices.map((device) => (
            <Card key={device.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-5 w-5" />
                    <CardTitle className="text-lg">{device.name}</CardTitle>
                  </div>
                  <Badge variant={device.status === "online" ? "default" : "secondary"}>{device.status}</Badge>
                </div>
                <CardDescription>{device.ip}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Platform</span>
                    <span className="font-medium">{device.platform}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Version</span>
                    <span className="font-medium">{device.version}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">MAC</span>
                    <span className="font-mono text-xs">{device.mac}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Last Seen</span>
                    <span className="text-xs">{device.last_seen}</span>
                  </div>
                </div>

                <Button
                  variant="outline"
                  className="w-full bg-transparent"
                  onClick={() => openOTADialog(device)}
                  disabled={device.status === "offline"}
                >
                  <Upload className="mr-2 h-4 w-4" />
                  OTA Update
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-muted-foreground">No devices discovered yet</p>
            <Button className="mt-4" onClick={() => discoverMutation.mutate()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Discover Devices
            </Button>
          </CardContent>
        </Card>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>OTA Update</DialogTitle>
            <DialogDescription>Upload firmware to {selectedDevice?.name}</DialogDescription>
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
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleOTAUpdate} disabled={!firmwareFile || otaUpdateMutation.isPending}>
                {otaUpdateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Upload & Update
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
