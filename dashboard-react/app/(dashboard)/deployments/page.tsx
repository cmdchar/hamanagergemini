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
import { Plus, Play, Square, RotateCw, Trash2, AlertCircle, Loader2 } from "lucide-react"
import { toast } from "sonner"
import { DeploymentForm } from "@/components/forms/deployment-form"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

interface Deployment {
  id: string
  name: string
  server_id: string
  server_name: string
  path: string
  status: "running" | "stopped" | "error"
  pm2_id: number
  uptime: string
  memory: string
  cpu: string
  created_at: string
}

export default function DeploymentsPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingDeployment, setEditingDeployment] = useState<Deployment | null>(null)
  const queryClient = useQueryClient()

  const {
    data: deployments,
    isLoading,
    error,
  } = useQuery<Deployment[]>({
    queryKey: ["deployments"],
    queryFn: async () => {
      const response = await apiClient.get("/deployments")
      return response.data
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/deployments/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deployments"] })
      toast.success("Deployment deleted successfully")
    },
    onError: () => {
      toast.error("Failed to delete deployment")
    },
  })

  const actionMutation = useMutation({
    mutationFn: async ({ id, action }: { id: string; action: string }) => {
      const response = await apiClient.post(`/deployments/${id}/${action}`)
      return response.data
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["deployments"] })
      toast.success(`Deployment ${variables.action} successful`)
    },
    onError: (error: any, variables) => {
      toast.error(`Failed to ${variables.action} deployment`)
    },
  })

  const handleEdit = (deployment: Deployment) => {
    setEditingDeployment(deployment)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingDeployment(null)
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Deployments</h1>
            <p className="text-muted-foreground">Manage HA deployments with PM2</p>
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
          <h1 className="text-3xl font-bold">Deployments</h1>
          <p className="text-muted-foreground">Manage HA deployments with PM2</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load deployments. Please try again.</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Deployments</h1>
          <p className="text-muted-foreground">Manage HA deployments with PM2</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => setEditingDeployment(null)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Deployment
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingDeployment ? "Edit Deployment" : "Add New Deployment"}</DialogTitle>
              <DialogDescription>
                {editingDeployment ? "Update the deployment configuration" : "Configure a new HA deployment"}
              </DialogDescription>
            </DialogHeader>
            <DeploymentForm deployment={editingDeployment} onSuccess={handleCloseDialog} />
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>HA Deployments</CardTitle>
          <CardDescription>List of Home Assistant deployments managed by PM2</CardDescription>
        </CardHeader>
        <CardContent>
          {deployments && deployments.length > 0 ? (
            <ResponsiveTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Server</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Uptime</TableHead>
                    <TableHead>CPU</TableHead>
                    <TableHead>Memory</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {deployments.map((deployment) => (
                    <TableRow key={deployment.id}>
                      <TableCell className="font-medium">{deployment.name}</TableCell>
                      <TableCell>{deployment.server_name}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            deployment.status === "running"
                              ? "default"
                              : deployment.status === "stopped"
                                ? "secondary"
                                : "destructive"
                          }
                        >
                          {deployment.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{deployment.uptime || "N/A"}</TableCell>
                      <TableCell>{deployment.cpu || "N/A"}</TableCell>
                      <TableCell>{deployment.memory || "N/A"}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="outline" size="sm" disabled={actionMutation.isPending}>
                                {actionMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Actions"}
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() => actionMutation.mutate({ id: deployment.id, action: "start" })}
                                disabled={deployment.status === "running"}
                              >
                                <Play className="mr-2 h-4 w-4" />
                                Start
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => actionMutation.mutate({ id: deployment.id, action: "stop" })}
                                disabled={deployment.status === "stopped"}
                              >
                                <Square className="mr-2 h-4 w-4" />
                                Stop
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => actionMutation.mutate({ id: deployment.id, action: "restart" })}
                              >
                                <RotateCw className="mr-2 h-4 w-4" />
                                Restart
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                          <Button variant="outline" size="sm" onClick={() => handleEdit(deployment)}>
                            Edit
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => deleteMutation.mutate(deployment.id)}
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
              <p className="text-muted-foreground">No deployments configured yet</p>
              <Button className="mt-4" onClick={() => setDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Your First Deployment
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
