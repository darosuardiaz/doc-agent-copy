"use client"

import { useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Search, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useDocumentStore } from "@/lib/stores/document-store"
import { DocumentInfo } from "@/components/documents/document-info"
import { FinancialFacts } from "@/components/documents/financial-facts"
import { ProcessingStatus } from "@/components/documents/processing-status"

export default function DocumentDetailPage() {
  const params = useParams()
  const router = useRouter()
  const documentId = params.id as string

  const { currentDocument, isLoading, error, fetchDocument } = useDocumentStore()

  useEffect(() => {
    if (documentId) {
      fetchDocument(documentId)
    }
  }, [documentId])

  if (isLoading) {
    return (
      <div className="container mx-auto px-6 py-8">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading document...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !currentDocument) {
    return (
      <div className="container mx-auto px-6 py-8">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-red-600 mb-4">{error || "Document not found"}</p>
            <Button onClick={() => router.push("/documents")} variant="outline">
              Back to Documents
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-6 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/documents"
            className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Documents
          </Link>

          <div className="flex items-start justify-between">
            <div className="min-w-0 flex-1">
              <h1 className="text-3xl font-bold mb-2 break-words">{currentDocument.original_filename}</h1>
              <p className="text-muted-foreground">Document ID: {currentDocument.id}</p>
            </div>

            <div className="flex items-center gap-2 ml-4">
              <Link href={`/research?document=${currentDocument.id}`}>
                <Button>
                  <Search className="h-4 w-4 mr-2" />
                  Research
                </Button>
              </Link>
              <Link href={`/chat?document=${currentDocument.id}`}>
                <Button>
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Chat
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="space-y-8">
          <ProcessingStatus
            documentId={currentDocument.id}
            isProcessed={currentDocument.is_processed}
            isEmbedded={currentDocument.is_embedded}
            embeddingCount={currentDocument.embedding_count}
          />
          <DocumentInfo document={currentDocument} />
          <FinancialFacts document={currentDocument} />
        </div>
      </div>
    </div>
  )
}
