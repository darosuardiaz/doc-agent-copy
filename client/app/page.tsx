'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, Document } from '@/lib/api-client';
import { formatBytes, formatDate, formatRelativeTime } from '@/lib/utils';
import { FileText, Trash2, Eye, Brain, MessageSquare, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';

export default function DocumentsPage() {
  const queryClient = useQueryClient();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data: documents, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  const deleteMutation = useMutation({
    mutationFn: (documentId: string) => apiClient.deleteDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Document deleted', {
        description: 'The document has been successfully deleted.',
      });
    },
    onError: (error) => {
      toast.error('Error', {
        description: 'Failed to delete document. Please try again.',
      });
    },
    onSettled: () => {
      setDeletingId(null);
    },
  });

  const handleDelete = (documentId: string) => {
    if (confirm('Are you sure you want to delete this document?')) {
      setDeletingId(documentId);
      deleteMutation.mutate(documentId);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Documents</h1>
          <p className="text-muted-foreground">Manage your uploaded financial documents</p>
        </div>
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="space-y-3">
                <Skeleton className="h-5 w-1/3" />
                <Skeleton className="h-4 w-1/2" />
                <div className="flex gap-4">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-20" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load documents. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Documents</h1>
        <p className="text-muted-foreground">Manage your uploaded financial documents</p>
      </div>

      {documents?.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No documents yet</h3>
            <p className="text-muted-foreground mb-6">Upload your first document to get started</p>
            <Button asChild>
              <Link href="/upload">
                Upload Document
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {documents?.map((doc) => (
            <Card
              key={doc.id}
              className="hover:shadow-md transition-shadow"
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <FileText className="h-5 w-5 text-primary" />
                      <h3 className="text-lg font-semibold">
                        {doc.original_filename || doc.filename}
                      </h3>
                      {doc.is_processed && doc.is_embedded && (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      )}
                    </div>
                  
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Size:</span>{' '}
                        <span className="font-medium">{formatBytes(doc.file_size)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Pages:</span>{' '}
                        <span className="font-medium">{doc.page_count || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Words:</span>{' '}
                        <span className="font-medium">
                          {doc.word_count ? doc.word_count.toLocaleString() : 'N/A'}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Uploaded:</span>{' '}
                        <span className="font-medium">{formatRelativeTime(doc.created_at)}</span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 text-sm">
                      <Badge variant={doc.is_processed ? 'default' : 'secondary'}>
                        {doc.is_processed ? 'Processed' : 'Processing'}
                      </Badge>
                      <Badge variant={doc.is_embedded ? 'default' : 'secondary'}>
                        {doc.is_embedded ? 'Embedded' : 'Not Embedded'}
                      </Badge>
                      {doc.embedding_count && (
                        <span className="text-muted-foreground">
                          {doc.embedding_count} embeddings
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      asChild
                    >
                      <Link
                        href={`/documents/${doc.id}`}
                        title="View details"
                      >
                        <Eye className="h-4 w-4" />
                      </Link>
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      asChild
                    >
                      <Link
                        href={`/research?documentId=${doc.id}`}
                        title="Research"
                      >
                        <Brain className="h-4 w-4" />
                      </Link>
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      asChild
                    >
                      <Link
                        href={`/chat?documentId=${doc.id}`}
                        title="Chat"
                      >
                        <MessageSquare className="h-4 w-4" />
                      </Link>
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(doc.id)}
                      disabled={deletingId === doc.id}
                      title="Delete"
                    >
                      {deletingId === doc.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}