"use client"

import { formatDistanceToNow } from "date-fns"
import { User, Bot, FileText } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
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

            {message.sources_used && message.sources_used.length > 0 && (
              <div className="mt-4 pt-3 border-t border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">Sources Used</span>
                </div>
                <div className="space-y-2">
                  {message.sources_used.map((source, index) => (
                    <div key={index} className="relative group inline-block">
                      <Badge variant="outline" className="text-xs cursor-pointer">
                        Page {source.page}
                      </Badge>

                      <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-10 w-80 bg-white border border-gray-200 rounded-lg shadow-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <Badge variant="outline" className="text-xs">
                            Page {source.page}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            Score: {Math.round(source.relevance_score * 100)}%
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-700">{source.content}</p>
                        <div className="absolute top-full left-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-200"></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className={cn("text-xs mt-2 opacity-70", isUser ? "text-blue-100" : "text-muted-foreground")}>
              {formatDistanceToNow(new Date(message.created_at), { addSuffix: true })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
