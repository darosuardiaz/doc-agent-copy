"use client"

import { formatDistanceToNow } from "date-fns"
import { User, Bot } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { SourcesDisplay } from "@/components/ui/sources-display"
import type { ChatMessage } from "@/lib/stores/chat-store"
import { cn } from "@/lib/utils"

interface ChatMessageProps {
  message: ChatMessage
}

export function ChatMessageComponent({ message }: ChatMessageProps) {
  const isUser = message.role === "user"

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600",
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className={cn("flex-1 max-w-3xl", isUser && "flex justify-end")}>
        <Card className={cn("max-w-full", isUser ? "bg-blue-600 text-white" : "bg-background")}>
          <CardContent className="p-4">
            <div className="prose prose-sm max-w-none">
              <p className={cn("mb-0", isUser && "text-white")}>{message.content}</p>
            </div>

            <SourcesDisplay sources={message.sources_used || []} showBorder={true} />

            <div className={cn("text-xs mt-2 opacity-70", isUser ? "text-blue-100" : "text-muted-foreground")}>
              {formatDistanceToNow(new Date(message.created_at), { addSuffix: true })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
