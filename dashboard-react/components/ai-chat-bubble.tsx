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
import {
  Loader2,
  Send,
  Bot,
  User,
  X,
  Minimize2,
  Maximize2,
  Sparkles,
  Server,
  Rocket,
  Database,
} from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface UserContext {
  total_servers: number
  total_deployments: number
  total_backups: number
}

export function AIChatBubble() {
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [conversationId, setConversationId] = useState<number | null>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Get user context
  const { data: userContext } = useQuery<UserContext>({
    queryKey: ["ai-context"],
    queryFn: async () => {
      const response = await apiClient.get("/ai/user-context")
      return response.data
    },
    enabled: isOpen,
  })

  // Create conversation when opening chat
  const createConversationMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post("/ai/conversations", {
        title: "Chat Bubble Conversation",
        context_type: "general",
        model: "deepseek-chat",
        temperature: 0.7,
        max_tokens: 2000,
      })
      return response.data
    },
    onSuccess: (data) => {
      setConversationId(data.id)
    },
  })

  // Chat mutation
  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      if (!conversationId) {
        throw new Error("No conversation ID")
      }
      const response = await apiClient.post(`/ai/conversations/${conversationId}/chat`, {
        message,
        include_context: true,
      })
      return response.data
    },
    onSuccess: (data) => {
      // Add assistant message
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: data.message.content,
          timestamp: new Date(),
        },
      ])
    },
    onError: () => {
      toast.error("Failed to get AI response")
    },
  })

  const handleOpen = () => {
    setIsOpen(true)
    if (!conversationId) {
      createConversationMutation.mutate()
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !conversationId) return

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

  if (!isOpen) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <Button
          size="lg"
          className="h-14 w-14 rounded-full shadow-lg hover:shadow-xl transition-all bg-primary hover:scale-110"
          onClick={handleOpen}
        >
          <Sparkles className="h-6 w-6" />
        </Button>
        <Badge className="absolute -top-1 -right-1 bg-red-500">AI</Badge>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "fixed bottom-6 right-6 z-50 transition-all",
        isMinimized ? "w-80 h-16" : "w-96 h-[600px]"
      )}
    >
      <Card className="h-full flex flex-col shadow-2xl border-2 border-primary/20">
        <CardHeader className="pb-3 border-b bg-gradient-to-r from-primary/10 to-primary/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center">
                <Bot className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  AI Assistant
                  <Badge variant="secondary" className="text-xs">
                    DeepSeek
                  </Badge>
                </CardTitle>
                {userContext && !isMinimized && (
                  <CardDescription className="text-xs">
                    {userContext.total_servers} servers • {userContext.total_deployments} deployments
                  </CardDescription>
                )}
              </div>
            </div>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setIsMinimized(!isMinimized)}
              >
                {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => {
                  setIsOpen(false)
                  setMessages([])
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>

        {!isMinimized && (
          <>
            <CardContent className="flex-1 p-0">
              <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
                {messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    <div className="text-center space-y-3">
                      <Bot className="h-12 w-12 mx-auto opacity-50" />
                      <div>
                        <p className="text-sm font-medium">Hi! I'm your AI assistant</p>
                        <p className="text-xs mt-1">I know everything about your infrastructure</p>
                      </div>
                      {userContext && (
                        <div className="flex gap-2 justify-center mt-3">
                          <Badge variant="outline" className="text-xs">
                            <Server className="h-3 w-3 mr-1" />
                            {userContext.total_servers}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            <Rocket className="h-3 w-3 mr-1" />
                            {userContext.total_deployments}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            <Database className="h-3 w-3 mr-1" />
                            {userContext.total_backups}
                          </Badge>
                        </div>
                      )}
                      <div className="grid grid-cols-1 gap-1 max-w-xs mx-auto mt-3">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setInput("Show me my servers")}
                          className="text-xs justify-start h-8"
                        >
                          Show me my servers
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setInput("What's my infrastructure status?")}
                          className="text-xs justify-start h-8"
                        >
                          Infrastructure status?
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={cn("flex gap-2", message.role === "user" ? "justify-end" : "justify-start")}
                      >
                        {message.role === "assistant" && (
                          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center mt-1">
                            <Bot className="h-4 w-4 text-primary" />
                          </div>
                        )}
                        <div
                          className={cn(
                            "rounded-lg px-3 py-2 max-w-[80%] text-sm",
                            message.role === "user"
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted text-foreground"
                          )}
                        >
                          <p className="whitespace-pre-wrap">{message.content}</p>
                          <p className="text-xs opacity-70 mt-1">
                            {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </p>
                        </div>
                        {message.role === "user" && (
                          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary flex items-center justify-center mt-1">
                            <User className="h-4 w-4 text-primary-foreground" />
                          </div>
                        )}
                      </div>
                    ))}
                    {chatMutation.isPending && (
                      <div className="flex gap-2">
                        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
                          <Bot className="h-4 w-4 text-primary" />
                        </div>
                        <div className="rounded-lg px-3 py-2 bg-muted">
                          <Loader2 className="h-4 w-4 animate-spin" />
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </ScrollArea>
            </CardContent>

            <form onSubmit={handleSubmit} className="p-3 border-t bg-background">
              <div className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask me anything..."
                  disabled={chatMutation.isPending || !conversationId}
                  className="flex-1 text-sm"
                />
                <Button
                  type="submit"
                  size="sm"
                  disabled={chatMutation.isPending || !input.trim() || !conversationId}
                >
                  {chatMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
              </div>
            </form>
          </>
        )}
      </Card>
    </div>
  )
}
