'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient, Document, ResearchTask } from '@/lib/api-client';
import { formatRelativeTime } from '@/lib/utils';
import { Brain, FileText, Loader2, AlertCircle, CheckCircle, Clock, ChevronRight, ChevronDown } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

function ResearchContent() {
  const searchParams = useSearchParams();
  const preselectedDocumentId = searchParams.get('documentId');
  
  const [selectedDocument, setSelectedDocument] = useState<string>(preselectedDocumentId || '');
  const [topic, setTopic] = useState('');
  const [customQuery, setCustomQuery] = useState('');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  const { data: researchTasks, refetch: refetchTasks } = useQuery({
    queryKey: ['research-tasks', selectedDocument],
    queryFn: () => selectedDocument ? apiClient.listResearchTasks(selectedDocument) : null,
    enabled: !!selectedDocument,
  });

  const startResearchMutation = useMutation({
    mutationFn: ({ documentId, topic, customQuery }: { documentId: string; topic: string; customQuery?: string }) =>
      apiClient.startResearch(documentId, topic, customQuery),
    onSuccess: (data) => {
      toast.success('Research started', {
        description: `Research task "${data.topic}" has been initiated.`,
      });
      refetchTasks();
      // Clear form
      setTopic('');
      setCustomQuery('');
    },
    onError: (error: any) => {
      toast.error('Failed to start research', {
        description: error.message || 'Please try again.',
      });
    },
  });

  // Poll for task updates
  useEffect(() => {
    if (!researchTasks || researchTasks.length === 0) return;

    const hasInProgressTasks = researchTasks.some(task => task.status === 'in_progress' || task.status === 'pending');
    if (!hasInProgressTasks) return;

    const interval = setInterval(() => {
      refetchTasks();
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
  }, [researchTasks, refetchTasks]);

  const handleStartResearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDocument || !topic.trim()) return;
    
    startResearchMutation.mutate({
      documentId: selectedDocument,
      topic: topic.trim(),
      customQuery: customQuery.trim() || undefined,
    });
  };

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const processedDocuments = documents?.filter(doc => doc.is_processed && doc.is_embedded) || [];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Deep Research</h1>
        <p className="text-muted-foreground">Generate comprehensive research and analysis from your documents</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Research Form */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>New Research Task</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleStartResearch} className="space-y-4">
                <div>
                  <Label>Select Document</Label>
                  <Select
                    value={selectedDocument}
                    onValueChange={setSelectedDocument}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Choose a document..." />
                    </SelectTrigger>
                    <SelectContent>
                      {processedDocuments.map((doc) => (
                        <SelectItem key={doc.id} value={doc.id}>
                          {doc.original_filename || doc.filename}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Research Topic</Label>
                  <Input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g., Key Investment Highlights"
                    required
                  />
                </div>

                <div>
                  <Label>Custom Query (Optional)</Label>
                  <Textarea
                    value={customQuery}
                    onChange={(e) => setCustomQuery(e.target.value)}
                    placeholder="Add specific questions or areas to focus on..."
                    rows={3}
                  />
                </div>

                <Button
                  type="submit"
                  disabled={!selectedDocument || !topic.trim() || startResearchMutation.isPending}
                  className="w-full"
                >
                  {startResearchMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Starting Research...
                    </>
                  ) : (
                    <>
                      <Brain className="h-4 w-4 mr-2" />
                      Start Research
                    </>
                  )}
                </Button>
              </form>

              {processedDocuments.length === 0 && (
                <Alert className="mt-4">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No processed documents available. Please upload and wait for documents to be fully processed before starting research.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Research Tasks */}
        <div className="lg:col-span-2">
          {!selectedDocument ? (
            <Card className="h-full">
              <CardContent className="flex items-center justify-center h-full min-h-[400px]">
                <div className="text-center">
                  <Brain className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Select a document to view research tasks</p>
                </div>
              </CardContent>
            </Card>
          ) : researchTasks && researchTasks.length > 0 ? (
            <div className="space-y-4">
              {researchTasks.map((task) => (
                <Card key={task.id}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold">{task.topic}</h3>
                        {task.custom_query && (
                          <p className="text-sm text-muted-foreground mt-1">{task.custom_query}</p>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        {task.status === 'completed' && (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        )}
                        {task.status === 'in_progress' && (
                          <Loader2 className="h-5 w-5 animate-spin text-primary" />
                        )}
                        {task.status === 'pending' && (
                          <Clock className="h-5 w-5 text-muted-foreground" />
                        )}
                        {task.status === 'failed' && (
                          <AlertCircle className="h-5 w-5 text-destructive" />
                        )}
                        <Badge variant={
                          task.status === 'completed' ? 'default' :
                          task.status === 'in_progress' ? 'secondary' :
                          task.status === 'pending' ? 'outline' :
                          'destructive'
                        }>
                          {task.status.replace('_', ' ')}
                        </Badge>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span>Created {formatRelativeTime(task.created_at)}</span>
                      {task.processing_time && (
                        <span>• {task.processing_time.toFixed(1)}s processing time</span>
                      )}
                    </div>

                    {/* Content Outline */}
                    {task.content_outline && Object.keys(task.content_outline).length > 0 && (
                      <div className="mt-6">
                        <h4 className="font-medium mb-3">Content Outline</h4>
                        <div className="space-y-2">
                          {Object.entries(task.content_outline).map(([key, section]) => {
                            const sectionId = `${task.id}-${key}`;
                            const isExpanded = expandedSections.has(sectionId);
                            const findings = task.research_findings?.[key];

                            return (
                              <Collapsible
                                key={key}
                                open={isExpanded}
                                onOpenChange={() => toggleSection(sectionId)}
                              >
                                <Card>
                                  <CollapsibleTrigger asChild>
                                    <Button
                                      variant="ghost"
                                      className="w-full justify-between p-4 h-auto"
                                    >
                                      <div className="flex items-start text-left">
                                        <span className="font-medium text-muted-foreground mr-2">{key}.</span>
                                        <div>
                                          <p className="font-medium">{section.title}</p>
                                          <p className="text-sm text-muted-foreground">{section.description}</p>
                                        </div>
                                      </div>
                                      {isExpanded ? (
                                        <ChevronDown className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                                      ) : (
                                        <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                                      )}
                                    </Button>
                                  </CollapsibleTrigger>

                                  <CollapsibleContent>
                                    {findings && (
                                      <CardContent className="pt-0 pb-4">
                                        <div className="prose prose-sm max-w-none">
                                          <p className="text-foreground">{findings.content}</p>
                                          {findings.key_points && findings.key_points.length > 0 && (
                                            <div className="mt-3">
                                              <p className="font-medium">Key Points:</p>
                                              <ul className="mt-1 space-y-1">
                                                {findings.key_points.map((point, idx) => (
                                                  <li key={idx}>{point}</li>
                                                ))}
                                              </ul>
                                            </div>
                                          )}
                                        </div>
                                      </CardContent>
                                    )}
                                  </CollapsibleContent>
                                </Card>
                              </Collapsible>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Sources */}
                    {task.sources_used && task.sources_used.length > 0 && (
                      <div className="mt-6">
                        <h4 className="font-medium mb-3">Sources Used</h4>
                        <div className="space-y-2">
                          {task.sources_used.slice(0, 5).map((source, idx) => (
                            <div key={idx} className="bg-secondary rounded p-3 text-sm">
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-medium">Page {source.page}</span>
                                <Badge variant="outline" className="text-xs">
                                  {(source.relevance_score * 100).toFixed(0)}% relevance
                                </Badge>
                              </div>
                              <p className="text-muted-foreground line-clamp-2">{source.content}</p>
                            </div>
                          ))}
                          {task.sources_used.length > 5 && (
                            <p className="text-sm text-muted-foreground text-center">
                              and {task.sources_used.length - 5} more sources...
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="h-full">
              <CardContent className="flex items-center justify-center h-full min-h-[400px]">
                <div className="text-center">
                  <Brain className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-foreground">No research tasks yet for this document</p>
                  <p className="text-sm text-muted-foreground mt-2">Create your first research task using the form</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ResearchPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-screen"><Loader2 className="h-8 w-8 animate-spin" /></div>}>
      <ResearchContent />
    </Suspense>
  );
}