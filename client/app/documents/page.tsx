"use client"

import { DocumentsList } from "@/components/documents/documents-list"
import { Button } from "@/components/ui/button"
import { Upload } from "lucide-react"
import Link from "next/link"

export default function DocumentsPage() {
  return (
    <div className="container mx-auto px-6 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Documents</h1>
            <p className="text-muted-foreground">Manage your uploaded financial documents</p>
          </div>

          <Link href="/upload">
            <Button>
              <Upload className="h-4 w-4 mr-2" />
              Upload Document
            </Button>
          </Link>
        </div>

        <DocumentsList />
      </div>
    </div>
  )
}
