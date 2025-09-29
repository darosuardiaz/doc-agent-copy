"use client"

import { useEffect } from "react"
import { useResearchStore } from "@/lib/stores/research-store"
import { ResearchResult } from "./research-result"
import { RefreshCw, Search } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ResearchListProps {
  documentId?: string
}

export function ResearchList({ documentId }: ResearchListProps) {
  const { tasks, isLoading, error, fetchTasks } = useResearchStore()

  useEffect(() => {
    if (documentId) {
      fetchTasks(documentId)
    }
  }, [documentId])

  const handleRefresh = () => {
    if (documentId) {
      fetchTasks(documentId)
    }
  }

  const filteredTasks = documentId ? tasks.filter((task) => task.document_id === documentId) : tasks

  if (isLoading && filteredTasks.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">Loading research tasks...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error loading research tasks: {error}</p>
          <Button onClick={handleRefresh} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  if (filteredTasks.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center max-w-md">
          <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-medium mb-2">No research tasks yet</h3>
          <p className="text-muted-foreground mb-6">
            {documentId
              ? "Start your first research task to generate comprehensive analysis from your document."
              : "Select a document and create a research task to get started."}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {filteredTasks.length} research task{filteredTasks.length !== 1 ? "s" : ""} found
        </p>
        <Button onClick={handleRefresh} variant="outline" size="sm" disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <div className="space-y-6">
        {filteredTasks
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
          .map((task) => (
            <ResearchResult key={task.id} task={task} />
          ))}
      </div>
    </div>
  )
}
