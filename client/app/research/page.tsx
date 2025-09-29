"use client"

import { useState, useEffect } from "react"
import { ResearchForm } from "@/components/research/research-form"
import { ResearchList } from "@/components/research/research-list"
import { useDocumentStore } from "@/lib/stores/document-store"

export default function ResearchPage() {
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>("")
  const { documents, fetchDocuments } = useDocumentStore()

  useEffect(() => {
    if (documents.length === 0) {
      fetchDocuments()
    }
  }, [])

  const handleDocumentChange = (documentId: string) => {
    setSelectedDocumentId(documentId)
  }

  const handleResearchStart = (taskId: string) => {
    // Research started, the list will automatically update
    console.log("[v0] Research task started:", taskId)
  }

  return (
    <div className="container mx-auto px-6 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Deep Research</h1>
          <p className="text-muted-foreground">Generate comprehensive research and analysis from your documents</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Research Form */}
          <div>
            <ResearchForm
              selectedDocumentId={selectedDocumentId}
              onDocumentChange={handleDocumentChange}
              onResearchStart={handleResearchStart}
            />
          </div>

          {/* Research Results */}
          <div>
            <ResearchList documentId={selectedDocumentId} />
          </div>
        </div>
      </div>
    </div>
  )
}
