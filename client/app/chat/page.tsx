'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient, Document, ChatSession, ChatMessage } from '@/lib/api-client';
import { formatRelativeTime, formatDate } from '@/lib/utils';
import { MessageSquare, Send, Loader2, Plus, FileText, Bot, User, Settings } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Skeleton } from '@/components/ui/skeleton';

function ChatContent() {
  const searchParams = useSearchParams();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const preselectedDocumentId = searchParams.get('documentId');
  
  const [selectedDocument, setSelectedDocument] = useState<string>(preselectedDocumentId || 'all');
  const [selectedSession, setSelectedSession] = useState<string>('');
  const [message, setMessage] = useState('');
  const [useRag, setUseRag] = useState(true);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [sessionName, setSessionName] = useState('');

  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  const { data: sessions, refetch: refetchSessions } = useQuery({
    queryKey: ['chat-sessions'],
    queryFn: () => apiClient.listChatSessions(),
  });

  const { data: messages, refetch: refetchMessages } = useQuery({
    queryKey: ['chat-messages', selectedSession],
    queryFn: () => selectedSession ? apiClient.getChatHistory(selectedSession) : null,
    enabled: !!selectedSession,
  });

  const createSessionMutation = useMutation({
    mutationFn: ({ documentId, name }: { documentId: string; name?: string }) =>
      apiClient.createChatSession(documentId, name),
    onSuccess: (data) => {
      toast.success('Session created', {
        description: 'New chat session has been created.',
      });
      setSelectedSession(data.id);
      refetchSessions();
      setIsCreatingSession(false);
      setSessionName('');
    },
    onError: (error: any) => {
      toast.error('Failed to create session', {
        description: error.message || 'Please try again.',
      });
    },
  });

  const sendMessageMutation = useMutation({
    mutationFn: ({ message, documentId, sessionId, useRag }: { 
      message: string; 
      documentId?: string; 
      sessionId?: string;
      useRag: boolean;
    }) => apiClient.sendMessage(message, documentId, sessionId, useRag),
    onSuccess: () => {
      setMessage('');
      refetchMessages();
    },
    onError: (error: any) => {
      toast.error('Failed to send message', {
        description: error.message || 'Please try again.',
      });
    },
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Filter sessions for selected document
  const documentSessions = sessions?.filter(
    session => selectedDocument === 'all' || session.document_id === selectedDocument
  ) || [];

  const processedDocuments = documents?.filter(doc => doc.is_processed && doc.is_embedded) || [];

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const currentMessage = message.trim();
    setMessage(''); // Clear immediately for better UX

    sendMessageMutation.mutate({
      message: currentMessage,
      documentId: selectedDocument === 'all' ? undefined : selectedDocument,
      sessionId: selectedSession || undefined,
      useRag,
    });
  };

  const handleCreateSession = () => {
    if (!selectedDocument || selectedDocument === 'all') {
      toast.error('Select a document', {
        description: 'Please select a document before creating a session.',
      });
      return;
    }
    createSessionMutation.mutate({
      documentId: selectedDocument,
      name: sessionName.trim() || undefined,
    });
  };

  const currentSession = sessions?.find(s => s.id === selectedSession);

  return (
    <div className="h-[calc(100vh-8rem)] flex">
      {/* Sidebar */}
      <div className="w-80 bg-background border-r flex flex-col">
        <div className="p-4 border-b">
          <div className="mb-4">
            <Label className="mb-1">
              Document
            </Label>
            <Select
              value={selectedDocument}
              onValueChange={(value) => {
                setSelectedDocument(value);
                setSelectedSession('');
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a document" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All documents</SelectItem>
                {processedDocuments.map((doc) => (
                  <SelectItem key={doc.id} value={doc.id}>
                    {doc.original_filename || doc.filename}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {isCreatingSession ? (
            <div className="space-y-2">
              <Input
                type="text"
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
                placeholder="Session name (optional)"
                autoFocus
              />
              <div className="flex space-x-2">
                <Button
                  onClick={handleCreateSession}
                  disabled={!selectedDocument || selectedDocument === 'all' || createSessionMutation.isPending}
                  className="flex-1"
                  size="sm"
                >
                  {createSessionMutation.isPending ? 'Creating...' : 'Create'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setIsCreatingSession(false);
                    setSessionName('');
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <Button
              variant="outline"
              className="w-full"
              size="sm"
              onClick={() => setIsCreatingSession(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              New Session
            </Button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          {documentSessions.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground text-sm">
              No chat sessions yet
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {documentSessions.map((session) => (
                <Button
                  key={session.id}
                  variant={selectedSession === session.id ? "secondary" : "ghost"}
                  className="w-full justify-start h-auto p-3"
                  onClick={() => setSelectedSession(session.id)}
                >
                  <div className="w-full text-left">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm">
                        {session.session_name || 'Untitled Session'}
                      </span>
                      <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {session.message_count} messages • {formatRelativeTime(session.last_activity)}
                    </div>
                  </div>
                </Button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedSession ? (
          <>
            {/* Chat Header */}
            <div className="bg-background border-b px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">
                    {currentSession?.session_name || 'Chat Session'}
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    {currentSession && formatDate(currentSession.created_at)}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="use-rag"
                    checked={useRag}
                    onCheckedChange={(checked) => setUseRag(checked as boolean)}
                  />
                  <Label htmlFor="use-rag" className="text-sm cursor-pointer">
                    Use RAG
                  </Label>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto bg-secondary/30 px-6 py-4">
              {messages && messages.length > 0 ? (
                <div className="space-y-4 max-w-4xl mx-auto">
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`flex items-start space-x-2 max-w-[80%] ${
                        msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                      }`}>
                        <div className={`p-2 rounded-full ${
                          msg.role === 'user' ? 'bg-primary' : 'bg-muted'
                        }`}>
                          {msg.role === 'user' ? (
                            <User className="h-4 w-4 text-primary-foreground" />
                          ) : (
                            <Bot className="h-4 w-4 text-foreground" />
                          )}
                        </div>
                        <Card className={msg.role === 'user' ? 'bg-primary text-primary-foreground' : ''}>
                          <CardContent className="p-4">
                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                            <p className={`text-xs mt-1 ${
                              msg.role === 'user' ? 'opacity-80' : 'text-muted-foreground'
                            }`}>
                              {formatRelativeTime(msg.created_at)}
                            </p>
                          </CardContent>
                        </Card>
                      </div>
                    </div>
                  ))}
                  {sendMessageMutation.isPending && (
                    <div className="flex justify-start">
                      <div className="flex items-start space-x-2 max-w-[80%]">
                        <div className="p-2 rounded-full bg-muted">
                          <Bot className="h-4 w-4 text-foreground" />
                        </div>
                        <Card>
                          <CardContent className="p-4">
                            <Loader2 className="h-4 w-4 animate-spin" />
                          </CardContent>
                        </Card>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-lg font-medium">Start a conversation</p>
                    <p className="text-sm text-muted-foreground mt-2">
                      Ask questions about your document
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Message Input */}
            <div className="bg-background border-t px-6 py-4">
              <form onSubmit={handleSendMessage} className="flex space-x-2">
                <Input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type your message..."
                  disabled={sendMessageMutation.isPending}
                  className="flex-1"
                />
                <Button
                  type="submit"
                  disabled={!message.trim() || sendMessageMutation.isPending}
                  size="icon"
                >
                  {sendMessageMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-secondary/30">
            <div className="text-center">
              <MessageSquare className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No session selected</h3>
              <p className="text-muted-foreground mb-4">
                Select an existing session or create a new one to start chatting
              </p>
              {selectedDocument && selectedDocument !== 'all' && (
                <Button
                  onClick={() => setIsCreatingSession(true)}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create New Session
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-screen"><Loader2 className="h-8 w-8 animate-spin" /></div>}>
      <ChatContent />
    </Suspense>
  );
}