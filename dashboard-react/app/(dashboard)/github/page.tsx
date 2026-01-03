"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import {
  Github,
  GitBranch,
  Loader2,
  CheckCircle2,
  XCircle,
  ExternalLink,
  RefreshCw,
  Rocket,
  AlertCircle,
  Link as LinkIcon,
  Unlink,
  Copy,
  Check,
  Settings,
  BookOpen,
  Key,
  Lock,
  Shield,
  ArrowRight,
  Save,
  Eye,
  EyeOff,
  FileCode,
  Folder,
  ChevronDown,
  ChevronRight,
  ArrowLeft,
  Home,
  CheckSquare,
  Square,
  AlertTriangle,
} from "lucide-react"
import { toast } from "sonner"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"

interface GitHubRepo {
  id: string
  name: string
  full_name: string
  description: string
  private: boolean
  clone_url: string
  default_branch: string
  updated_at: string
}

interface GitHubBranch {
  name: string
  commit: string
  protected: boolean
}

interface Server {
  id: string
  name: string
  host: string
  github_repo?: string
  github_branch?: string
}

interface WebhookConfig {
  enabled: boolean
  url: string
  secret: string
  events: string[]
}

export default function GitHubPage() {
  const router = useRouter()
  const [selectedRepo, setSelectedRepo] = useState<string>("")
  const [selectedBranch, setSelectedBranch] = useState<string>("")
  const [selectedServer, setSelectedServer] = useState<string>("")
  const [webhookDialogOpen, setWebhookDialogOpen] = useState(false)
  const [copiedWebhook, setCopiedWebhook] = useState(false)
  const [activeTab, setActiveTab] = useState("overview")

  // GitHub Configuration State
  const [showClientSecret, setShowClientSecret] = useState(false)
  const [showToken, setShowToken] = useState(false)
  const [expandedServer, setExpandedServer] = useState<string | null>(null)
  const [currentPath, setCurrentPath] = useState<string>("")
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [githubConfig, setGithubConfig] = useState({
    clientId: "",
    clientSecret: "",
    token: "",
    webhookSecret: "",
  })

  const queryClient = useQueryClient()

  // Check GitHub connection status
  const {
    data: githubStatus,
    isLoading: isLoadingStatus,
  } = useQuery({
    queryKey: ["github-status"],
    queryFn: async () => {
      try {
        const response = await apiClient.get("/github/status")
        return response.data
      } catch (error) {
        return { connected: false, username: null, email: null }
      }
    },
  })

  // Get user's repositories
  const {
    data: repositories,
    isLoading: isLoadingRepos,
  } = useQuery<GitHubRepo[]>({
    queryKey: ["github-repos"],
    queryFn: async () => {
      const response = await apiClient.get("/github/repos")
      return response.data
    },
    enabled: githubStatus?.connected,
  })

  // Get branches for selected repo
  const {
    data: branches,
    isLoading: isLoadingBranches,
  } = useQuery<GitHubBranch[]>({
    queryKey: ["github-branches", selectedRepo],
    queryFn: async () => {
      if (!selectedRepo) return []
      const response = await apiClient.get(`/github/repos/${selectedRepo}/branches`)
      return response.data
    },
    enabled: !!selectedRepo,
  })

  // Get servers
  const {
    data: servers,
  } = useQuery<Server[]>({
    queryKey: ["servers"],
    queryFn: async () => {
      const response = await apiClient.get("/servers")
      return response.data
    },
  })

  // Get webhook configuration
  const {
    data: webhookConfig,
  } = useQuery<WebhookConfig>({
    queryKey: ["github-webhook"],
    queryFn: async () => {
      const response = await apiClient.get("/github/webhook")
      return response.data
    },
  })

  // Get repository files for expanded server
  const {
    data: repoFiles,
    isLoading: isLoadingRepoFiles,
  } = useQuery({
    queryKey: ["github-files", expandedServer],
    queryFn: async () => {
      if (!expandedServer) return null
      const response = await apiClient.get(`/github/servers/${expandedServer}/files`)
      return response.data
    },
    enabled: !!expandedServer,
  })

  // Get server files for expanded server
  const {
    data: serverFiles,
    isLoading: isLoadingServerFiles,
  } = useQuery({
    queryKey: ["server-files", expandedServer, currentPath],
    queryFn: async () => {
      if (!expandedServer) return null
      const params = currentPath ? `?path=${encodeURIComponent(currentPath)}` : ""
      const response = await apiClient.get(`/ha-config/servers/${expandedServer}/files${params}`)
      return response.data
    },
    enabled: !!expandedServer,
  })

  // Helper functions for file selection
  const toggleFileSelection = (filePath: string) => {
    setSelectedFiles(prev => {
      const newSet = new Set(prev)
      if (newSet.has(filePath)) {
        newSet.delete(filePath)
      } else {
        newSet.add(filePath)
      }
      return newSet
    })
  }

  const selectAllRecommended = () => {
    if (!serverFiles?.files) return
    const recommended = serverFiles.files
      .filter((f: any) => f.recommended)
      .map((f: any) => f.path)
    setSelectedFiles(new Set(recommended))
    toast.success(`Selected ${recommended.length} recommended files`)
  }

  const selectAll = () => {
    if (!serverFiles?.files) return
    const allPaths = serverFiles.files.map((f: any) => f.path)
    setSelectedFiles(new Set(allPaths))
    toast.success(`Selected all ${allPaths.length} files`)
  }

  const deselectAll = () => {
    setSelectedFiles(new Set())
    toast.info("Deselected all files")
  }

  // Save GitHub configuration
  const saveConfigMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post("/github/config", githubConfig)
    },
    onSuccess: () => {
      toast.success("Configuration saved! Please restart the containers.")
      queryClient.invalidateQueries({ queryKey: ["github-status"] })
    },
    onError: () => {
      toast.error("Failed to save configuration")
    },
  })

  // Connect GitHub OAuth
  const connectGitHub = () => {
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID || githubConfig.clientId
    if (!clientId) {
      toast.error("GitHub Client ID not configured. Please configure in Settings tab first.")
      setActiveTab("settings")
      return
    }
    const redirectUri = `${window.location.origin}/api/auth/github/callback`
    const scope = "repo,read:user,admin:repo_hook"
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`
  }

  // Disconnect GitHub
  const disconnectMutation = useMutation({
    mutationFn: async () => {
      await apiClient.delete("/github/disconnect")
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github-status"] })
      toast.success("GitHub disconnected")
    },
    onError: () => {
      toast.error("Failed to disconnect GitHub")
    },
  })

  // Link repository to server
  const linkRepoMutation = useMutation({
    mutationFn: async () => {
      if (!selectedServer || !selectedRepo || !selectedBranch) {
        throw new Error("Please select server, repository, and branch")
      }
      await apiClient.post(`/github/servers/${selectedServer}/link`, {
        repo_url: selectedRepo,
        branch: selectedBranch,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["servers"] })
      toast.success("Repository linked to server")
      setSelectedServer("")
      setSelectedRepo("")
      setSelectedBranch("")
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to link repository")
    },
  })

  // Unlink repository from server
  const unlinkRepoMutation = useMutation({
    mutationFn: async (serverId: string) => {
      await apiClient.delete(`/github/servers/${serverId}/unlink`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["servers"] })
      toast.success("Repository unlinked")
    },
    onError: () => {
      toast.error("Failed to unlink repository")
    },
  })

  // Push to GitHub
  const pushMutation = useMutation({
    mutationFn: async (serverId: string) => {
      const response = await apiClient.post(`/github/servers/${serverId}/push`)
      return response.data
    },
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ["servers"] })
      toast.success(data.message || "Configuration pushed to GitHub successfully")
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to push to GitHub")
    },
  })

  // Pull from GitHub
  const pullMutation = useMutation({
    mutationFn: async (serverId: string) => {
      const response = await apiClient.post(`/github/servers/${serverId}/pull`)
      return response.data
    },
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ["servers"] })
      toast.success(data.message || "Configuration pulled from GitHub successfully")
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to pull from GitHub")
    },
  })

  // Deploy from GitHub (deprecated - use pullMutation instead)
  const deployMutation = pullMutation

  // Create/update webhook
  const webhookMutation = useMutation({
    mutationFn: async (repo: string) => {
      await apiClient.post(`/github/repos/${repo}/webhook`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github-webhook"] })
      toast.success("Webhook created")
      setWebhookDialogOpen(false)
    },
    onError: () => {
      toast.error("Failed to create webhook")
    },
  })

  const copyWebhookUrl = () => {
    if (webhookConfig?.url) {
      navigator.clipboard.writeText(webhookConfig.url)
      setCopiedWebhook(true)
      setTimeout(() => setCopiedWebhook(false), 2000)
      toast.success("Webhook URL copied")
    }
  }

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    toast.success(`${label} copied to clipboard`)
  }

  const generateWebhookSecret = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    let result = ''
    for (let i = 0; i < 32; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    setGithubConfig({ ...githubConfig, webhookSecret: result })
    toast.success("Webhook secret generated")
  }

  if (isLoadingStatus) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">GitHub Integration</h1>
          <p className="text-muted-foreground">Connect repositories for automated deployments</p>
        </div>
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-40 w-full" />
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">GitHub Integration</h1>
        <p className="text-muted-foreground">Connect repositories for automated deployments</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="settings">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </TabsTrigger>
          <TabsTrigger value="guide">
            <BookOpen className="h-4 w-4 mr-2" />
            Setup Guide
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* GitHub Connection Status */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Github className="h-5 w-5" />
                  <CardTitle>GitHub Account</CardTitle>
                </div>
                {githubStatus?.connected ? (
                  <Badge variant="default" className="gap-1">
                    <CheckCircle2 className="h-3 w-3" />
                    Connected
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="gap-1">
                    <XCircle className="h-3 w-3" />
                    Not Connected
                  </Badge>
                )}
              </div>
              <CardDescription>
                {githubStatus?.connected
                  ? `Connected as ${githubStatus.username}`
                  : "Connect your GitHub account to enable repository-based deployments"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {githubStatus?.connected ? (
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium">Username: {githubStatus.username}</p>
                    <p className="text-sm text-muted-foreground">
                      Email: {githubStatus.email}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => disconnectMutation.mutate()}
                    disabled={disconnectMutation.isPending}
                  >
                    {disconnectMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Unlink className="h-4 w-4 mr-2" />
                    )}
                    Disconnect
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>GitHub not configured</AlertTitle>
                    <AlertDescription>
                      Please configure GitHub OAuth credentials in the Settings tab first, then connect your account.
                    </AlertDescription>
                  </Alert>
                  <Button onClick={connectGitHub} className="gap-2">
                    <Github className="h-4 w-4" />
                    Connect GitHub
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Repository Linking */}
          {githubStatus?.connected && (
            <>
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <LinkIcon className="h-5 w-5" />
                    <CardTitle>Link Repository to Server</CardTitle>
                  </div>
                  <CardDescription>
                    Select a repository and link it to a server for automated deployments
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Server</Label>
                      <Select value={selectedServer} onValueChange={setSelectedServer}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select server" />
                        </SelectTrigger>
                        <SelectContent>
                          {servers?.map((server) => (
                            <SelectItem key={server.id} value={server.id}>
                              {server.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Repository</Label>
                      <Select value={selectedRepo} onValueChange={setSelectedRepo}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select repository" />
                        </SelectTrigger>
                        <SelectContent>
                          {isLoadingRepos ? (
                            <SelectItem value="loading" disabled>
                              Loading...
                            </SelectItem>
                          ) : (
                            repositories?.map((repo) => (
                              <SelectItem key={repo.id} value={repo.full_name}>
                                {repo.full_name}
                                {repo.private && " 🔒"}
                              </SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Branch</Label>
                      <Select
                        value={selectedBranch}
                        onValueChange={setSelectedBranch}
                        disabled={!selectedRepo}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select branch" />
                        </SelectTrigger>
                        <SelectContent>
                          {isLoadingBranches ? (
                            <SelectItem value="loading" disabled>
                              Loading...
                            </SelectItem>
                          ) : (
                            branches?.map((branch) => (
                              <SelectItem key={branch.name} value={branch.name}>
                                {branch.name}
                                {branch.protected && " 🛡️"}
                              </SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <Button
                    onClick={() => linkRepoMutation.mutate()}
                    disabled={
                      !selectedServer ||
                      !selectedRepo ||
                      !selectedBranch ||
                      linkRepoMutation.isPending
                    }
                    className="gap-2"
                  >
                    {linkRepoMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <LinkIcon className="h-4 w-4" />
                    )}
                    Link Repository
                  </Button>
                </CardContent>
              </Card>

              {/* Linked Servers */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <GitBranch className="h-5 w-5" />
                      <CardTitle>Linked Repositories</CardTitle>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => queryClient.invalidateQueries({ queryKey: ["servers"] })}
                    >
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  </div>
                  <CardDescription>Servers with linked GitHub repositories</CardDescription>
                </CardHeader>
                <CardContent>
                  {servers?.filter((s) => s.github_repo).length === 0 ? (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        No servers linked to repositories yet. Link a repository above to get started.
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Server</TableHead>
                          <TableHead>Repository</TableHead>
                          <TableHead>Branch</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {servers
                          ?.filter((server) => server.github_repo)
                          .map((server) => (
                            <>
                              <TableRow key={server.id} className="hover:bg-muted/50">
                                <TableCell className="font-medium">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      const newExpandedServer = expandedServer === server.id ? null : server.id
                                      setExpandedServer(newExpandedServer)
                                      setCurrentPath("") // Reset path when expanding/collapsing
                                    }}
                                    className="gap-2 p-0 h-auto hover:bg-transparent"
                                  >
                                    {expandedServer === server.id ? (
                                      <ChevronDown className="h-4 w-4" />
                                    ) : (
                                      <ChevronRight className="h-4 w-4" />
                                    )}
                                    {server.name}
                                  </Button>
                                </TableCell>
                                <TableCell>
                                  <a
                                    href={`https://github.com/${server.github_repo}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-1 text-primary hover:underline"
                                  >
                                    {server.github_repo}
                                    <ExternalLink className="h-3 w-3" />
                                  </a>
                                </TableCell>
                                <TableCell>
                                  <Badge variant="outline">{server.github_branch}</Badge>
                                </TableCell>
                                <TableCell className="text-right space-x-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => pushMutation.mutate(server.id)}
                                    disabled={pushMutation.isPending}
                                    className="gap-1"
                                    title="Push configuration to GitHub"
                                  >
                                    {pushMutation.isPending ? (
                                      <Loader2 className="h-3 w-3 animate-spin" />
                                    ) : (
                                      <ArrowRight className="h-3 w-3" />
                                    )}
                                    Push
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => pullMutation.mutate(server.id)}
                                    disabled={pullMutation.isPending}
                                    className="gap-1"
                                    title="Pull configuration from GitHub"
                                  >
                                    {pullMutation.isPending ? (
                                      <Loader2 className="h-3 w-3 animate-spin" />
                                    ) : (
                                      <Rocket className="h-3 w-3" />
                                    )}
                                    Pull
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => unlinkRepoMutation.mutate(server.id)}
                                    disabled={unlinkRepoMutation.isPending}
                                    className="gap-1"
                                  >
                                    {unlinkRepoMutation.isPending ? (
                                      <Loader2 className="h-3 w-3 animate-spin" />
                                    ) : (
                                      <Unlink className="h-3 w-3" />
                                    )}
                                    Unlink
                                  </Button>
                                </TableCell>
                              </TableRow>
                              {expandedServer === server.id && (
                                <TableRow>
                                  <TableCell colSpan={4} className="bg-muted/20 p-4">
                                    {(isLoadingRepoFiles || isLoadingServerFiles) ? (
                                      <div className="flex items-center justify-center py-4">
                                        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                      </div>
                                    ) : (
                                      <div className="grid grid-cols-2 gap-4">
                                        {/* Server Files */}
                                        <div className="space-y-2">
                                          <div className="flex items-center justify-between mb-3">
                                            <div>
                                              <h4 className="font-medium flex items-center gap-2">
                                                <FileCode className="h-4 w-4" />
                                                Server Files
                                              </h4>
                                              <div className="flex flex-col gap-2 mt-1">
                                                <div className="flex items-center gap-2">
                                                  {currentPath && (
                                                    <Button
                                                      variant="ghost"
                                                      size="sm"
                                                      onClick={() => {
                                                        const parts = currentPath.split('/').filter(Boolean)
                                                        parts.pop()
                                                        setCurrentPath(parts.join('/'))
                                                      }}
                                                      className="h-6 px-2"
                                                    >
                                                      <ArrowLeft className="h-3 w-3 mr-1" />
                                                      Back
                                                    </Button>
                                                  )}
                                                  {currentPath && (
                                                    <Button
                                                      variant="ghost"
                                                      size="sm"
                                                      onClick={() => setCurrentPath("")}
                                                      className="h-6 px-2"
                                                    >
                                                      <Home className="h-3 w-3 mr-1" />
                                                      Root
                                                    </Button>
                                                  )}
                                                  <p className="text-sm text-muted-foreground">
                                                    {currentPath ? `/${currentPath}` : '/'} • {serverFiles?.total_files || 0} files
                                                  </p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                  <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={selectAllRecommended}
                                                    className="h-6 px-2 text-xs"
                                                  >
                                                    <CheckSquare className="h-3 w-3 mr-1" />
                                                    Recommended ({serverFiles?.recommended_files || 0})
                                                  </Button>
                                                  <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={selectAll}
                                                    className="h-6 px-2 text-xs"
                                                  >
                                                    All
                                                  </Button>
                                                  <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={deselectAll}
                                                    className="h-6 px-2 text-xs"
                                                  >
                                                    None
                                                  </Button>
                                                  <p className="text-xs text-muted-foreground">
                                                    {selectedFiles.size} selected
                                                  </p>
                                                </div>
                                              </div>
                                            </div>
                                          </div>
                                          <div className="border rounded-lg overflow-hidden max-h-96 overflow-y-auto">
                                            <Table>
                                              <TableHeader className="sticky top-0 bg-background">
                                                <TableRow>
                                                  <TableHead className="w-10"></TableHead>
                                                  <TableHead>Name</TableHead>
                                                  <TableHead className="text-right">Size</TableHead>
                                                </TableRow>
                                              </TableHeader>
                                              <TableBody>
                                                {serverFiles?.files?.length > 0 ? (
                                                  serverFiles.files.map((file: any) => (
                                                    <TableRow
                                                      key={file.path}
                                                      className={`hover:bg-muted/50 ${!file.recommended ? 'opacity-60' : ''}`}
                                                    >
                                                      <TableCell onClick={(e) => e.stopPropagation()}>
                                                        <Checkbox
                                                          checked={selectedFiles.has(file.path)}
                                                          onCheckedChange={() => toggleFileSelection(file.path)}
                                                        />
                                                      </TableCell>
                                                      <TableCell
                                                        className="font-mono text-sm cursor-pointer"
                                                        onClick={() => {
                                                          if (file.is_dir) {
                                                            const newPath = currentPath ? `${currentPath}/${file.name}` : file.name
                                                            setCurrentPath(newPath)
                                                          } else {
                                                            router.push(`/servers/${server.id}/config`)
                                                            toast.info(`Opening File Manager for ${server.name}`)
                                                          }
                                                        }}
                                                      >
                                                        <div className="flex items-center gap-2">
                                                          {file.is_dir ? (
                                                            <Folder className="h-4 w-4 text-blue-500" />
                                                          ) : (
                                                            <FileCode className="h-4 w-4 text-green-500" />
                                                          )}
                                                          <span className="hover:underline">
                                                            {file.name}
                                                          </span>
                                                          {file.warning && (
                                                            <AlertTriangle className="h-3 w-3 text-orange-500" title={file.warning} />
                                                          )}
                                                        </div>
                                                      </TableCell>
                                                      <TableCell className="text-right text-sm text-muted-foreground">
                                                        {!file.is_dir && file.size > 0
                                                          ? `${(file.size / 1024).toFixed(1)} KB`
                                                          : "-"}
                                                      </TableCell>
                                                    </TableRow>
                                                  ))
                                                ) : (
                                                  <TableRow>
                                                    <TableCell colSpan={3} className="text-center py-4 text-muted-foreground">
                                                      No files found
                                                    </TableCell>
                                                  </TableRow>
                                                )}
                                              </TableBody>
                                            </Table>
                                          </div>
                                        </div>

                                        {/* GitHub Repository Files */}
                                        <div className="space-y-2">
                                          <div className="flex items-center justify-between mb-3">
                                            <div>
                                              <h4 className="font-medium flex items-center gap-2">
                                                <Github className="h-4 w-4" />
                                                GitHub Repository
                                              </h4>
                                              <p className="text-sm text-muted-foreground">
                                                {repoFiles?.total_files || 0} files • Commit: {repoFiles?.commit_sha || "N/A"}
                                              </p>
                                            </div>
                                          </div>
                                          <div className="border rounded-lg overflow-hidden max-h-96 overflow-y-auto">
                                            <Table>
                                              <TableHeader className="sticky top-0 bg-background">
                                                <TableRow>
                                                  <TableHead>Name</TableHead>
                                                  <TableHead className="text-right">Size</TableHead>
                                                </TableRow>
                                              </TableHeader>
                                              <TableBody>
                                                {repoFiles?.files?.length > 0 ? (
                                                  repoFiles.files.map((file: any) => (
                                                    <TableRow key={file.path}>
                                                      <TableCell className="font-mono text-sm">
                                                        <div className="flex items-center gap-2">
                                                          {file.type === "dir" ? (
                                                            <Folder className="h-4 w-4 text-blue-500" />
                                                          ) : (
                                                            <FileCode className="h-4 w-4 text-purple-500" />
                                                          )}
                                                          {file.download_url ? (
                                                            <a
                                                              href={file.download_url}
                                                              target="_blank"
                                                              rel="noopener noreferrer"
                                                              className="hover:underline text-primary"
                                                            >
                                                              {file.name}
                                                            </a>
                                                          ) : (
                                                            <span>{file.name}</span>
                                                          )}
                                                        </div>
                                                      </TableCell>
                                                      <TableCell className="text-right text-sm text-muted-foreground">
                                                        {file.type === "file" && file.size > 0
                                                          ? `${(file.size / 1024).toFixed(1)} KB`
                                                          : "-"}
                                                      </TableCell>
                                                    </TableRow>
                                                  ))
                                                ) : (
                                                  <TableRow>
                                                    <TableCell colSpan={2} className="text-center py-4 text-muted-foreground">
                                                      No files in repository
                                                    </TableCell>
                                                  </TableRow>
                                                )}
                                              </TableBody>
                                            </Table>
                                          </div>
                                        </div>
                                      </div>
                                    )}
                                  </TableCell>
                                </TableRow>
                              )}
                            </>
                          ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>

              {/* Webhook Configuration */}
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <RefreshCw className="h-5 w-5" />
                    <CardTitle>Webhook Configuration</CardTitle>
                  </div>
                  <CardDescription>
                    Configure webhooks to enable automatic deployments on push
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {webhookConfig?.enabled ? (
                    <>
                      <div className="space-y-2">
                        <Label>Webhook URL</Label>
                        <div className="flex gap-2">
                          <Input value={webhookConfig.url} readOnly />
                          <Button variant="outline" size="icon" onClick={copyWebhookUrl}>
                            {copiedWebhook ? (
                              <Check className="h-4 w-4" />
                            ) : (
                              <Copy className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Add this URL to your repository's webhook settings
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label>Events</Label>
                        <div className="flex gap-2">
                          {webhookConfig.events.map((event) => (
                            <Badge key={event} variant="secondary">
                              {event}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <Alert>
                        <CheckCircle2 className="h-4 w-4" />
                        <AlertDescription>
                          Webhooks are configured. Pushing to linked branches will trigger automatic
                          deployments.
                        </AlertDescription>
                      </Alert>
                    </>
                  ) : (
                    <div className="space-y-4">
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          Webhooks are not configured. Set up webhooks to enable automatic deployments.
                        </AlertDescription>
                      </Alert>

                      <Dialog open={webhookDialogOpen} onOpenChange={setWebhookDialogOpen}>
                        <DialogTrigger asChild>
                          <Button className="gap-2">
                            <RefreshCw className="h-4 w-4" />
                            Configure Webhook
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Configure Webhook</DialogTitle>
                            <DialogDescription>
                              Select a repository to configure webhooks for automatic deployments
                            </DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4">
                            <div className="space-y-2">
                              <Label>Repository</Label>
                              <Select value={selectedRepo} onValueChange={setSelectedRepo}>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select repository" />
                                </SelectTrigger>
                                <SelectContent>
                                  {repositories?.map((repo) => (
                                    <SelectItem key={repo.id} value={repo.full_name}>
                                      {repo.full_name}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                            <Button
                              onClick={() => {
                                if (selectedRepo) {
                                  webhookMutation.mutate(selectedRepo)
                                }
                              }}
                              disabled={!selectedRepo || webhookMutation.isPending}
                              className="w-full gap-2"
                            >
                              {webhookMutation.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <RefreshCw className="h-4 w-4" />
                              )}
                              Create Webhook
                            </Button>
                          </div>
                        </DialogContent>
                      </Dialog>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                <CardTitle>GitHub Configuration</CardTitle>
              </div>
              <CardDescription>
                Configure GitHub OAuth credentials and API tokens. These values will be saved to your environment configuration.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <Alert>
                <Shield className="h-4 w-4" />
                <AlertTitle>Security Notice</AlertTitle>
                <AlertDescription>
                  These credentials will be stored securely and encrypted. Never share your tokens publicly.
                  After saving, you'll need to restart the Docker containers to apply changes.
                </AlertDescription>
              </Alert>

              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="clientId" className="flex items-center gap-2">
                      <Key className="h-4 w-4" />
                      GitHub Client ID
                    </Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(githubConfig.clientId, "Client ID")}
                      disabled={!githubConfig.clientId}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                  <Input
                    id="clientId"
                    placeholder="Iv1.xxxxxxxxxxxxxxxx"
                    value={githubConfig.clientId}
                    onChange={(e) => setGithubConfig({ ...githubConfig, clientId: e.target.value })}
                  />
                  <p className="text-xs text-muted-foreground">
                    Format: Iv1.xxxxxxxxxxxxxxxx (from GitHub OAuth App)
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="clientSecret" className="flex items-center gap-2">
                      <Lock className="h-4 w-4" />
                      GitHub Client Secret
                    </Label>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowClientSecret(!showClientSecret)}
                      >
                        {showClientSecret ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(githubConfig.clientSecret, "Client Secret")}
                        disabled={!githubConfig.clientSecret}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  <Input
                    id="clientSecret"
                    type={showClientSecret ? "text" : "password"}
                    placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    value={githubConfig.clientSecret}
                    onChange={(e) => setGithubConfig({ ...githubConfig, clientSecret: e.target.value })}
                  />
                  <p className="text-xs text-muted-foreground">
                    40 characters (shown only once when creating OAuth App)
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="token" className="flex items-center gap-2">
                      <Key className="h-4 w-4" />
                      Personal Access Token
                    </Label>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowToken(!showToken)}
                      >
                        {showToken ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(githubConfig.token, "Personal Access Token")}
                        disabled={!githubConfig.token}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  <Input
                    id="token"
                    type={showToken ? "text" : "password"}
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    value={githubConfig.token}
                    onChange={(e) => setGithubConfig({ ...githubConfig, token: e.target.value })}
                  />
                  <p className="text-xs text-muted-foreground">
                    Format: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (40 chars)
                    <br />
                    Required scopes: repo, read:user, admin:repo_hook
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="webhookSecret" className="flex items-center gap-2">
                      <Shield className="h-4 w-4" />
                      Webhook Secret
                    </Label>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={generateWebhookSecret}
                      >
                        Generate
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(githubConfig.webhookSecret, "Webhook Secret")}
                        disabled={!githubConfig.webhookSecret}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  <Input
                    id="webhookSecret"
                    placeholder="random_secure_string_min_32_chars"
                    value={githubConfig.webhookSecret}
                    onChange={(e) => setGithubConfig({ ...githubConfig, webhookSecret: e.target.value })}
                  />
                  <p className="text-xs text-muted-foreground">
                    Minimum 32 characters (use Generate button for secure random string)
                  </p>
                </div>

                <div className="pt-4 border-t">
                  <Button
                    onClick={() => saveConfigMutation.mutate()}
                    disabled={saveConfigMutation.isPending || !githubConfig.clientId || !githubConfig.clientSecret || !githubConfig.token}
                    className="w-full gap-2"
                  >
                    {saveConfigMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    Save Configuration
                  </Button>
                </div>

                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>After saving</AlertTitle>
                  <AlertDescription>
                    You'll need to restart Docker containers for changes to take effect:
                    <code className="block mt-2 p-2 bg-muted rounded text-xs">
                      docker-compose restart
                    </code>
                  </AlertDescription>
                </Alert>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Setup Guide Tab */}
        <TabsContent value="guide" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                <CardTitle>GitHub Integration Setup Guide</CardTitle>
              </div>
              <CardDescription>
                Follow these steps to configure GitHub integration for automated deployments
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="step1">
                  <AccordionTrigger className="text-base font-semibold">
                    <div className="flex items-center gap-2">
                      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">
                        1
                      </div>
                      Create GitHub OAuth App
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <ol className="space-y-3 list-decimal list-inside text-sm">
                      <li>
                        Go to{" "}
                        <a
                          href="https://github.com/settings/developers"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline inline-flex items-center gap-1"
                        >
                          GitHub Developer Settings
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </li>
                      <li>Click "OAuth Apps" → "New OAuth App"</li>
                      <li className="space-y-2">
                        <div>Fill in the form with these values:</div>
                        <div className="ml-6 space-y-1 text-xs bg-muted p-3 rounded">
                          <div><strong>Application name:</strong> HA Config Manager</div>
                          <div><strong>Homepage URL:</strong> http://localhost:3000</div>
                          <div><strong>Authorization callback URL:</strong> http://localhost:3000/api/auth/github/callback</div>
                        </div>
                      </li>
                      <li>Click "Register application"</li>
                      <li>
                        <strong>Copy the Client ID</strong> (format: Iv1.xxxxxxxxxxxxxxxx)
                        <ArrowRight className="h-3 w-3 inline mx-1" />
                        Paste it in the Settings tab
                      </li>
                      <li>Click "Generate a new client secret"</li>
                      <li>
                        <strong>Copy the Client Secret immediately</strong> (shown only once!)
                        <ArrowRight className="h-3 w-3 inline mx-1" />
                        Paste it in the Settings tab
                      </li>
                    </ol>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="step2">
                  <AccordionTrigger className="text-base font-semibold">
                    <div className="flex items-center gap-2">
                      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">
                        2
                      </div>
                      Create Personal Access Token
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <ol className="space-y-3 list-decimal list-inside text-sm">
                      <li>
                        Go to{" "}
                        <a
                          href="https://github.com/settings/tokens"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline inline-flex items-center gap-1"
                        >
                          GitHub Tokens
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </li>
                      <li>Click "Generate new token" → "Generate new token (classic)"</li>
                      <li className="space-y-2">
                        <div>Configure the token:</div>
                        <div className="ml-6 space-y-1 text-xs bg-muted p-3 rounded">
                          <div><strong>Note:</strong> HA Config Manager API</div>
                          <div><strong>Expiration:</strong> No expiration (or 90 days)</div>
                          <div className="pt-2"><strong>Select scopes:</strong></div>
                          <div className="ml-4 space-y-1">
                            <div>✅ <strong>repo</strong> (Full control of private repositories)</div>
                            <div className="ml-6 text-muted-foreground">
                              ✓ repo:status, repo_deployment, public_repo, repo:invite
                            </div>
                            <div>✅ <strong>read:user</strong> (Read ALL user profile data)</div>
                            <div>✅ <strong>admin:repo_hook</strong> (Full control of repository hooks)</div>
                            <div className="ml-6 text-muted-foreground">
                              ✓ write:repo_hook, read:repo_hook
                            </div>
                          </div>
                        </div>
                      </li>
                      <li>Click "Generate token"</li>
                      <li>
                        <strong>Copy the token immediately</strong> (format: ghp_xxxxxxxxxxxxxxxxxxxx)
                        <ArrowRight className="h-3 w-3 inline mx-1" />
                        Paste it in the Settings tab
                      </li>
                    </ol>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="step3">
                  <AccordionTrigger className="text-base font-semibold">
                    <div className="flex items-center gap-2">
                      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">
                        3
                      </div>
                      Generate Webhook Secret
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <div className="space-y-3 text-sm">
                      <p>A webhook secret is used to verify that webhook requests are actually from GitHub.</p>
                      <div className="space-y-2">
                        <p className="font-medium">Option 1: Use the Generate button (Recommended)</p>
                        <p className="text-muted-foreground ml-4">
                          Go to the Settings tab and click "Generate" next to Webhook Secret field.
                          This will create a secure random 32-character string.
                        </p>
                      </div>
                      <div className="space-y-2">
                        <p className="font-medium">Option 2: Generate manually</p>
                        <div className="ml-4 space-y-2">
                          <p className="text-muted-foreground">Windows PowerShell:</p>
                          <code className="block p-2 bg-muted rounded text-xs">
                            {`-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})`}
                          </code>
                          <p className="text-muted-foreground">Linux/Mac:</p>
                          <code className="block p-2 bg-muted rounded text-xs">
                            openssl rand -hex 32
                          </code>
                        </div>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="step4">
                  <AccordionTrigger className="text-base font-semibold">
                    <div className="flex items-center gap-2">
                      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">
                        4
                      </div>
                      Save Configuration & Restart
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <ol className="space-y-3 list-decimal list-inside text-sm">
                      <li>Go to the <strong>Settings</strong> tab</li>
                      <li>Paste all values you copied:
                        <ul className="ml-6 mt-1 space-y-1 text-xs list-disc">
                          <li>GitHub Client ID</li>
                          <li>GitHub Client Secret</li>
                          <li>Personal Access Token</li>
                          <li>Webhook Secret</li>
                        </ul>
                      </li>
                      <li>Click <strong>"Save Configuration"</strong></li>
                      <li>Open terminal and restart Docker containers:
                        <code className="block mt-2 p-2 bg-muted rounded text-xs">
                          docker-compose restart
                        </code>
                      </li>
                      <li>Wait 10-15 seconds for containers to restart</li>
                      <li>Refresh this page</li>
                    </ol>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="step5">
                  <AccordionTrigger className="text-base font-semibold">
                    <div className="flex items-center gap-2">
                      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">
                        5
                      </div>
                      Connect & Start Using
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-3 pt-4">
                    <ol className="space-y-3 list-decimal list-inside text-sm">
                      <li>Go to the <strong>Overview</strong> tab</li>
                      <li>Click "Connect GitHub" button</li>
                      <li>Authorize the application on GitHub</li>
                      <li>You'll be redirected back to the platform</li>
                      <li>You should see "Connected as [your_username]"</li>
                      <li>
                        <strong>Link a repository:</strong>
                        <ul className="ml-6 mt-1 space-y-1 text-xs list-disc">
                          <li>Select a server from dropdown</li>
                          <li>Select a repository</li>
                          <li>Select a branch (e.g., main)</li>
                          <li>Click "Link Repository"</li>
                        </ul>
                      </li>
                      <li>
                        <strong>Deploy manually:</strong> Click "Deploy" button in the Linked Repositories table
                      </li>
                      <li>
                        <strong>Setup auto-deploy:</strong> Configure webhook to trigger deployments automatically on git push
                      </li>
                    </ol>
                    <Alert>
                      <CheckCircle2 className="h-4 w-4" />
                      <AlertTitle>Success!</AlertTitle>
                      <AlertDescription>
                        You now have a fully automated deployment pipeline from GitHub to your Home Assistant servers!
                      </AlertDescription>
                    </Alert>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Troubleshooting</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <p className="font-medium">Issue: "client_id is undefined" when connecting</p>
                <p className="text-muted-foreground ml-4">
                  ✅ Make sure you saved the configuration and restarted containers
                </p>
              </div>
              <div>
                <p className="font-medium">Issue: "GitHub not connected" error</p>
                <p className="text-muted-foreground ml-4">
                  ✅ Check that Personal Access Token has correct scopes (repo, read:user, admin:repo_hook)
                </p>
              </div>
              <div>
                <p className="font-medium">Issue: "Failed to create webhook"</p>
                <p className="text-muted-foreground ml-4">
                  ✅ Make sure you're the owner of the repository
                  <br />
                  ✅ Check that token has admin:repo_hook scope
                </p>
              </div>
              <div>
                <p className="font-medium">Issue: Deployment fails</p>
                <p className="text-muted-foreground ml-4">
                  ✅ Check SSH credentials for the server
                  <br />
                  ✅ View deployment logs in Deployments page
                  <br />
                  ✅ Verify repository has valid YAML configuration files
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
