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
import { Plus, Trash2, AlertCircle, Loader2, Radio, Play, Square, RotateCw } from "lucide-react"
import { toast } from "sonner"
import { FPPForm } from "@/components/forms/fpp-form"

interface FPPDevice {
  id: string
  name: string
  host: string
  port: number
  status: "online" | "offline"
  mode: "player" | "remote" | "bridge"
  current_playlist: string | null
  current_sequence: string | null
  created_at: string
}

export default function FPPPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingDevice, setEditingDevice] = useState<FPPDevice | null>(null)
  const queryClient = useQueryClient()

  const {
    data: devices,
    isLoading,
    error,
  } = useQuery<FPPDevice[]>({
    queryKey: ["fpp-devices"],
    queryFn: async () => {
      const response = await apiClient.get("/fpp/devices")
      return response.data
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/fpp/devices/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fpp-devices"] })
      toast.success("Device deleted successfully")
    },
    onError: () => {
      toast.error("Failed to delete device")
    },
  })

  const controlMutation = useMutation({
    mutationFn: async ({ id, action }: { id: string; action: string }) => {
      let endpoint = "";
      let payload = {};
      
      if (action === "stop") {
        endpoint = `/fpp/devices/${id}/playlist/stop`;
        // stop endpoint might require empty body or none, usually POSTs are fine with empty dict if schema allows or no body.
        // Backend `stop_playlist` takes no body args, just dependencies.
      } else if (action === "play") {
         // Placeholder: logic requires playlist name
         endpoint = `/fpp/devices/${id}/playlist/start`;
         // This will likely fail validation without body
      } else {
         // Fallback or other actions
         endpoint = `/fpp/devices/${id}/${action}`;
      }
      
      const response = await apiClient.post(endpoint, payload)
      return response.data
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["fpp-devices"] })
      toast.success(`${variables.action} command sent`)
    },
    onError: () => {
      toast.error("Failed to send command")
    },
  })

  const handleEdit = (device: FPPDevice) => {
    setEditingDevice(device)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingDevice(null)
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Falcon Player (FPP)</h1>
            <p className="text-muted-foreground">Manage FPP devices</p>
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
          <h1 className="text-3xl font-bold">Falcon Player (FPP)</h1>
          <p className="text-muted-foreground">Manage FPP devices</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load FPP devices. Please try again.</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Falcon Player (FPP)</h1>
          <p className="text-muted-foreground">Manage FPP devices</p>
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
              <DialogTitle>{editingDevice ? "Edit Device" : "Add New FPP Device"}</DialogTitle>
              <DialogDescription>
                {editingDevice ? "Update the device configuration" : "Configure a new Falcon Player device"}
              </DialogDescription>
            </DialogHeader>
            <FPPForm device={editingDevice} onSuccess={handleCloseDialog} />
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
                    <Radio className="h-5 w-5" />
                    <CardTitle className="text-lg">{device.name}</CardTitle>
                  </div>
                  <Badge variant={device.status === "online" ? "default" : "secondary"}>{device.status}</Badge>
                </div>
                <CardDescription>
                  {device.host}:{device.port}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Mode</span>
                    <Badge variant="outline">{device.mode}</Badge>
                  </div>
                  {device.current_playlist && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Playlist</span>
                      <span className="font-medium truncate max-w-[150px]">{device.current_playlist}</span>
                    </div>
                  )}
                  {device.current_sequence && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Sequence</span>
                      <span className="font-medium truncate max-w-[150px]">{device.current_sequence}</span>
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 bg-transparent"
                    onClick={() => controlMutation.mutate({ id: device.id, action: "play" })}
                    disabled={device.status === "offline" || controlMutation.isPending}
                  >
                    <Play className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 bg-transparent"
                    onClick={() => controlMutation.mutate({ id: device.id, action: "stop" })}
                    disabled={device.status === "offline" || controlMutation.isPending}
                  >
                    <Square className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 bg-transparent"
                    onClick={() => controlMutation.mutate({ id: device.id, action: "restart" })}
                    disabled={device.status === "offline" || controlMutation.isPending}
                  >
                    <RotateCw className="h-4 w-4" />
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
            <p className="text-muted-foreground">No FPP devices configured yet</p>
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
