"use client"

import { FileText } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface Source {
  page: number
  content: string
  relevance_score: number
}

interface SourcesDisplayProps {
  sources: Source[]
  className?: string
  showBorder?: boolean
}

export function SourcesDisplay({ sources, className = "", showBorder = false }: SourcesDisplayProps) {
  if (!sources || sources.length === 0) {
    return null
  }

  return (
    <div className={`${showBorder ? "mt-4 pt-3 border-t border-gray-200" : ""} ${className}`}>
      <div className="flex items-center gap-2 mb-2">
        <FileText className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium text-muted-foreground">Sources Used</span>
      </div>
      <div className="space-y-2">
        {sources.map((source, index) => (
          <div key={index} className="relative group inline-block">
            <Badge variant="outline" className="text-xs cursor-pointer">
              Page {source.page}
            </Badge>

            <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-10 w-80 bg-white border border-gray-200 rounded-lg shadow-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <Badge variant="outline" className="text-xs">
                  Page {source.page}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  Score: {Math.round(source.relevance_score * 100)}%
                </Badge>
              </div>
              <p className="text-sm text-gray-700">{source.content}</p>
              <div className="absolute top-full left-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-200"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}