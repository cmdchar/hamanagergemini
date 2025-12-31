"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Textarea } from "@/components/ui/textarea"
import { RefreshCw, FileText, ArrowLeft, Save } from "lucide-react"
import { toast } from "sonner"
import Link from "next/link"
import { useParams } from "next/navigation"

interface HaConfig {
  id: string
  path: string
  content: string
  updated_at: string
}

export default function ServerConfigPage() {
  const params = useParams()
  const serverId = params.id as string
  const [selectedConfig, setSelectedConfig] = useState<HaConfig | null>(null)
  const [editedContent, setEditedContent] = useState<string>("")
  const queryClient = useQueryClient()

  const { data: configs, isLoading } = useQuery<HaConfig[]>({
    queryKey: ["server-configs", serverId],
    queryFn: async () => {
      const response = await apiClient.get(`/servers/${serverId}/configs`)
      return response.data
    },
  })

  const syncMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/servers/${serverId}/sync-config`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["server-configs", serverId] })
      toast.success("Configurations synced successfully")
    },
    onError: () => {
      toast.error("Failed to sync configurations")
    },
  })

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!selectedConfig) return
      const response = await apiClient.put(`/servers/${serverId}/configs/${selectedConfig.id}`, {
        content: editedContent
      })
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["server-configs", serverId] })
      // Update local state to reflect saved content
      if (selectedConfig) {
        setSelectedConfig({
          ...selectedConfig,
          content: editedContent
        })
      }
      toast.success("Configuration saved successfully")
    },
    onError: (error: any) => {
      console.error("Save error:", error)
      toast.error(`Failed to save configuration: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleSelectConfig = (config: HaConfig) => {
    setSelectedConfig(config)
    setEditedContent(config.content)
  }

  return (
    <div className="space-y-6 h-[calc(100vh-100px)] flex flex-col">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/servers">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <h1 className="text-2xl font-bold tracking-tight">Home Assistant Configuration</h1>
        </div>
        <Button 
          onClick={() => syncMutation.mutate()} 
          disabled={syncMutation.isPending}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${syncMutation.isPending ? "animate-spin" : ""}`} />
          Sync from Server
        </Button>
      </div>

      <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
        <Card className="col-span-3 flex flex-col h-full">
          <CardHeader>
            <CardTitle className="text-lg">Files</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden p-0">
            <ScrollArea className="h-full">
              <div className="space-y-1 p-4">
                {isLoading ? (
                  <p className="text-sm text-muted-foreground">Loading...</p>
                ) : configs?.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No configs found. Click Sync.</p>
                ) : (
                  configs?.map((config) => (
                    <Button
                      key={config.id}
                      variant={selectedConfig?.id === config.id ? "secondary" : "ghost"}
                      className="w-full justify-start font-mono text-sm truncate"
                      onClick={() => handleSelectConfig(config)}
                      title={config.path}
                    >
                      <FileText className="mr-2 h-4 w-4 shrink-0" />
                      <span className="truncate">{config.path.replace("/config/", "")}</span>
                    </Button>
                  ))
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card className="col-span-9 flex flex-col h-full">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <CardTitle className="text-lg font-mono">
              {selectedConfig ? selectedConfig.path : "Select a file"}
            </CardTitle>
            {selectedConfig && (
              <Button 
                onClick={() => saveMutation.mutate()}
                disabled={saveMutation.isPending || editedContent === selectedConfig.content}
                size="sm"
              >
                <Save className="mr-2 h-4 w-4" />
                {saveMutation.isPending ? "Saving..." : "Save Changes"}
              </Button>
            )}
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden min-h-0 p-0">
             {selectedConfig ? (
               <div className="h-full w-full p-0">
                 <Textarea
                   value={editedContent}
                   onChange={(e) => setEditedContent(e.target.value)}
                   className="h-full w-full resize-none font-mono text-sm border-0 focus-visible:ring-0 rounded-none p-4"
                   spellCheck={false}
                 />
               </div>
             ) : (
               <div className="flex h-full items-center justify-center text-muted-foreground">
                 Select a file to view and edit its content
               </div>
             )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
