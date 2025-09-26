import { FileText, ExternalLink } from 'lucide-react';

interface Source {
  chunk_id?: string;
  page_number?: number;
  similarity_score?: number;
  preview?: string;
}

interface MessageSourcesProps {
  sources: Source[];
}

export function MessageSources({ sources }: MessageSourcesProps) {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-center space-x-2 mb-2">
        <FileText className="h-4 w-4 text-gray-500" />
        <span className="text-sm font-medium text-gray-700">Sources Used</span>
      </div>
      <div className="space-y-2">
        {sources.map((source, index) => (
          <div key={source.chunk_id || index} className="text-sm relative group">
            <div className="flex items-start space-x-2 cursor-pointer">
              <ExternalLink className="h-3 w-3 text-gray-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="flex items-center space-x-2 text-xs text-gray-600">
                  {source.page_number && (
                    <span>Page {source.page_number}</span>
                  )}
                  {source.similarity_score && (
                    <span className="text-gray-400">•</span>
                  )}
                  {source.similarity_score && (
                    <span>Score: {(source.similarity_score * 100).toFixed(0)}%</span>
                  )}
                </div>
              </div>
            </div>
            {source.preview && (
              <div className="absolute left-0 top-full mt-1 z-10 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 delay-300">
                <div className="bg-gray-900 text-white text-xs rounded-lg p-3 shadow-lg max-w-xs min-w-48 relative">
                  <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-900 rotate-45"></div>
                  <p className="leading-relaxed">
                    {source.preview}
                  </p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}