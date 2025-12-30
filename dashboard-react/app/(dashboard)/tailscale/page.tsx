"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  ResponsiveTable,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/responsive-table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, Loader2, Network, RefreshCw } from "lucide-react"
import { toast } from "sonner"

interface TailscaleDevice {
  id: string
  hostname: string
  ip: string
  status: "online" | "offline"
  last_seen: string
  os: string
  user: string
}

export default function TailscalePage() {
  const queryClient = useQueryClient()

  const {
    data: devices,
    isLoading,
    error,
  } = useQuery<TailscaleDevice[]>({
    queryKey: ["tailscale-devices"],
    queryFn: async () => {
      const response = await apiClient.get("/tailscale/devices")
      return response.data
    },
  })

  const refreshMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post("/tailscale/refresh")
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tailscale-devices"] })
      toast.success("Devices refreshed")
    },
    onError: () => {
      toast.error("Failed to refresh devices")
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Tailscale</h1>
            <p className="text-muted-foreground">Manage VPN devices</p>
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Tailscale</h1>
          <p className="text-muted-foreground">Manage VPN devices</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load Tailscale devices. Please try again.</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tailscale</h1>
          <p className="text-muted-foreground">Manage VPN devices</p>
        </div>
        <Button onClick={() => refreshMutation.mutate()} disabled={refreshMutation.isPending}>
          {refreshMutation.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Connected Devices</CardTitle>
          <CardDescription>Devices in your Tailscale network</CardDescription>
        </CardHeader>
        <CardContent>
          {devices && devices.length > 0 ? (
            <ResponsiveTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Hostname</TableHead>
                    <TableHead>IP Address</TableHead>
                    <TableHead>OS</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last Seen</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {devices.map((device) => (
                    <TableRow key={device.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <Network className="h-4 w-4 text-muted-foreground" />
                          {device.hostname}
                        </div>
                      </TableCell>
                      <TableCell>{device.ip}</TableCell>
                      <TableCell>{device.os}</TableCell>
                      <TableCell>{device.user}</TableCell>
                      <TableCell>
                        <Badge variant={device.status === "online" ? "default" : "secondary"}>{device.status}</Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{device.last_seen}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ResponsiveTable>
          ) : (
            <div className="text-center py-12 text-muted-foreground">No devices found</div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
