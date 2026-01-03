"use client"

import { useState, useMemo } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { RefreshCw, FileText, ArrowLeft, Save, Folder, FolderOpen, ChevronRight, ChevronDown, Search } from "lucide-react"
import { toast } from "sonner"
import Link from "next/link"
import { useParams } from "next/navigation"

interface HaConfig {
  id: string
  path: string
  content: string
  updated_at: string
}

interface FileNode {
  name: string
  path: string
  type: 'file' | 'folder'
  config?: HaConfig
  children?: FileNode[]
}

// Build file tree from flat list of configs
function buildFileTree(configs: HaConfig[]): FileNode[] {
  const root: Record<string, FileNode> = {}

  configs.forEach(config => {
    const parts = config.path.replace(/^\/config\//, '').split('/')
    let current = root

    parts.forEach((part, index) => {
      const isFile = index === parts.length - 1
      const fullPath = parts.slice(0, index + 1).join('/')

      if (!current[part]) {
        current[part] = {
          name: part,
          path: `/config/${fullPath}`,
          type: isFile ? 'file' : 'folder',
          ...(isFile ? { config } : { children: {} })
        }
      }

      if (!isFile) {
        current = current[part].children as Record<string, FileNode>
      }
    })
  })

  // Convert to array and sort
  const sortNodes = (nodes: Record<string, FileNode>): FileNode[] => {
    return Object.values(nodes)
      .map(node => ({
        ...node,
        children: node.children ? sortNodes(node.children as Record<string, FileNode>) : undefined
      }))
      .sort((a, b) => {
        // Folders first, then alphabetically
        if (a.type !== b.type) return a.type === 'folder' ? -1 : 1
        return a.name.localeCompare(b.name)
      })
  }

  return sortNodes(root)
}

export default function ServerConfigPage() {
  const params = useParams()
  const serverId = params.id as string
  const [selectedConfig, setSelectedConfig] = useState<HaConfig | null>(null)
  const [editedContent, setEditedContent] = useState<string>("")
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState<string>("")
  const queryClient = useQueryClient()

  const { data: configs, isLoading } = useQuery<HaConfig[]>({
    queryKey: ["server-configs", serverId],
    queryFn: async () => {
      const response = await apiClient.get(`/ha-config/servers/${serverId}/configs`)
      return response.data
    },
  })

  const syncMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/ha-config/servers/${serverId}/sync-config`)
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
      const response = await apiClient.put(`/ha-config/servers/${serverId}/configs/${selectedConfig.id}`, {
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

  const toggleFolder = (path: string) => {
    setExpandedFolders(prev => {
      const next = new Set(prev)
      if (next.has(path)) {
        next.delete(path)
      } else {
        next.add(path)
      }
      return next
    })
  }

  // Build file tree and filter by search
  const fileTree = useMemo(() => {
    if (!configs) return []
    const tree = buildFileTree(configs)

    if (!searchQuery.trim()) return tree

    // Filter tree by search query
    const filterTree = (nodes: FileNode[]): FileNode[] => {
      return nodes.reduce<FileNode[]>((acc, node) => {
        if (node.type === 'file') {
          // Check if file matches search
          if (node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              node.path.toLowerCase().includes(searchQuery.toLowerCase())) {
            acc.push(node)
          }
        } else if (node.children) {
          // Recursively filter children
          const filteredChildren = filterTree(node.children)
          if (filteredChildren.length > 0) {
            acc.push({
              ...node,
              children: filteredChildren
            })
            // Auto-expand folders when searching
            expandedFolders.add(node.path)
          }
        }
        return acc
      }, [])
    }

    return filterTree(tree)
  }, [configs, searchQuery])

  // Recursive tree node component
  const TreeNode = ({ node, depth = 0 }: { node: FileNode; depth?: number }) => {
    const isExpanded = expandedFolders.has(node.path)
    const isSelected = selectedConfig?.id === node.config?.id

    if (node.type === 'file') {
      return (
        <Button
          variant={isSelected ? "secondary" : "ghost"}
          className="w-full justify-start font-mono text-xs h-7 px-2"
          style={{ paddingLeft: `${(depth + 1) * 12 + 8}px` }}
          onClick={() => node.config && handleSelectConfig(node.config)}
          title={node.path}
        >
          <FileText className="mr-2 h-3 w-3 shrink-0" />
          <span className="truncate">{node.name}</span>
        </Button>
      )
    }

    return (
      <div>
        <Button
          variant="ghost"
          className="w-full justify-start font-mono text-xs h-7 px-2"
          style={{ paddingLeft: `${depth * 12 + 8}px` }}
          onClick={() => toggleFolder(node.path)}
        >
          {isExpanded ? (
            <ChevronDown className="mr-1 h-3 w-3 shrink-0" />
          ) : (
            <ChevronRight className="mr-1 h-3 w-3 shrink-0" />
          )}
          {isExpanded ? (
            <FolderOpen className="mr-2 h-3 w-3 shrink-0" />
          ) : (
            <Folder className="mr-2 h-3 w-3 shrink-0" />
          )}
          <span className="truncate">{node.name}</span>
          {node.children && (
            <span className="ml-auto text-muted-foreground text-xs">
              {node.children.length}
            </span>
          )}
        </Button>
        {isExpanded && node.children && (
          <div>
            {node.children.map((child) => (
              <TreeNode key={child.path} node={child} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    )
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
          <CardHeader className="pb-3">
            <CardTitle className="text-lg mb-2">Files</CardTitle>
            <div className="relative">
              <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 h-8 text-sm"
              />
            </div>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden p-0">
            <ScrollArea className="h-full">
              <div className="space-y-0.5 p-2">
                {isLoading ? (
                  <p className="text-sm text-muted-foreground p-2">Loading...</p>
                ) : configs?.length === 0 ? (
                  <p className="text-sm text-muted-foreground p-2">No configs found. Click Sync.</p>
                ) : fileTree.length === 0 ? (
                  <p className="text-sm text-muted-foreground p-2">No files match your search.</p>
                ) : (
                  fileTree.map((node) => (
                    <TreeNode key={node.path} node={node} />
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
