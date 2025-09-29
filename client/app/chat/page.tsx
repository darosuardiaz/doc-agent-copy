"use client"

import { useState, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { ChatSidebar } from "@/components/chat/chat-sidebar"
import { ChatInterface } from "@/components/chat/chat-interface"
import { useChatStore, type ChatSession } from "@/lib/stores/chat-store"

export default function ChatPage() {
  const searchParams = useSearchParams()
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>("")
  const { currentSession } = useChatStore()

  useEffect(() => {
    const documentParam = searchParams.get("document")
    if (documentParam) {
      setSelectedDocumentId(documentParam)
    }
  }, [searchParams])

  const handleDocumentChange = (documentId: string) => {
    setSelectedDocumentId(documentId)
  }

  const handleSessionChange = (session: ChatSession) => {
    // Session change is handled by the store
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex">
      <ChatSidebar
        selectedDocumentId={selectedDocumentId}
        onDocumentChange={handleDocumentChange}
        onSessionChange={handleSessionChange}
      />
      <ChatInterface session={currentSession} documentId={selectedDocumentId} />
    </div>
  )
}
