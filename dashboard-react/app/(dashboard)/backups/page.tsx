"use client"

import { useState } from "react"
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
import { AlertCircle, Loader2, Download, Trash2, Plus, Database } from "lucide-react"
import { toast } from "sonner"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { format } from "date-fns"

interface Backup {
  id: string
  name: string
  type: "node-red" | "zigbee2mqtt"
  size: string
  created_at: string
}

export default function BackupsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState("all")

  const {
    data: backups,
    isLoading,
    error,
  } = useQuery<Backup[]>({
    queryKey: ["backups"],
    queryFn: async () => {
      const response = await apiClient.get("/backups")
      return response.data
    },
  })

  const createBackupMutation = useMutation({
    mutationFn: async (type: string) => {
      const response = await apiClient.post("/backups", { type })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["backups"] })
      toast.success("Backup created successfully")
    },
    onError: () => {
      toast.error("Failed to create backup")
    },
  })

  const deleteBackupMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/backups/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["backups"] })
      toast.success("Backup deleted successfully")
    },
    onError: () => {
      toast.error("Failed to delete backup")
    },
  })

  const downloadBackupMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await apiClient.get(`/backups/${id}/download`, {
        responseType: "blob",
      })
      return response.data
    },
    onSuccess: (data, id) => {
      const url = window.URL.createObjectURL(new Blob([data]))
      const link = document.createElement("a")
      link.href = url
      link.setAttribute("download", `backup-${id}.tar.gz`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      toast.success("Backup downloaded")
    },
    onError: () => {
      toast.error("Failed to download backup")
    },
  })

  const filteredBackups = activeTab === "all" ? backups : backups?.filter((backup) => backup.type === activeTab) || []

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Backups</h1>
            <p className="text-muted-foreground">Manage Node-RED and Zigbee2MQTT backups</p>
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
          <h1 className="text-3xl font-bold">Backups</h1>
          <p className="text-muted-foreground">Manage Node-RED and Zigbee2MQTT backups</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load backups. Please try again.</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Backups</h1>
          <p className="text-muted-foreground">Manage Node-RED and Zigbee2MQTT backups</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => createBackupMutation.mutate("node-red")}
            disabled={createBackupMutation.isPending}
          >
            {createBackupMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Plus className="mr-2 h-4 w-4" />
            Node-RED
          </Button>
          <Button
            variant="outline"
            onClick={() => createBackupMutation.mutate("zigbee2mqtt")}
            disabled={createBackupMutation.isPending}
          >
            {createBackupMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Plus className="mr-2 h-4 w-4" />
            Zigbee2MQTT
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">All Backups</TabsTrigger>
          <TabsTrigger value="node-red">Node-RED</TabsTrigger>
          <TabsTrigger value="zigbee2mqtt">Zigbee2MQTT</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>
                <div className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  {activeTab === "all"
                    ? "All Backups"
                    : activeTab === "node-red"
                      ? "Node-RED Backups"
                      : "Zigbee2MQTT Backups"}
                </div>
              </CardTitle>
              <CardDescription>List of backup files</CardDescription>
            </CardHeader>
            <CardContent>
              {filteredBackups && filteredBackups.length > 0 ? (
                <ResponsiveTable>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Size</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredBackups.map((backup) => (
                        <TableRow key={backup.id}>
                          <TableCell className="font-medium">{backup.name}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{backup.type}</Badge>
                          </TableCell>
                          <TableCell>{backup.size}</TableCell>
                          <TableCell className="text-muted-foreground">
                            {format(new Date(backup.created_at), "MMM dd, yyyy HH:mm")}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => downloadBackupMutation.mutate(backup.id)}
                                disabled={downloadBackupMutation.isPending}
                              >
                                {downloadBackupMutation.isPending ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Download className="h-4 w-4" />
                                )}
                              </Button>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => deleteBackupMutation.mutate(backup.id)}
                                disabled={deleteBackupMutation.isPending}
                              >
                                {deleteBackupMutation.isPending ? (
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
                <div className="text-center py-12 text-muted-foreground">
                  No {activeTab !== "all" ? activeTab : ""} backups found
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
