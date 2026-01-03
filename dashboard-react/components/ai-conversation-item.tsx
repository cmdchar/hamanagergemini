"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { MessageSquare, Pin, Archive, Trash2, MoreVertical } from "lucide-react"
import { cn } from "@/lib/utils"

interface Conversation {
  id: number
  title: string
  created_at: string
  last_message_at: string | null
  message_count: number
  is_active: boolean
  is_pinned: boolean
  is_archived: boolean
}

interface ConversationItemProps {
  conversation: Conversation
  isSelected: boolean
  onClick: () => void
  onPin: (id: number, isPinned: boolean) => void
  onArchive: (id: number, isArchived: boolean) => void
  onDelete: (id: number) => void
}

export function ConversationItem({
  conversation: conv,
  isSelected,
  onClick,
  onPin,
  onArchive,
  onDelete,
}: ConversationItemProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "w-full text-left px-3 py-2 rounded-lg transition-colors group relative cursor-pointer",
        "hover:bg-accent",
        isSelected && "bg-accent border-2 border-primary"
      )}
    >
      <div className="flex items-start gap-2">
        <div className="flex items-center gap-1 flex-shrink-0">
          {conv.is_pinned && <Pin className="h-3 w-3 text-primary fill-primary" />}
          <MessageSquare className="h-4 w-4 mt-1" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate">{conv.title}</p>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline" className="text-xs">
              {conv.message_count} msg
            </Badge>
            <span className="text-xs text-muted-foreground">
              {conv.last_message_at
                ? new Date(conv.last_message_at).toLocaleDateString()
                : new Date(conv.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                onPin(conv.id, conv.is_pinned)
              }}
            >
              <Pin className="h-4 w-4 mr-2" />
              {conv.is_pinned ? "Unpin" : "Pin"}
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                onArchive(conv.id, conv.is_archived)
              }}
            >
              <Archive className="h-4 w-4 mr-2" />
              {conv.is_archived ? "Unarchive" : "Archive"}
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                if (confirm("Are you sure you want to delete this conversation?")) {
                  onDelete(conv.id)
                }
              }}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}
