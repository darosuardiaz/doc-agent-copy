"use client"

import { useEffect } from "react"
import { useDocumentStore } from "@/lib/stores/document-store"
import { DocumentCard } from "./document-card"
import { Button } from "@/components/ui/button"
import { Upload, RefreshCw } from "lucide-react"
import Link from "next/link"

export function DocumentsList() {
  const { documents, isLoading, error, fetchDocuments } = useDocumentStore()

  useEffect(() => {
    fetchDocuments()
  }, [])

  const handleRefresh = () => {
    fetchDocuments()
  }

  if (isLoading && documents.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">Loading documents...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error loading documents: {error}</p>
          <Button onClick={handleRefresh} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center max-w-md">
          <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-medium mb-2">No documents yet</h3>
          <p className="text-muted-foreground mb-6">
            Upload your first financial document to get started with AI-powered analysis.
          </p>
          <Link href="/upload">
            <Button>
              <Upload className="h-4 w-4 mr-2" />
              Upload Document
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {documents.length} document{documents.length !== 1 ? "s" : ""} found
        </p>
        <Button onClick={handleRefresh} variant="outline" size="sm" disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <div className="grid gap-4">
        {documents.map((document) => (
          <DocumentCard key={document.id} document={document} />
        ))}
      </div>
    </div>
  )
}
