"use client"

import type React from "react"

import { useState } from "react"
import { Brain } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useDocumentStore } from "@/lib/stores/document-store"
import { useResearchStore } from "@/lib/stores/research-store"

interface ResearchFormProps {
  selectedDocumentId?: string
  onDocumentChange?: (documentId: string) => void
  onResearchStart?: (taskId: string) => void
}

export function ResearchForm({ selectedDocumentId, onDocumentChange, onResearchStart }: ResearchFormProps) {
  const [topic, setTopic] = useState("")
  const [customQuery, setCustomQuery] = useState("")

  const { documents } = useDocumentStore()
  const { startResearch, isLoading } = useResearchStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedDocumentId || !topic.trim()) return

    try {
      const taskId = await startResearch(selectedDocumentId, topic.trim(), customQuery.trim() || undefined)

      if (onResearchStart) {
        onResearchStart(taskId)
      }

      // Reset form
      setTopic("")
      setCustomQuery("")
    } catch (error) {
      console.error("Failed to start research:", error)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>New Research Task</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="document">Select Document</Label>
            <Select value={selectedDocumentId} onValueChange={onDocumentChange}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a document to research" />
              </SelectTrigger>
              <SelectContent>
                {documents
                  .filter((doc) => doc.is_processed)
                  .map((doc) => (
                    <SelectItem key={doc.id} value={doc.id}>
                      {doc.original_filename}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="topic">Research Topic</Label>
            <Input
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., Key Investment Highlights"
              required
            />
          </div>

          <div>
            <Label htmlFor="query">Custom Query (Optional)</Label>
            <Textarea
              id="query"
              value={customQuery}
              onChange={(e) => setCustomQuery(e.target.value)}
              placeholder="Add specific questions or areas to focus on..."
              rows={3}
            />
          </div>

          <Button type="submit" disabled={!selectedDocumentId || !topic.trim() || isLoading} className="w-full">
            <Brain className="h-4 w-4 mr-2" />
            {isLoading ? "Starting Research..." : "Start Research"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
