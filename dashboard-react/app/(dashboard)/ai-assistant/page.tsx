"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Loader2, Send, Bot, User, Server, Rocket, Database, RefreshCw, Sparkles, MessageSquare, Plus } from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  action?: string
  timestamp: Date
}

interface UserContext {
  total_servers: number
  total_deployments: number
  total_backups: number
}

interface Conversation {
  id: number
  title: string
  created_at: string
  last_message_at: string | null
  message_count: number
  is_active: boolean
}

interface AIMessageResponse {
  id: number
  role: string
  content: string
  created_at: string
}

export default function AIAssistantPage() {
  const queryClient = useQueryClient()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [conversationId, setConversationId] = useState<number | null>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Fetch conversations list
  const { data: conversations, isLoading: conversationsLoading } = useQuery<Conversation[]>({
    queryKey: ["ai-conversations"],
    queryFn: async () => {
      const response = await apiClient.get("/ai/conversations")
      return response.data
    },
  })

  // Fetch messages for selected conversation
  const { data: conversationMessages } = useQuery<AIMessageResponse[]>({
    queryKey: ["ai-messages", conversationId],
    enabled: !!conversationId,
    queryFn: async () => {
      const response = await apiClient.get(`/ai/conversations/${conversationId}/messages`)
      return response.data
    },
  })

  // Load messages when conversation changes
  useEffect(() => {
    if (conversationMessages) {
      const formattedMessages: Message[] = conversationMessages.map((msg) => ({
        id: msg.id.toString(),
        role: msg.role as "user" | "assistant",
        content: msg.content,
        timestamp: new Date(msg.created_at),
      }))
      setMessages(formattedMessages)
    }
  }, [conversationMessages])

  // Create new conversation
  const createConversationMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post("/ai/conversations", {
        title: "New AI Chat",
        context_type: "general",
      })
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["ai-conversations"] })
      setConversationId(data.id)
      setMessages([])
      toast.success("New conversation created")
    },
    onError: () => {
      toast.error("Failed to create conversation")
    },
  })

  // Auto-select first conversation or create new one on mount
  useEffect(() => {
    if (conversations && conversations.length > 0 && !conversationId) {
      setConversationId(conversations[0].id)
    } else if (conversations && conversations.length === 0 && !conversationId) {
      createConversationMutation.mutate()
    }
  }, [conversations, conversationId])

  // Get user context
  const { data: userContext, refetch: refetchContext } = useQuery<UserContext>({
    queryKey: ["ai-context"],
    queryFn: async () => {
      const response = await apiClient.get("/ai/user-context")
      return response.data
    },
  })

  const refreshContextMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post("/ai/context/refresh")
      return response.data
    },
    onSuccess: () => {
      refetchContext()
      toast.success("Context refreshed")
    },
  })

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      if (!conversationId) {
        throw new Error("No conversation initialized")
      }
      const response = await apiClient.post(`/ai/conversations/${conversationId}/chat`, {
        message,
        include_context: true,
      })
      return response.data
    },
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: data.message.id,
          role: "assistant",
          content: data.message.content,
          action: data.executed_actions?.[0],
          timestamp: new Date(data.message.created_at),
        },
      ])

      // Invalidate queries to refresh conversation list
      queryClient.invalidateQueries({ queryKey: ["ai-conversations"] })
      queryClient.invalidateQueries({ queryKey: ["ai-messages", conversationId] })

      if (data.executed_actions?.length > 0) {
        toast.success(`Action executed: ${data.executed_actions[0]}`)
      }
      if (data.suggested_actions?.length > 0) {
        const modCount = data.suggested_actions.length
        toast.success(
          `AI created ${modCount} file modification${modCount > 1 ? "s" : ""}. Review in AI Modifications.`,
          {
            duration: 10000,
            action: {
              label: "Review",
              onClick: () => (window.location.href = "/ai-modifications"),
            },
          }
        )
      }
    },
    onError: (error: any) => {
      console.error("Chat error:", error)
      toast.error("Failed to get AI response")
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    if (!conversationId) {
      toast.error("AI chat is still initializing, please wait...")
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    chatMutation.mutate(input)
    setInput("")
  }

  return (
    <div className="flex gap-4 h-[calc(100vh-8rem)]">
      {/* Conversations Sidebar */}
      <Card className="w-80 flex-shrink-0">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Conversations</CardTitle>
            <Button
              size="sm"
              variant="outline"
              onClick={() => createConversationMutation.mutate()}
              disabled={createConversationMutation.isPending}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[calc(100vh-16rem)]">
            {conversationsLoading ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : conversations && conversations.length > 0 ? (
              <div className="space-y-1 p-2">
                {conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => setConversationId(conv.id)}
                    className={cn(
                      "w-full text-left px-3 py-2 rounded-lg transition-colors",
                      "hover:bg-accent",
                      conversationId === conv.id && "bg-accent"
                    )}
                  >
                    <div className="flex items-start gap-2">
                      <MessageSquare className="h-4 w-4 mt-1 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{conv.title}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {conv.message_count} messages
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(conv.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-muted-foreground">
                <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No conversations yet</p>
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">
                <Sparkles className="h-8 w-8 text-primary" />
                AI Assistant
              </h1>
              <p className="text-muted-foreground">Context-aware AI that knows your entire infrastructure</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refreshContextMutation.mutate()}
              disabled={refreshContextMutation.isPending}
            >
              {refreshContextMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              <span className="ml-2">Refresh Context</span>
            </Button>
          </div>

        {/* Context Summary */}
        {userContext && (
          <div className="grid grid-cols-3 gap-4 mt-4">
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2">
                  <Server className="h-5 w-5 text-blue-500" />
                  <div>
                    <p className="text-2xl font-bold">{userContext.total_servers}</p>
                    <p className="text-xs text-muted-foreground">Servers</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2">
                  <Rocket className="h-5 w-5 text-green-500" />
                  <div>
                    <p className="text-2xl font-bold">{userContext.total_deployments}</p>
                    <p className="text-xs text-muted-foreground">Deployments</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-purple-500" />
                  <div>
                    <p className="text-2xl font-bold">{userContext.total_backups}</p>
                    <p className="text-xs text-muted-foreground">Backups</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      <Card className="flex-1 flex flex-col">
        <CardHeader className="border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              <div>
                <CardTitle>Context-Aware Chat</CardTitle>
                <CardDescription>AI knows about your {userContext?.total_servers || 0} servers, {userContext?.total_deployments || 0} deployments, and more</CardDescription>
              </div>
            </div>
            {conversationId && <Badge variant="secondary">Conversation: {conversationId}</Badge>}
          </div>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col p-0">
          <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <div className="text-center space-y-4">
                  <Bot className="h-16 w-16 mx-auto opacity-50" />
                  <div>
                    <p className="text-lg font-medium">Start a conversation with your AI assistant</p>
                    <p className="text-sm mt-2">I have full context about your infrastructure!</p>
                  </div>
                  <div className="grid grid-cols-2 gap-2 max-w-lg mx-auto mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setInput("Show me my servers")}
                      className="text-left justify-start"
                    >
                      Show me my servers
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setInput("List my deployments")}
                      className="text-left justify-start"
                    >
                      List my deployments
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setInput("How many servers do I have?")}
                      className="text-left justify-start"
                    >
                      How many servers do I have?
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setInput("Help me understand my infrastructure")}
                      className="text-left justify-start"
                    >
                      Explain my setup
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn("flex gap-3", message.role === "user" ? "justify-end" : "justify-start")}
                  >
                    {message.role === "assistant" && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <Bot className="h-4 w-4" />
                      </div>
                    )}
                    <div
                      className={cn(
                        "rounded-lg px-4 py-2 max-w-[80%]",
                        message.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground",
                      )}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      {message.action && (
                        <Badge variant="secondary" className="mt-2">
                          Action: {message.action}
                        </Badge>
                      )}
                      <p className="text-xs opacity-70 mt-1">
                        {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </p>
                    </div>
                    {message.role === "user" && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                        <User className="h-4 w-4 text-primary-foreground" />
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </ScrollArea>

          <form onSubmit={handleSubmit} className="p-4 border-t">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                disabled={chatMutation.isPending}
                className="flex-1"
              />
              <Button type="submit" disabled={chatMutation.isPending || !input.trim()}>
                {chatMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
      </div>
    </div>
  )
}
