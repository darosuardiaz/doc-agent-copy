"use client"

import Link from "next/link"
import { formatDistanceToNow } from "date-fns"
import { FileText, Eye, Search, MessageSquare, Trash2, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { useDocumentStore, type Document } from "@/lib/stores/document-store"
import { cn } from "@/lib/utils"

interface DocumentCardProps {
  document: Document
}

export function DocumentCard({ document }: DocumentCardProps) {
  const { deleteDocument } = useDocumentStore()

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const handleDelete = async () => {
    if (confirm("Are you sure you want to delete this document?")) {
      try {
        await deleteDocument(document.id)
      } catch (error) {
        console.error("Failed to delete document:", error)
      }
    }
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <FileText className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <Link
                href={`/documents/${document.id}`}
                className="font-medium text-foreground hover:text-blue-600 transition-colors line-clamp-1"
              >
                {document.original_filename}
              </Link>
              {document.is_processed && (
                <div className="flex items-center gap-1 mt-1">
                  <CheckCircle className="h-3 w-3 text-green-600" />
                  <span className="text-xs text-green-600">Processed</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1 ml-2">
            <Link href={`/documents/${document.id}`}>
              <Button variant="ghost" size="sm">
                <Eye className="h-4 w-4" />
              </Button>
            </Link>
            <Link href={`/research?document=${document.id}`}>
              <Button variant="ghost" size="sm">
                <Search className="h-4 w-4" />
              </Button>
            </Link>
            <Link href={`/chat?document=${document.id}`}>
              <Button variant="ghost" size="sm">
                <MessageSquare className="h-4 w-4" />
              </Button>
            </Link>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDelete}
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Size:</span>
            <div className="font-medium">{formatFileSize(document.file_size)}</div>
          </div>
          <div>
            <span className="text-muted-foreground">Pages:</span>
            <div className="font-medium">{document.page_count || "N/A"}</div>
          </div>
          <div>
            <span className="text-muted-foreground">Words:</span>
            <div className="font-medium">{document.word_count || "N/A"}</div>
          </div>
          <div>
            <span className="text-muted-foreground">Uploaded:</span>
            <div className="font-medium">{formatDistanceToNow(new Date(document.created_at), { addSuffix: true })}</div>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-4">
          <Badge
            variant={document.is_processed ? "default" : "secondary"}
            className={cn(document.is_processed && "bg-green-100 text-green-800 hover:bg-green-100")}
          >
            {document.is_processed ? "Processed" : "Processing"}
          </Badge>
          <Badge
            variant={document.is_embedded ? "default" : "secondary"}
            className={cn(document.is_embedded && "bg-blue-100 text-blue-800 hover:bg-blue-100")}
          >
            {document.is_embedded ? "Embedded" : "Pending"}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}
