"use client"

import { formatDistanceToNow } from "date-fns"
import { CheckCircle, Clock } from "lucide-react"
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
        return <Clock className="h-4 w-4 text-blue-600 animate-pulse" />
      case "failed":
        return <Clock className="h-4 w-4 text-red-600" />
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
        </p>
      </CardHeader>
      {task.status === "completed" && task.research_findings && (
        <CardContent className="pt-0">
          <div className="space-y-6">
            {/* Summary */}
            {task.research_findings?.summary && (
              <div>
                <h4 className="font-medium mb-2">Summary</h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-800 leading-relaxed">
                    {task.research_findings.summary}
                  </p>
                </div>
              </div>
            )}

            {/* Content Outline */}
            {task.content_outline && (
              <div>
                <h4 className="font-medium mb-3">Overview (unchanged + additions)</h4>
                <div className="space-y-3">
                  {Object.entries(task.content_outline).map(([key, section]) => (
                    <div key={key} className="border-l-2 border-blue-200 pl-4">
                      <h5 className="font-medium text-sm">{section.title}</h5>
                      <p className="text-sm text-muted-foreground">{section.description}</p>
                    </div>
                  ))}
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
