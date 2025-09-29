"use client"

import { useEffect, useRef } from "react"
import { useChatStore, type ChatSession } from "@/lib/stores/chat-store"
import { ChatMessageComponent } from "./chat-message"
import { ChatInput } from "./chat-input"
import { Loader2 } from "lucide-react"

interface ChatInterfaceProps {
  session: ChatSession | null
  documentId?: string
}

export function ChatInterface({ session, documentId }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages, isTyping, error, fetchMessages, sendMessage } = useChatStore()

  useEffect(() => {
    if (session?.id) {
      fetchMessages(session.id)
    }
  }, [session?.id])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isTyping])

  const handleSendMessage = async (message: string) => {
    if (!documentId) return

    try {
      await sendMessage(message, documentId, true)
    } catch (error) {
      console.error("Failed to send message:", error)
    }
  }

  if (!session) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground">Select a document and create a chat session to get started</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Chat Header */}
      <div className="p-4 border-b bg-background">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold">{session.session_name}</h2>
            <p className="text-sm text-muted-foreground">
              {new Date(session.created_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
          <div className="flex items-center gap-2">{/* Settings button could go here */}</div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isTyping && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <p className="text-muted-foreground mb-4">
                Start a conversation about your document. Ask questions about financial data, request analysis, or
                explore key insights.
              </p>
              <div className="bg-blue-50 rounded-lg p-4">
                <p className="text-sm text-blue-700 font-medium mb-2">Try asking:</p>
                <ul className="text-sm text-blue-600 space-y-1">
                  <li>"What is the total revenue for this company?"</li>
                  <li>"Summarize the key financial metrics"</li>
                  <li>"What are the main investment highlights?"</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessageComponent key={message.id} message={message} />
        ))}

        {isTyping && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
              <Loader2 className="h-4 w-4 animate-spin text-gray-600" />
            </div>
            <div className="flex-1 max-w-3xl">
              <div className="bg-gray-100 rounded-lg p-4">
                <p className="text-sm text-gray-600">AI is thinking...</p>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border-t border-red-200">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Chat Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        disabled={isTyping || !documentId}
        placeholder="Type your message..."
      />
    </div>
  )
}
