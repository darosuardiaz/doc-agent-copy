"use client"

import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, FileText, AlertCircle, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { useDocumentStore } from "@/lib/stores/document-store"
import { cn } from "@/lib/utils"

interface FileUploadProps {
  onUploadComplete?: (documentId: string) => void
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "success" | "error">("idle")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const { uploadDocument, isLoading } = useDocumentStore()

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (!file) return

      // Validate file type
      if (file.type !== "application/pdf") {
        setErrorMessage("Only PDF files are supported")
        setUploadStatus("error")
        return
      }

      // Validate file size (50MB limit)
      const maxSize = 50 * 1024 * 1024 // 50MB in bytes
      if (file.size > maxSize) {
        setErrorMessage("File size must be less than 50MB")
        setUploadStatus("error")
        return
      }

      try {
        setUploadStatus("uploading")
        setErrorMessage(null)
        setUploadProgress(0)

        // Simulate upload progress
        const progressInterval = setInterval(() => {
          setUploadProgress((prev) => {
            if (prev >= 90) {
              clearInterval(progressInterval)
              return 90
            }
            return prev + 10
          })
        }, 200)

        const documentId = await uploadDocument(file)

        clearInterval(progressInterval)
        setUploadProgress(100)
        setUploadStatus("success")

        if (onUploadComplete) {
          onUploadComplete(documentId)
        }

        // Reset after 2 seconds
        setTimeout(() => {
          setUploadStatus("idle")
          setUploadProgress(0)
        }, 2000)
      } catch (error) {
        setUploadStatus("error")
        setErrorMessage(error instanceof Error ? error.message : "Upload failed")
        setUploadProgress(0)
      }
    },
    [uploadDocument, onUploadComplete],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
    },
    maxFiles: 1,
    disabled: isLoading || uploadStatus === "uploading",
  })

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
          isDragActive && "border-blue-500 bg-blue-50",
          uploadStatus === "uploading" && "border-blue-500 bg-blue-50",
          uploadStatus === "success" && "border-green-500 bg-green-50",
          uploadStatus === "error" && "border-red-500 bg-red-50",
          uploadStatus === "idle" && "border-gray-300 hover:border-gray-400",
        )}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center gap-4">
          {uploadStatus === "uploading" && (
            <div className="w-full max-w-xs">
              <Progress value={uploadProgress} className="h-2" />
              <p className="text-sm text-muted-foreground mt-2">Uploading... {uploadProgress}%</p>
            </div>
          )}

          {uploadStatus === "success" && (
            <>
              <CheckCircle className="h-12 w-12 text-green-600" />
              <p className="text-green-700 font-medium">Upload successful!</p>
            </>
          )}

          {uploadStatus === "error" && (
            <>
              <AlertCircle className="h-12 w-12 text-red-600" />
              <p className="text-red-700 font-medium">Upload failed</p>
              {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
            </>
          )}

          {(uploadStatus === "idle" || uploadStatus === "error") && (
            <>
              <Upload className="h-12 w-12 text-gray-400" />
              <div>
                <p className="text-lg font-medium">
                  {isDragActive ? "Drop your PDF file here" : "Drag and drop your PDF file here, or click to browse"}
                </p>
                <p className="text-sm text-muted-foreground mt-1">Maximum file size: 50 MB</p>
              </div>
              <Button disabled={uploadStatus === "uploading"}>Select File</Button>
            </>
          )}
        </div>
      </div>

      <div className="mt-8">
        <h3 className="font-medium mb-4">Supported Features:</h3>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            PDF document parsing with advanced extraction
          </li>
          <li className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Financial facts and metrics extraction
          </li>
          <li className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Investment data analysis
          </li>
          <li className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Semantic search with vector embeddings
          </li>
          <li className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            AI-powered research and chat capabilities
          </li>
        </ul>
      </div>
    </div>
  )
}
