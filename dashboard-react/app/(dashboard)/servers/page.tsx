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
import { Plus, Trash2, AlertCircle, CheckCircle, Loader2, TestTube, ExternalLink } from "lucide-react"
import { toast } from "sonner"
import { ServerForm } from "@/components/forms/server-form"

interface Server {
  id: string
  name: string
  host: string
  port: number
  username: string
  status: "online" | "offline" | "unknown"
  created_at: string
}

export default function ServersPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingServer, setEditingServer] = useState<Server | null>(null)
  const queryClient = useQueryClient()

  const {
    data: servers,
    isLoading,
    error,
  } = useQuery<Server[]>({
    queryKey: ["servers"],
    queryFn: async () => {
      const response = await apiClient.get("/servers")
      return response.data
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/servers/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["servers"] })
      toast.success("Server deleted successfully")
    },
    onError: () => {
      toast.error("Failed to delete server")
    },
  })

  const testConnectionMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await apiClient.post(`/servers/${id}/test`)
      return response.data
    },
    onSuccess: (data) => {
      toast.success(data.message || "Connection successful")
      queryClient.invalidateQueries({ queryKey: ["servers"] })
    },
    onError: () => {
      toast.error("Connection test failed")
    },
  })

  const handleEdit = (server: Server) => {
    setEditingServer(server)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingServer(null)
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Servers</h1>
            <p className="text-muted-foreground">Manage your SSH servers</p>
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
          <h1 className="text-3xl font-bold">Servers</h1>
          <p className="text-muted-foreground">Manage your SSH servers</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load servers. Please try again.</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Servers</h1>
          <p className="text-muted-foreground">Manage your SSH servers</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => setEditingServer(null)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Server
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingServer ? "Edit Server" : "Add New Server"}</DialogTitle>
              <DialogDescription>
                {editingServer ? "Update the server configuration" : "Configure a new SSH server connection"}
              </DialogDescription>
            </DialogHeader>
            <ServerForm server={editingServer} onSuccess={handleCloseDialog} />
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>SSH Servers</CardTitle>
          <CardDescription>List of configured SSH servers</CardDescription>
        </CardHeader>
        <CardContent>
          {servers && servers.length > 0 ? (
            <ResponsiveTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Host</TableHead>
                    <TableHead>Port</TableHead>
                    <TableHead>Username</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {servers.map((server) => (
                    <TableRow key={server.id}>
                      <TableCell className="font-medium">{server.name}</TableCell>
                      <TableCell>{server.host}</TableCell>
                      <TableCell>{server.port}</TableCell>
                      <TableCell>{server.username}</TableCell>
                      <TableCell>
                        <Badge variant={server.status === "online" ? "default" : "secondary"}>
                          {server.status === "online" && <CheckCircle className="mr-1 h-3 w-3" />}
                          {server.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            title="Open Node-RED"
                            onClick={() => window.open(`http://${server.host}:1880`, '_blank')}
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => testConnectionMutation.mutate(server.id)}
                            disabled={testConnectionMutation.isPending}
                          >
                            {testConnectionMutation.isPending ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <TestTube className="h-4 w-4" />
                            )}
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => handleEdit(server)}>
                            Edit
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => deleteMutation.mutate(server.id)}
                            disabled={deleteMutation.isPending}
                          >
                            {deleteMutation.isPending ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ResponsiveTable>
          ) : (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No servers configured yet</p>
              <Button className="mt-4" onClick={() => setDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Your First Server
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
