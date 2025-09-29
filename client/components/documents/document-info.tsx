"use client"

import { formatDistanceToNow } from "date-fns"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { Document } from "@/lib/stores/document-store"

interface DocumentInfoProps {
  document: Document
}

export function DocumentInfo({ document }: DocumentInfoProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Document Information</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <span className="text-sm text-muted-foreground">File Size:</span>
              <div className="font-medium">{formatFileSize(document.file_size)}</div>
            </div>

            <div>
              <span className="text-sm text-muted-foreground">Words:</span>
              <div className="font-medium">{document.word_count || "N/A"}</div>
            </div>

            <div>
              <span className="text-sm text-muted-foreground">Created:</span>
              <div className="font-medium">
                {new Date(document.created_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <span className="text-sm text-muted-foreground">Pages:</span>
              <div className="font-medium">{document.page_count || "N/A"}</div>
            </div>

            <div>
              <span className="text-sm text-muted-foreground">Embeddings:</span>
              <div className="font-medium">{document.embedding_count || "N/A"}</div>
            </div>

            <div>
              <span className="text-sm text-muted-foreground">Updated:</span>
              <div className="font-medium">
                {formatDistanceToNow(new Date(document.updated_at), { addSuffix: true })}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
