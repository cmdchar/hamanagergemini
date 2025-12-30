"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { AppHeader } from "@/components/app-header"
import { WebTerminal } from "@/components/terminal/web-terminal"
import { apiClient } from "@/lib/api"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Terminal as TerminalIcon, AlertCircle } from "lucide-react"

interface Server {
  id: string
  name: string
  host: string
  port: number
  username: string
}

export default function TerminalPage() {
  const [selectedServerId, setSelectedServerId] = useState<string>("")

  const { data: servers, isLoading, error } = useQuery<Server[]>({
    queryKey: ["servers"],
    queryFn: async () => {
      const response = await apiClient.get("/servers")
      return response.data
    },
  })

  // Select first server by default if not set
  if (!selectedServerId && servers && servers.length > 0) {
    setSelectedServerId(servers[0].id)
  }

  return (
    <div className="space-y-6">
      <AppHeader
        title="Terminal"
        description="SSH access to your Home Assistant servers"
      />

      <div className="flex flex-col space-y-4">
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium">Select Server:</label>
          <Select
            value={selectedServerId}
            onValueChange={setSelectedServerId}
            disabled={isLoading || !servers?.length}
          >
            <SelectTrigger className="w-[300px]">
              <SelectValue placeholder="Select a server..." />
            </SelectTrigger>
            <SelectContent>
              {servers?.map((server) => (
                <SelectItem key={server.id} value={server.id}>
                  {server.name} ({server.host})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {isLoading ? (
          <div>Loading servers...</div>
        ) : error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>Failed to load servers.</AlertDescription>
          </Alert>
        ) : !servers?.length ? (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>No Servers</AlertTitle>
            <AlertDescription>
              Please add a server in the Servers section first.
            </AlertDescription>
          </Alert>
        ) : (
          selectedServerId && (
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <TerminalIcon className="h-5 w-5" />
                  <span>Terminal Session</span>
                </CardTitle>
                <CardDescription>
                  Connected to {servers.find(s => s.id === selectedServerId)?.name}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <WebTerminal serverId={selectedServerId} />
              </CardContent>
            </Card>
          )
        )}
      </div>
    </div>
  )
}
