"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
  GitCommit,
  User,
  Calendar,
  FileText,
  Server,
  Package,
  Filter,
  Download
} from "lucide-react"
import { cn } from "@/lib/utils"

interface Deployment {
  id: string
  version: string
  status: "success" | "failed" | "in_progress" | "rolled_back"
  environment: "production" | "staging" | "development"
  deployed_by: string
  deployed_at: string
  duration: number
  commit_hash: string
  commit_message: string
  changes: string[]
  services_affected: string[]
  rollback_info?: {
    rolled_back_at: string
    rolled_back_by: string
    reason: string
  }
}

const statusConfig = {
  success: {
    icon: CheckCircle2,
    color: "text-green-500",
    bg: "bg-green-500/10",
    label: "Success",
    variant: "default" as const,
  },
  failed: {
    icon: XCircle,
    color: "text-red-500",
    bg: "bg-red-500/10",
    label: "Failed",
    variant: "destructive" as const,
  },
  in_progress: {
    icon: Clock,
    color: "text-blue-500",
    bg: "bg-blue-500/10",
    label: "In Progress",
    variant: "secondary" as const,
  },
  rolled_back: {
    icon: AlertCircle,
    color: "text-orange-500",
    bg: "bg-orange-500/10",
    label: "Rolled Back",
    variant: "outline" as const,
  },
}

const environmentConfig = {
  production: { color: "bg-red-500", label: "Production" },
  staging: { color: "bg-yellow-500", label: "Staging" },
  development: { color: "bg-green-500", label: "Development" },
}

