'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { formatBytes } from '@/lib/utils';
import { Upload, FileText, X, Loader2, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export default function UploadPage() {
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.uploadDocument(file),
    onSuccess: (data) => {
      toast.success('Upload successful', {
        description: `${selectedFile?.name} has been uploaded and processing has started.`,
      });
      // Redirect to document details or documents list
      setTimeout(() => {
        router.push(`/documents/${data.document_id}`);
      }, 1500);
    },
    onError: (error: any) => {
      toast.error('Upload failed', {
        description: error.message || 'Failed to upload document. Please try again.',
      });
    },
  });

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileSelect = (file: File) => {
    if (file.type !== 'application/pdf') {
      toast.error('Invalid file type', {
        description: 'Please select a PDF file.',
      });
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      toast.error('File too large', {
        description: `Please select a file smaller than ${formatBytes(MAX_FILE_SIZE)}.`,
      });
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile);
    }
  };

  const isUploading = uploadMutation.isPending;
  const isSuccess = uploadMutation.isSuccess;

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Upload Document</h1>
        <p className="text-muted-foreground">Upload a financial document for AI-powered analysis</p>
      </div>

      <Card>
        <CardContent className="p-8">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive 
                ? 'border-primary bg-primary/5' 
                : 'border-border hover:border-muted-foreground'
            } ${isUploading || isSuccess ? 'pointer-events-none opacity-60' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
          {!selectedFile ? (
            <>
              <Upload className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-foreground mb-2">
                Drag and drop your PDF file here, or click to browse
              </p>
              <p className="text-sm text-muted-foreground mb-4">
                Maximum file size: {formatBytes(MAX_FILE_SIZE)}
              </p>
              <Input
                type="file"
                accept=".pdf"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileSelect(e.target.files[0]);
                  }
                }}
                className="hidden"
                id="file-upload"
                disabled={isUploading}
              />
              <Label htmlFor="file-upload">
                <Button asChild>
                  <span className="cursor-pointer">
                    Select File
                  </span>
                </Button>
              </Label>
            </>
          ) : (
            <div className="space-y-4">
              {isSuccess ? (
                <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
              ) : (
                <FileText className="h-12 w-12 text-primary mx-auto mb-4" />
              )}
              
              <div className="bg-secondary rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <FileText className="h-8 w-8 text-muted-foreground" />
                  <div className="text-left">
                    <p className="font-medium">{selectedFile.name}</p>
                    <p className="text-sm text-muted-foreground">{formatBytes(selectedFile.size)}</p>
                  </div>
                </div>
                {!isUploading && !isSuccess && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setSelectedFile(null)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>

              {isSuccess ? (
                <p className="text-green-600 font-medium">
                  Upload successful! Redirecting...
                </p>
              ) : (
                <Button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="w-full"
                  size="lg"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Upload Document
                    </>
                  )}
                </Button>
              )}
            </div>
          )}
          </div>

          <div className="mt-6 space-y-2">
            <h3 className="font-medium">Supported Features:</h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• PDF document parsing with advanced extraction</li>
              <li>• Financial facts and metrics extraction</li>
              <li>• Investment data analysis</li>
              <li>• Semantic search with vector embeddings</li>
              <li>• AI-powered research and chat capabilities</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}