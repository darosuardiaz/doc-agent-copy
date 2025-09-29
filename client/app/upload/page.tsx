"use client"

import { useRouter } from "next/navigation"
import { FileUpload } from "@/components/upload/file-upload"

export default function UploadPage() {
  const router = useRouter()

  const handleUploadComplete = (documentId: string) => {
    // Redirect to document detail page after successful upload
    router.push(`/documents/${documentId}`)
  }

  return (
    <div className="container mx-auto px-6 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">Upload Document</h1>
          <p className="text-muted-foreground">Upload a financial document for AI-powered analysis</p>
        </div>

        <FileUpload onUploadComplete={handleUploadComplete} />
      </div>
    </div>
  )
}
