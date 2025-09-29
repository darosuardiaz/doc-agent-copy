"use client"

import { useEffect, useState } from "react"
import { Clock, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

interface ProcessingStep {
  id: string
  label: string
  completed: boolean
  current: boolean
}

interface ProcessingStatusProps {
  documentId: string
  isProcessed: boolean
  isEmbedded: boolean
  embeddingCount?: number
}

export function ProcessingStatus({ documentId, isProcessed, isEmbedded, embeddingCount = 0 }: ProcessingStatusProps) {
  const [progress, setProgress] = useState(0)
  const [steps, setSteps] = useState<ProcessingStep[]>([
    { id: "parsing", label: "Document parsing and extraction", completed: false, current: false },
    {
      id: "embedding",
      label: `Creating vector embeddings (${embeddingCount} chunks)`,
      completed: false,
      current: false,
    },
  ])

  // Mock processing simulation
  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = Math.min(prev + Math.random() * 15, 100)

        // Update steps based on progress
        setSteps((currentSteps) =>
          currentSteps.map((step) => {
            if (step.id === "parsing") {
              return {
                ...step,
                completed: newProgress > 40 || isProcessed,
                current: newProgress <= 40 && !isProcessed,
              }
            }
            if (step.id === "embedding") {
              return {
                ...step,
                label: `Creating vector embeddings (${Math.floor(newProgress / 10)} chunks)`,
                completed: newProgress > 80 || isEmbedded,
                current: newProgress > 40 && newProgress <= 80 && !isEmbedded,
              }
            }
            return step
          }),
        )

        return newProgress
      })
    }, 2000)

    return () => clearInterval(interval)
  }, [isProcessed, isEmbedded])

  // Don't show processing status if document is fully processed
  if (isProcessed && isEmbedded) {
    return null
  }

  return (
    <Card className="border-blue-200 bg-blue-50/50">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
            <CardTitle className="text-blue-700">Processing Document</CardTitle>
          </div>
          <div className="text-2xl font-bold text-blue-600">{Math.round(progress)}%</div>
        </div>
        <p className="text-sm text-blue-600">This may take a few minutes depending on the document size...</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <Progress value={progress} className="h-2" />

        <div className="space-y-3">
          {steps.map((step) => (
            <div key={step.id} className="flex items-center gap-3">
              <div
                className={cn(
                  "flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center",
                  step.completed
                    ? "bg-green-100 border-green-500 text-green-600"
                    : step.current
                      ? "bg-blue-100 border-blue-500 text-blue-600"
                      : "bg-gray-100 border-gray-300 text-gray-400",
                )}
              >
                {step.completed ? (
                  <div className="w-2 h-2 bg-green-600 rounded-full" />
                ) : step.current ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Clock className="w-3 h-3" />
                )}
              </div>
              <span
                className={cn(
                  "text-sm",
                  step.completed
                    ? "text-green-700 font-medium"
                    : step.current
                      ? "text-blue-700 font-medium"
                      : "text-gray-600",
                )}
              >
                {step.label}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
