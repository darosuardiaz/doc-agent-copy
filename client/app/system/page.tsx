"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Settings, Database, Cpu, Globe } from "lucide-react"

export default function SystemPage() {
  return (
    <div className="container mx-auto px-6 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">System</h1>
          <p className="text-muted-foreground">System configuration and status information</p>
        </div>

        <div className="grid gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Application Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Frontend Status</span>
                  <Badge className="bg-green-100 text-green-800">Online</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Backend API</span>
                  <Badge variant="outline">Not Connected</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Document Processing</span>
                  <Badge variant="outline">Pending</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">AI Services</span>
                  <Badge variant="outline">Pending</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Storage & Database
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Vector Database (Pinecone)</span>
                  <Badge variant="outline">Not Configured</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">File Storage</span>
                  <Badge variant="outline">Local</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Session Storage</span>
                  <Badge variant="outline">Memory</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cpu className="h-5 w-5" />
                AI & Processing
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Document Parser</span>
                  <Badge variant="outline">Not Connected</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Embedding Model</span>
                  <Badge variant="outline">Not Configured</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Chat Model</span>
                  <Badge variant="outline">Not Configured</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Research Agent</span>
                  <Badge variant="outline">Not Configured</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                API Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <span className="text-sm font-medium">Backend URL:</span>
                  <p className="text-sm text-muted-foreground">http://localhost:8000</p>
                </div>
                <div>
                  <span className="text-sm font-medium">Environment:</span>
                  <p className="text-sm text-muted-foreground">Development</p>
                </div>
                <div>
                  <span className="text-sm font-medium">Version:</span>
                  <p className="text-sm text-muted-foreground">1.0.0</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
