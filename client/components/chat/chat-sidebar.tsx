"use client"

import { useEffect } from "react"
import { Plus, MessageSquare, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useChatStore, type ChatSession } from "@/lib/stores/chat-store"
import { useDocumentStore } from "@/lib/stores/document-store"
import { formatDistanceToNow } from "date-fns"
import { cn } from "@/lib/utils"

interface ChatSidebarProps {
  selectedDocumentId?: string
  onDocumentChange?: (documentId: string) => void
  onSessionChange?: (session: ChatSession) => void
}

export function ChatSidebar({ selectedDocumentId, onDocumentChange, onSessionChange }: ChatSidebarProps) {
  const { sessions, currentSession, isLoading, fetchSessions, createSession, setCurrentSession } = useChatStore()

  const { documents, fetchDocuments } = useDocumentStore()

  useEffect(() => {
    fetchSessions()
    fetchDocuments()
  }, [])

  const handleNewSession = async () => {
    if (!selectedDocumentId) return

    try {
      const sessionId = await createSession(selectedDocumentId, "New Chat Session")
      // The new session is automatically set as current in the store
    } catch (error) {
      console.error("Failed to create session:", error)
    }
  }

  const handleSessionSelect = (session: ChatSession) => {
    setCurrentSession(session)
    if (onSessionChange) {
      onSessionChange(session)
    }
  }

  const filteredSessions = selectedDocumentId
    ? sessions.filter((session) => session.document_id === selectedDocumentId)
    : sessions

  return (
    <div className="w-80 border-r bg-muted/30 flex flex-col h-full">
      <div className="p-4 border-b">
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Document</label>
            <Select value={selectedDocumentId} onValueChange={onDocumentChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select a document" />
              </SelectTrigger>
              <SelectContent>
                {documents.map((doc) => (
                  <SelectItem key={doc.id} value={doc.id}>
                    {doc.original_filename}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button onClick={handleNewSession} disabled={!selectedDocumentId || isLoading} className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            New Session
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-2">
          {filteredSessions.length === 0 ? (
            <div className="text-center py-8">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                {selectedDocumentId ? "No chat sessions yet" : "Select a document to start chatting"}
              </p>
            </div>
          ) : (
            filteredSessions.map((session) => (
              <Card
                key={session.id}
                className={cn(
                  "cursor-pointer transition-colors hover:bg-muted/50",
                  currentSession?.id === session.id && "ring-2 ring-blue-500 bg-blue-50",
                )}
                onClick={() => handleSessionSelect(session)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <h4 className="font-medium text-sm line-clamp-1">{session.session_name}</h4>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100"
                      onClick={(e) => {
                        e.stopPropagation()
                        // Handle delete session
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="text-xs text-muted-foreground">
                    {session.message_count} messages •{" "}
                    {formatDistanceToNow(new Date(session.last_activity), { addSuffix: true })}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
