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
import { Plus, Trash2, AlertCircle, Loader2, Lightbulb, Power, PowerOff } from "lucide-react"
import { toast } from "sonner"
import { WLEDForm } from "@/components/forms/wled-form"
import { Slider } from "@/components/ui/slider"

interface WLEDDevice {
  id: string
  name: string
  host: string
  port: number
  status: "online" | "offline"
  brightness: number
  color: string
  effect: string
  created_at: string
}

export default function WLEDPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingDevice, setEditingDevice] = useState<WLEDDevice | null>(null)
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
    mutationFn: async (id: string) => {
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
    mutationFn: async ({ id, action, value }: { id: string; action: string; value?: any }) => {
      let payload = {};
      let endpoint = `/wled/devices/${id}/state`;
      
      if (action === "brightness") {
        payload = { bri: Math.round(value * 2.55) }; // Convert 0-100 to 0-255
      } else if (action === "on") {
        payload = { on: true };
      } else if (action === "off") {
        payload = { on: false };
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

  const handleEdit = (device: WLEDDevice) => {
    setEditingDevice(device)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingDevice(null)
  }

  const handleBrightnessChange = (deviceId: string, value: number[]) => {
    controlMutation.mutate({ id: deviceId, action: "brightness", value: value[0] })
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">WLED Controllers</h1>
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
          <h1 className="text-3xl font-bold">WLED Controllers</h1>
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
          <h1 className="text-3xl font-bold">WLED Controllers</h1>
          <p className="text-muted-foreground">Manage LED controllers</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => setEditingDevice(null)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Device
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

      {devices && devices.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {devices.map((device) => (
            <Card key={device.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5" />
                    <CardTitle className="text-lg">{device.name}</CardTitle>
                  </div>
                  <Badge variant={device.status === "online" ? "default" : "secondary"}>{device.status}</Badge>
                </div>
                <CardDescription>
                  {device.host}:{device.port}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Brightness</span>
                    <span className="font-medium">{device.brightness}%</span>
                  </div>
                  <Slider
                    value={[device.brightness]}
                    onValueChange={(value) => handleBrightnessChange(device.id, value)}
                    max={100}
                    step={1}
                    disabled={device.status === "offline" || controlMutation.isPending}
                  />
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Effect</span>
                  <span className="font-medium">{device.effect || "Solid"}</span>
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 bg-transparent"
                    onClick={() => controlMutation.mutate({ id: device.id, action: "on" })}
                    disabled={device.status === "offline" || controlMutation.isPending}
                  >
                    <Power className="mr-2 h-4 w-4" />
                    On
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 bg-transparent"
                    onClick={() => controlMutation.mutate({ id: device.id, action: "off" })}
                    disabled={device.status === "offline" || controlMutation.isPending}
                  >
                    <PowerOff className="mr-2 h-4 w-4" />
                    Off
                  </Button>
                </div>

                <div className="flex gap-2 pt-2 border-t">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 bg-transparent"
                    onClick={() => handleEdit(device)}
                  >
                    Edit
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
            <p className="text-muted-foreground">No WLED devices configured yet</p>
            <Button className="mt-4" onClick={() => setDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Your First Device
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
