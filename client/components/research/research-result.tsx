"use client"

import { formatDistanceToNow } from "date-fns"
import { CheckCircle, Clock, AlertCircle, Loader2 } from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeRaw from "rehype-raw"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SourcesDisplay } from "@/components/ui/sources-display"
import type { ResearchTask } from "@/lib/stores/research-store"
import { cn } from "@/lib/utils"

interface ResearchResultProps {
  task: ResearchTask
}

export function ResearchResult({ task }: ResearchResultProps) {
  const getStatusIcon = () => {
    switch (task.status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "in_progress":
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case "pending":
        return <Clock className="h-4 w-4 text-orange-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusColor = () => {
    switch (task.status) {
      case "completed":
        return "bg-green-100 text-green-800"
      case "in_progress":
        return "bg-blue-100 text-blue-800"
      case "failed":
        return "bg-red-100 text-red-800"
      case "pending":
        return "bg-orange-100 text-orange-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <CardTitle className="text-lg">{task.topic}</CardTitle>
          </div>
          <Badge className={cn("capitalize", getStatusColor())}>
            {task.status === "in_progress" ? "in progress" : task.status}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Created {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
          {task.completed_at && (
            <span> • Completed {formatDistanceToNow(new Date(task.completed_at), { addSuffix: true })}</span>
          )}
        </p>
      </CardHeader>
      
      {/* Show error message for failed tasks */}
      {task.status === "failed" && (
        <CardContent className="pt-0">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-red-800 mb-2">
              <AlertCircle className="h-4 w-4" />
              <span className="font-medium">Research Failed</span>
            </div>
            <p className="text-sm text-red-700">
              {task.error_message || "An error occurred during research processing."}
            </p>
          </div>
        </CardContent>
      )}
      
      {/* Show progress for pending/in-progress tasks */}
      {(task.status === "pending" || task.status === "in_progress") && (
        <CardContent className="pt-0">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-blue-800 mb-2">
              {getStatusIcon()}
              <span className="font-medium">
                {task.status === "pending" ? "Research Queued" : "Research in Progress"}
              </span>
            </div>
            <p className="text-sm text-blue-700">
              {task.status === "pending" 
                ? "Your research task is waiting to be processed..."
                : "Your research is being generated. This may take a few minutes..."
              }
            </p>
          </div>
        </CardContent>
      )}
      
      {task.status === "completed" && task.research_findings && (
        <CardContent className="pt-0">
          <div className="space-y-6">
            {/* Summary */}
            {task.research_findings?.summary && (
              <div>
                <h4 className="font-medium mb-2">Summary</h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="prose prose-sm prose-gray max-w-none text-sm text-gray-800 leading-relaxed">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw]}
                      components={{
                        // Custom styling for headings
                        h2: ({ children }) => (
                          <h2 className="text-lg font-semibold text-gray-900 mt-4 mb-2 border-b border-gray-200 pb-1">
                            {children}
                          </h2>
                        ),
                        h3: ({ children }) => (
                          <h3 className="text-base font-medium text-gray-800 mt-3 mb-2">
                            {children}
                          </h3>
                        ),
                        // Custom styling for lists
                        ul: ({ children }) => (
                          <ul className="list-disc list-inside space-y-1 ml-2">
                            {children}
                          </ul>
                        ),
                        ol: ({ children }) => (
                          <ol className="list-decimal list-inside space-y-1 ml-2">
                            {children}
                          </ol>
                        ),
                        // Custom styling for paragraphs
                        p: ({ children }) => (
                          <p className="mb-3 last:mb-0">
                            {children}
                          </p>
                        ),
                        // Custom styling for tables
                        table: ({ children }) => (
                          <div className="overflow-x-auto my-4">
                            <table className="min-w-full border border-gray-200 rounded-lg">
                              {children}
                            </table>
                          </div>
                        ),
                        thead: ({ children }) => (
                          <thead className="bg-gray-100">
                            {children}
                          </thead>
                        ),
                        th: ({ children }) => (
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-b border-gray-200">
                            {children}
                          </th>
                        ),
                        td: ({ children }) => (
                          <td className="px-3 py-2 text-sm text-gray-800 border-b border-gray-200">
                            {children}
                          </td>
                        ),
                        // Custom styling for bold text
                        strong: ({ children }) => (
                          <strong className="font-semibold text-gray-900">
                            {children}
                          </strong>
                        ),
                      }}
                    >
                      {task.research_findings.summary}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            )}

            {/* Sources Used */}
            <SourcesDisplay sources={task.sources_used || []} />

            {/* Processing Time */}
            {task.processing_time && (
              <div className="text-xs text-muted-foreground">
                Processing completed in {task.processing_time.toFixed(1)} seconds
              </div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  )
}
