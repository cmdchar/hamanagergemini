"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { DiffViewer, SideBySideDiffViewer } from "@/components/diff-viewer"
import { toast } from "sonner"
import { FileEdit, CheckCircle, XCircle, Upload, GitBranch, Trash2 } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"

interface AIModification {
  id: string
  file_path: string
  action: "create" | "update" | "delete"
  status: "pending" | "approved" | "rejected" | "reverted"
  ai_summary: string | null
  pushed_to_server: boolean
  pushed_to_github: boolean
  created_at: string
  updated_at: string
}

interface AIModificationDetail {
  id: string
  file_path: string
  action: "create" | "update" | "delete"
  status: "pending" | "approved" | "rejected" | "reverted"
  content_before: string | null
  content_after: string
  ai_summary: string | null
  ai_explanation: string | null
  created_at: string
}

export default function AIModificationsPage() {
  const queryClient = useQueryClient()
  const [selectedModification, setSelectedModification] = useState<string | null>(null)
  const [reviewComment, setReviewComment] = useState("")
  const [viewMode, setViewMode] = useState<"unified" | "split">("unified")
  const [showPushDialog, setShowPushDialog] = useState(false)
  const [pushOptions, setPushOptions] = useState({ server: false, github: false })
  const [commitMessage, setCommitMessage] = useState("")

  // Fetch modifications list
  const { data: modifications, isLoading } = useQuery<AIModification[]>({
    queryKey: ["ai-modifications"],
    queryFn: async () => {
      const response = await apiClient.get("/ai/files/modifications")
      return response.data
    },
  })

  // Fetch selected modification detail
  const { data: modificationDetail } = useQuery<AIModificationDetail>({
    queryKey: ["ai-modification", selectedModification],
    enabled: !!selectedModification,
    queryFn: async () => {
      const response = await apiClient.get(`/ai/files/modifications/${selectedModification}`)
      return response.data
    },
  })

  // Review mutation
  const reviewMutation = useMutation({
    mutationFn: async ({
      id,
      status,
      comment,
    }: {
      id: string
      status: "approved" | "rejected"
      comment?: string
    }) => {
      await apiClient.post(`/ai/files/modifications/${id}/review`, {
        status,
        review_comment: comment,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-modifications"] })
      queryClient.invalidateQueries({ queryKey: ["ai-modification", selectedModification] })
      toast.success("Modification reviewed successfully")
      setReviewComment("")
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to review modification")
    },
  })

  // Push mutation
  const pushMutation = useMutation({
    mutationFn: async ({
      id,
      pushToServer,
      pushToGithub,
      commitMsg,
    }: {
      id: string
      pushToServer: boolean
      pushToGithub: boolean
      commitMsg?: string
    }) => {
      await apiClient.post(`/ai/files/modifications/${id}/push`, {
        push_to_server: pushToServer,
        push_to_github: pushToGithub,
        commit_message: commitMsg,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-modifications"] })
      queryClient.invalidateQueries({ queryKey: ["ai-modification", selectedModification] })
      toast.success("Modification pushed successfully")
      setShowPushDialog(false)
      setPushOptions({ server: false, github: false })
      setCommitMessage("")
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to push modification")
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/ai/files/modifications/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-modifications"] })
      toast.success("Modification deleted successfully")
      setSelectedModification(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to delete modification")
    },
  })

  const handleApprove = () => {
    if (!selectedModification) return
    reviewMutation.mutate({
      id: selectedModification,
      status: "approved",
      comment: reviewComment || undefined,
    })
  }

  const handleReject = () => {
    if (!selectedModification) return
    reviewMutation.mutate({
      id: selectedModification,
      status: "rejected",
      comment: reviewComment || undefined,
    })
  }

  const handlePush = () => {
    if (!selectedModification) return
    pushMutation.mutate({
      id: selectedModification,
      pushToServer: pushOptions.server,
      pushToGithub: pushOptions.github,
      commitMsg: commitMessage || undefined,
    })
  }

  const handleDelete = () => {
    if (!selectedModification) return
    if (confirm("Are you sure you want to delete this modification?")) {
      deleteMutation.mutate(selectedModification)
    }
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: any; icon: any }> = {
      pending: { variant: "outline", icon: FileEdit },
      approved: { variant: "default", icon: CheckCircle },
      rejected: { variant: "destructive", icon: XCircle },
    }
    const config = variants[status] || variants.pending
    const Icon = config.icon

    return (
      <Badge variant={config.variant as any} className="gap-1">
        <Icon className="h-3 w-3" />
        {status}
      </Badge>
    )
  }

  const getActionBadge = (action: string) => {
    const colors: Record<string, string> = {
      create: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
      update: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
      delete: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    }

    return (
      <Badge variant="outline" className={colors[action] || ""}>
        {action}
      </Badge>
    )
  }

  const pendingMods = modifications?.filter((m) => m.status === "pending") || []
  const approvedMods = modifications?.filter((m) => m.status === "approved") || []
  const rejectedMods = modifications?.filter((m) => m.status === "rejected") || []

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">AI File Modifications</h1>
          <p className="text-muted-foreground mt-1">Review and manage AI-proposed changes to your configuration files</p>
        </div>
      </div>

      <Tabs defaultValue="pending" className="space-y-4">
        <TabsList>
          <TabsTrigger value="pending">
            Pending <Badge className="ml-2">{pendingMods.length}</Badge>
          </TabsTrigger>
          <TabsTrigger value="approved">Approved ({approvedMods.length})</TabsTrigger>
          <TabsTrigger value="rejected">Rejected ({rejectedMods.length})</TabsTrigger>
          <TabsTrigger value="all">All ({modifications?.length || 0})</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4">
          {pendingMods.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No pending modifications
              </CardContent>
            </Card>
          ) : (
            pendingMods.map((mod) => (
              <ModificationCard
                key={mod.id}
                modification={mod}
                onSelect={setSelectedModification}
                isSelected={selectedModification === mod.id}
                getStatusBadge={getStatusBadge}
                getActionBadge={getActionBadge}
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="approved" className="space-y-4">
          {approvedMods.map((mod) => (
            <ModificationCard
              key={mod.id}
              modification={mod}
              onSelect={setSelectedModification}
              isSelected={selectedModification === mod.id}
              getStatusBadge={getStatusBadge}
              getActionBadge={getActionBadge}
            />
          ))}
        </TabsContent>

        <TabsContent value="rejected" className="space-y-4">
          {rejectedMods.map((mod) => (
            <ModificationCard
              key={mod.id}
              modification={mod}
              onSelect={setSelectedModification}
              isSelected={selectedModification === mod.id}
              getStatusBadge={getStatusBadge}
              getActionBadge={getActionBadge}
            />
          ))}
        </TabsContent>

        <TabsContent value="all" className="space-y-4">
          {modifications?.map((mod) => (
            <ModificationCard
              key={mod.id}
              modification={mod}
              onSelect={setSelectedModification}
              isSelected={selectedModification === mod.id}
              getStatusBadge={getStatusBadge}
              getActionBadge={getActionBadge}
            />
          ))}
        </TabsContent>
      </Tabs>

      {/* Modification Detail Dialog */}
      <Dialog open={!!selectedModification} onOpenChange={(open) => !open && setSelectedModification(null)}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileEdit className="h-5 w-5" />
              {modificationDetail?.file_path}
            </DialogTitle>
            <DialogDescription>
              {modificationDetail?.ai_explanation || modificationDetail?.ai_summary || "No description provided"}
            </DialogDescription>
          </DialogHeader>

          {modificationDetail && (
            <div className="space-y-4">
              <div className="flex gap-2">
                {getActionBadge(modificationDetail.action)}
                {getStatusBadge(modificationDetail.status)}
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setViewMode("unified")}
                  className={viewMode === "unified" ? "bg-accent" : ""}
                >
                  Unified
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setViewMode("split")}
                  className={viewMode === "split" ? "bg-accent" : ""}
                >
                  Split
                </Button>
              </div>

              {viewMode === "unified" ? (
                <DiffViewer
                  oldText={modificationDetail.content_before || ""}
                  newText={modificationDetail.content_after}
                  fileName={modificationDetail.file_path}
                />
              ) : (
                <SideBySideDiffViewer
                  oldText={modificationDetail.content_before || ""}
                  newText={modificationDetail.content_after}
                  fileName={modificationDetail.file_path}
                />
              )}

              {modificationDetail.status === "pending" && (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="review-comment">Review Comment (Optional)</Label>
                    <Textarea
                      id="review-comment"
                      value={reviewComment}
                      onChange={(e) => setReviewComment(e.target.value)}
                      placeholder="Add a comment about this change..."
                      className="mt-2"
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            {modificationDetail?.status === "pending" && (
              <>
                <Button variant="destructive" onClick={handleDelete} disabled={deleteMutation.isPending}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </Button>
                <Button variant="outline" onClick={handleReject} disabled={reviewMutation.isPending}>
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject
                </Button>
                <Button onClick={handleApprove} disabled={reviewMutation.isPending}>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Approve
                </Button>
              </>
            )}
            {modificationDetail?.status === "approved" && (
              <Button onClick={() => setShowPushDialog(true)}>
                <Upload className="h-4 w-4 mr-2" />
                Push Changes
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Push Dialog */}
      <Dialog open={showPushDialog} onOpenChange={setShowPushDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Push Modification</DialogTitle>
            <DialogDescription>Choose where to push the approved changes</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="push-server"
                checked={pushOptions.server}
                onChange={(e) => setPushOptions((prev) => ({ ...prev, server: e.target.checked }))}
                className="h-4 w-4"
              />
              <Label htmlFor="push-server" className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Push to Server
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="push-github"
                checked={pushOptions.github}
                onChange={(e) => setPushOptions((prev) => ({ ...prev, github: e.target.checked }))}
                className="h-4 w-4"
              />
              <Label htmlFor="push-github" className="flex items-center gap-2">
                <GitBranch className="h-4 w-4" />
                Push to GitHub
              </Label>
            </div>

            {pushOptions.github && (
              <div>
                <Label htmlFor="commit-message">Commit Message</Label>
                <Textarea
                  id="commit-message"
                  value={commitMessage}
                  onChange={(e) => setCommitMessage(e.target.value)}
                  placeholder="Enter commit message..."
                  className="mt-2"
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPushDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={handlePush}
              disabled={(!pushOptions.server && !pushOptions.github) || pushMutation.isPending}
            >
              Push
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function ModificationCard({
  modification,
  onSelect,
  isSelected,
  getStatusBadge,
  getActionBadge,
}: {
  modification: AIModification
  onSelect: (id: string) => void
  isSelected: boolean
  getStatusBadge: (status: string) => JSX.Element
  getActionBadge: (action: string) => JSX.Element
}) {
  return (
    <Card
      className={`cursor-pointer hover:shadow-md transition-shadow ${isSelected ? "ring-2 ring-primary" : ""}`}
      onClick={() => onSelect(modification.id)}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg font-mono">{modification.file_path}</CardTitle>
            {modification.ai_summary && <CardDescription>{modification.ai_summary}</CardDescription>}
          </div>
          <div className="flex gap-2">
            {getActionBadge(modification.action)}
            {getStatusBadge(modification.status)}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>Created: {new Date(modification.created_at).toLocaleString()}</span>
          {modification.pushed_to_server && (
            <Badge variant="outline" className="gap-1">
              <Upload className="h-3 w-3" />
              Server
            </Badge>
          )}
          {modification.pushed_to_github && (
            <Badge variant="outline" className="gap-1">
              <GitBranch className="h-3 w-3" />
              GitHub
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
