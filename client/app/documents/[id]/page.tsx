'use client';

import { useParams, useRouter } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, DocumentStatus } from '@/lib/api-client';
import { formatBytes, formatDate } from '@/lib/utils';
import { FileText, Loader2, AlertCircle, CheckCircle, Clock, Brain, MessageSquare, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';

export default function DocumentDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params.id as string;
  const queryClient = useQueryClient();

  const { data: document, isLoading: docLoading, error: docError } = useQuery({
    queryKey: ['document', documentId],
    queryFn: () => apiClient.getDocument(documentId),
  });

  const { data: status, isLoading: statusLoading, dataUpdatedAt } = useQuery({
    queryKey: ['document-status', documentId],
    queryFn: () => apiClient.getDocumentStatus(documentId),
    enabled: !!documentId,
  });

  // Set up polling based on status
  useEffect(() => {
    if (!status || (status.is_processed && status.is_embedded)) return;
    
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ['document-status', documentId] });
    }, 2000);

    return () => clearInterval(interval);
  }, [status, documentId, queryClient]);

  // Refetch document details when processing is complete
  useEffect(() => {
    if (status?.is_processed && status?.is_embedded) {
      // Refetch document to get updated financial facts, etc.
      queryClient.invalidateQueries({ queryKey: ['document', documentId] });
    }
  }, [status?.is_processed, status?.is_embedded, documentId, queryClient]);

  if (docLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Skeleton className="h-8 w-48" />
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i}>
                  <Skeleton className="h-4 w-20 mb-1" />
                  <Skeleton className="h-5 w-24" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (docError || !document) {
    return (
      <div className="max-w-2xl mx-auto">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load document details.</AlertDescription>
        </Alert>
      </div>
    );
  }

  const isProcessing = !status?.is_processed || !status?.is_embedded;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <Button variant="ghost" size="sm" asChild className="mb-4">
          <Link href="/">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Documents
          </Link>
        </Button>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              {document.original_filename || document.filename}
            </h1>
            <p className="text-muted-foreground">Document ID: {document.id}</p>
          </div>
          
          <div className="flex items-center space-x-3">
            <Button
              disabled={isProcessing}
              asChild={!isProcessing}
            >
              {isProcessing ? (
                <>
                  <Brain className="h-4 w-4 mr-2" />
                  Research
                </>
              ) : (
                <Link href={`/research?documentId=${document.id}`}>
                  <Brain className="h-4 w-4 mr-2" />
                  Research
                </Link>
              )}
            </Button>
            <Button
              disabled={isProcessing}
              asChild={!isProcessing}
            >
              {isProcessing ? (
                <>
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Chat
                </>
              ) : (
                <Link href={`/chat?documentId=${document.id}`}>
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Chat
                </Link>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Processing Status */}
      {isProcessing && status && (
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                <div>
                  <CardTitle>Processing Document</CardTitle>
                  <CardDescription>
                    This may take a few minutes depending on the document size...
                  </CardDescription>
                </div>
              </div>
              <span className="text-2xl font-bold">
                {status.progress_percentage}%
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <Progress value={status.progress_percentage} className="mb-4" />
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                {status.is_processed ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <Clock className="h-5 w-5 text-muted-foreground" />
                )}
                <span className={status.is_processed ? 'text-green-600' : 'text-foreground'}>
                  Document parsing and extraction
                </span>
              </div>
              <div className="flex items-center space-x-2">
                {status.is_embedded ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <Clock className="h-5 w-5 text-muted-foreground" />
                )}
                <span className={status.is_embedded ? 'text-green-600' : 'text-foreground'}>
                  Creating vector embeddings ({status.embedding_count} chunks)
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Document Information */}
      <div className="grid gap-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Document Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-muted-foreground">File Size:</span>
                <p className="font-medium">{formatBytes(document.file_size)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Pages:</span>
                <p className="font-medium">{document.page_count || 'N/A'}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Words:</span>
                <p className="font-medium">
                  {document.word_count ? document.word_count.toLocaleString() : 'N/A'}
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">Embeddings:</span>
                <p className="font-medium">{document.embedding_count || 'N/A'}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Created:</span>
                <p className="font-medium">{formatDate(document.created_at)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Updated:</span>
                <p className="font-medium">{document.updated_at ? formatDate(document.updated_at) : 'N/A'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Financial Facts */}
        {document.financial_facts && Object.keys(document.financial_facts).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Financial Facts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(document.financial_facts).map(([key, value]) => (
                  <div key={key}>
                    <span className="text-muted-foreground text-sm">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                    </span>
                    <p className="font-medium">{String(value)}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Investment Data */}
        {document.investment_data && Object.keys(document.investment_data).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Investment Data</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(document.investment_data).map(([key, value]) => (
                  <div key={key}>
                    <span className="text-muted-foreground text-sm">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                    </span>
                    <p className="font-medium">{String(value)}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Key Metrics */}
        {document.key_metrics && Object.keys(document.key_metrics).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Key Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(document.key_metrics).map(([key, value]) => (
                  <div key={key}>
                    <span className="text-muted-foreground text-sm">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                    </span>
                    <p className="font-medium">
                      {typeof value === 'number' ? value.toLocaleString() : String(value)}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Processing Error */}
        {document.processing_error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <p className="font-medium">Processing Error</p>
              <p className="text-sm mt-1">{document.processing_error}</p>
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
}