export default function DeploymentHistoryPage() {
  const [selectedEnvironment, setSelectedEnvironment] = useState<string>("all")
  const [selectedStatus, setSelectedStatus] = useState<string>("all")

  const {
    data: deployments,
    isLoading,
    error,
  } = useQuery<Deployment[]>({
    queryKey: ["deployments", selectedEnvironment, selectedStatus],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (selectedEnvironment !== "all") params.append("environment", selectedEnvironment)
      if (selectedStatus !== "all") params.append("status", selectedStatus)

      const response = await apiClient.get(`/deployments?${params.toString()}`)
      return response.data
    },
  })

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Deployment History</h1>
          <p className="text-muted-foreground">Track all deployments across environments</p>
        </div>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Deployment History</h1>
          <p className="text-muted-foreground">Track all deployments across environments</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load deployment history. Please try again.</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Deployment History</h1>
          <p className="text-muted-foreground">Track all deployments across environments</p>
        </div>
        <Button variant="outline">
          <Download className="mr-2 h-4 w-4" />
          Export Report
        </Button>
      </div>

      {/* Statistics Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Deployments</CardDescription>
            <CardTitle className="text-3xl">{deployments?.length || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Successful</CardDescription>
            <CardTitle className="text-3xl text-green-500">
              {deployments?.filter((d) => d.status === "success").length || 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Failed</CardDescription>
            <CardTitle className="text-3xl text-red-500">
              {deployments?.filter((d) => d.status === "failed").length || 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Success Rate</CardDescription>
            <CardTitle className="text-3xl">
              {deployments && deployments.length > 0
                ? Math.round((deployments.filter((d) => d.status === "success").length / deployments.length) * 100)
                : 0}
              %
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex gap-2">
              <Button
                variant={selectedEnvironment === "all" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedEnvironment("all")}
              >
                All Environments
              </Button>
              {Object.entries(environmentConfig).map(([env, config]) => (
                <Button
                  key={env}
                  variant={selectedEnvironment === env ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedEnvironment(env)}
                >
                  <div className={cn("w-2 h-2 rounded-full mr-2", config.color)} />
                  {config.label}
                </Button>
              ))}
            </div>
            <div className="flex gap-2 ml-auto">
              <Button
                variant={selectedStatus === "all" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedStatus("all")}
              >
                All Statuses
              </Button>
              {Object.entries(statusConfig).map(([status, config]) => (
                <Button
                  key={status}
                  variant={selectedStatus === status ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedStatus(status)}
                >
                  {config.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Deployment Timeline</CardTitle>
          <CardDescription>Chronological view of all deployments</CardDescription>
        </CardHeader>
        <CardContent>
          {deployments && deployments.length > 0 ? (
            <div className="relative space-y-6">
              {/* Timeline line */}
              <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-border" />

              {deployments.map((deployment, index) => {
                const statusInfo = statusConfig[deployment.status]
                const envInfo = environmentConfig[deployment.environment]
                const StatusIcon = statusInfo.icon

                return (
                  <div key={deployment.id} className="relative pl-10">
                    {/* Timeline dot */}
                    <div
                      className={cn(
                        "absolute left-0 w-6 h-6 rounded-full border-4 border-background flex items-center justify-center",
                        statusInfo.bg
                      )}
                    >
                      <div className={cn("w-2 h-2 rounded-full", statusInfo.color.replace("text-", "bg-"))} />
                    </div>

                    <Card className={cn("transition-all hover:shadow-md", deployment.status === "in_progress" && "border-blue-500")}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <StatusIcon className={cn("h-5 w-5", statusInfo.color)} />
                            <div>
                              <CardTitle className="text-lg flex items-center gap-2">
                                v{deployment.version}
                                <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
                                <Badge variant="outline">
                                  <div className={cn("w-2 h-2 rounded-full mr-1", envInfo.color)} />
                                  {envInfo.label}
                                </Badge>
                              </CardTitle>
                              <CardDescription className="flex items-center gap-4 mt-1">
                                <span className="flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  {formatDate(deployment.deployed_at)}
                                </span>
                                <span className="flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {formatDuration(deployment.duration)}
                                </span>
                                <span className="flex items-center gap-1">
                                  <User className="h-3 w-3" />
                                  {deployment.deployed_by}
                                </span>
                              </CardDescription>
                            </div>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {/* Commit info */}
                        <div className="flex items-start gap-2 p-3 rounded-lg bg-muted/50">
                          <GitCommit className="h-4 w-4 mt-0.5 text-muted-foreground" />
                          <div className="flex-1 min-w-0">
                            <code className="text-xs font-mono">{deployment.commit_hash}</code>
                            <p className="text-sm mt-1">{deployment.commit_message}</p>
                          </div>
                        </div>

                        {/* Services affected */}
                        {deployment.services_affected.length > 0 && (
                          <div>
                            <p className="text-sm font-medium mb-2 flex items-center gap-2">
                              <Server className="h-4 w-4" />
                              Services Affected
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {deployment.services_affected.map((service) => (
                                <Badge key={service} variant="secondary">
                                  <Package className="h-3 w-3 mr-1" />
                                  {service}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Changes */}
                        {deployment.changes.length > 0 && (
                          <div>
                            <p className="text-sm font-medium mb-2 flex items-center gap-2">
                              <FileText className="h-4 w-4" />
                              Changes ({deployment.changes.length})
                            </p>
                            <ul className="space-y-1 text-sm text-muted-foreground">
                              {deployment.changes.slice(0, 3).map((change, i) => (
                                <li key={i} className="flex items-start gap-2">
                                  <span className="text-primary mt-1">•</span>
                                  <span>{change}</span>
                                </li>
                              ))}
                              {deployment.changes.length > 3 && (
                                <li className="text-xs italic">
                                  +{deployment.changes.length - 3} more changes
                                </li>
                              )}
                            </ul>
                          </div>
                        )}

                        {/* Rollback info */}
                        {deployment.rollback_info && (
                          <Alert>
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>
                              <p className="font-medium">Rolled back by {deployment.rollback_info.rolled_back_by}</p>
                              <p className="text-sm">{deployment.rollback_info.reason}</p>
                              <p className="text-xs text-muted-foreground mt-1">
                                {formatDate(deployment.rollback_info.rolled_back_at)}
                              </p>
                            </AlertDescription>
                          </Alert>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Package className="h-12 w-12 mx-auto opacity-50 mb-4" />
              <p>No deployments found</p>
              <p className="text-sm">Deployment history will appear here</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
