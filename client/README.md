# Financial Document AI - Client Application

This is the Next.js frontend application for the Financial Document AI system. It provides a modern, responsive interface for uploading, processing, and analyzing financial documents using AI.

## Features

- **Document Management**: Upload, view, and manage PDF documents
- **AI-Powered Research**: Generate comprehensive research and analysis
- **Interactive Chat**: Ask questions about documents with RAG support
- **System Monitoring**: Real-time health checks and performance metrics
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

## Installation

1. Navigate to the client directory:
```bash
cd client
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment:
```bash
# Create .env.local file if it doesn't exist
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

## Development

Run the development server:

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

## Building for Production

```bash
# Build the application
npm run build

# Run production server
npm start
```

## Application Structure

```
client/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Home/Documents page
│   ├── upload/            # Document upload page
│   ├── documents/[id]/    # Document details page
│   ├── research/          # Research interface
│   ├── chat/              # Chat interface
│   └── system/            # System monitoring
├── components/            # Reusable components
│   ├── navigation.tsx     # Main navigation
│   └── ui/               # UI components
├── lib/                   # Utilities and services
│   ├── api-client.ts     # API client service
│   └── utils.ts          # Helper functions
└── public/               # Static assets
```

## Key Features

### Document Upload
- Drag-and-drop or click to upload PDF files
- Real-time upload progress
- Automatic document processing
- File size validation (max 50MB)

### Document Management
- List all uploaded documents
- View processing status
- Access document details including:
  - Financial facts
  - Investment data
  - Key metrics
  - Processing statistics

### Deep Research
- Create research tasks on processed documents
- Define custom research topics and queries
- View comprehensive content outlines
- Access source citations with relevance scores
- Track research task progress in real-time

### Chat Interface
- Create multiple chat sessions per document
- Toggle RAG (Retrieval-Augmented Generation) support
- View conversation history
- Real-time message streaming
- Session management

### System Monitoring
- Real-time health status
- Service connectivity checks
- Performance metrics visualization
- Document processing statistics
- Vector store utilization

## Technologies Used

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **React Query**: Data fetching and caching
- **Recharts**: Data visualization
- **Radix UI**: Accessible UI components
- **Lucide Icons**: Modern icon set

## API Integration

The client communicates with the backend API through the `api-client.ts` service, which provides:

- Centralized error handling
- Type-safe API methods
- Automatic retries and caching (via React Query)
- Mock data fallbacks for missing endpoints

## Error Handling

The application includes comprehensive error handling:

- API error boundaries
- Loading states for all async operations
- User-friendly error messages
- Toast notifications for user feedback
- Graceful degradation for missing endpoints

## Contributing

1. Follow the existing code style
2. Add proper TypeScript types
3. Update tests for new features
4. Ensure responsive design
5. Test error scenarios

## License

MIT License - see the main project README for details.