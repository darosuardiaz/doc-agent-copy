'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Activity, Database, Brain, MessageSquare, HardDrive, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { formatDate } from '@/lib/utils';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'];

export default function SystemPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['system-stats'],
    queryFn: () => apiClient.getSystemStats(),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiClient.getSystemHealth(),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  if (statsLoading || healthLoading) {
    return (
      <div className="space-y-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">System Monitoring</h1>
          <p className="text-muted-foreground">Monitor system health and performance metrics</p>
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-48" />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          </CardContent>
        </Card>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-4 w-24 mb-2" />
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const documentChartData = stats ? [
    { name: 'Processed', value: stats.documents.processed },
    { name: 'Processing', value: stats.documents.total - stats.documents.processed },
  ] : [];

  const researchChartData = stats ? [
    { name: 'Completed', value: stats.research.completed_tasks },
    { name: 'Pending', value: stats.research.total_tasks - stats.research.completed_tasks },
  ] : [];

  const metricsData = stats ? [
    { name: 'Documents', value: stats.documents.total },
    { name: 'Sessions', value: stats.chat.total_sessions },
    { name: 'Research', value: stats.research.total_tasks },
    { name: 'Vectors', value: Math.round(stats.vector_store.total_vectors / 1000) },
  ] : [];

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">System Monitoring</h1>
        <p className="text-muted-foreground">Monitor system health and performance metrics</p>
      </div>

      {/* Health Status */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>System Health</CardTitle>
            <Badge variant={health?.status === 'healthy' ? 'default' : 'destructive'}>
              {health?.status === 'healthy' ? (
                <CheckCircle className="h-3 w-3 mr-1" />
              ) : (
                <AlertCircle className="h-3 w-3 mr-1" />
              )}
              {health?.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
        
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {health?.services && Object.entries(health.services).map(([service, status]) => (
              <div key={service} className="flex items-center justify-between p-4 bg-secondary rounded-lg">
                <div className="flex items-center space-x-3">
                  {service === 'database' && <Database className="h-5 w-5 text-muted-foreground" />}
                  {service === 'openai' && <Brain className="h-5 w-5 text-muted-foreground" />}
                  {service === 'pinecone' && <HardDrive className="h-5 w-5 text-muted-foreground" />}
                  <span className="font-medium capitalize">{service}</span>
                </div>
                <Badge variant={status === 'connected' || status === 'configured' ? 'default' : 'destructive'}>
                  {status}
                </Badge>
              </div>
            ))}
          </div>
        
          {health && (
            <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
              <span>Version: {health.version}</span>
              <span>Last updated: {formatDate(health.timestamp)}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-muted-foreground">Documents</span>
              <Activity className="h-5 w-5 text-primary" />
            </div>
            <p className="text-2xl font-bold">{stats?.documents.total || 0}</p>
            <p className="text-sm text-muted-foreground mt-1">
              {stats?.documents.processing_rate} processed
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-muted-foreground">Chat Sessions</span>
              <MessageSquare className="h-5 w-5 text-green-600" />
            </div>
            <p className="text-2xl font-bold">{stats?.chat.total_sessions || 0}</p>
            <p className="text-sm text-muted-foreground mt-1">
              {stats?.chat.active_sessions} active
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-muted-foreground">Research Tasks</span>
              <Brain className="h-5 w-5 text-purple-600" />
            </div>
            <p className="text-2xl font-bold">{stats?.research.total_tasks || 0}</p>
            <p className="text-sm text-muted-foreground mt-1">
              {stats?.research.completion_rate} completed
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-muted-foreground">Vector Store</span>
              <HardDrive className="h-5 w-5 text-amber-600" />
            </div>
            <p className="text-2xl font-bold">
              {stats?.vector_store.total_vectors.toLocaleString() || 0}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              {((stats?.vector_store.index_fullness || 0) * 100).toFixed(1)}% full
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Document Processing Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Document Processing</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {documentChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={documentChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }: any) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {documentChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground">
                  No data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Research Tasks Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Research Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {researchChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={researchChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }: any) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {researchChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground">
                  No data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity Overview */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Activity Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            {metricsData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={metricsData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                No data available
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Vector Store Details */}
      {stats?.vector_store && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Vector Store Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <span className="text-muted-foreground text-sm">Total Vectors</span>
                <p className="font-medium">{stats.vector_store.total_vectors.toLocaleString()}</p>
              </div>
              <div>
                <span className="text-muted-foreground text-sm">Dimension</span>
                <p className="font-medium">{stats.vector_store.dimension}</p>
              </div>
              <div>
                <span className="text-muted-foreground text-sm">Index Fullness</span>
                <p className="font-medium">{(stats.vector_store.index_fullness * 100).toFixed(2)}%</p>
              </div>
              <div>
                <span className="text-muted-foreground text-sm">Avg per Document</span>
                <p className="font-medium">
                  {stats.documents.embedded > 0 
                    ? Math.round(stats.vector_store.total_vectors / stats.documents.embedded)
                    : 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}