# Financial Document Processing System

A comprehensive AI system for uploading, processing, and researching financial documents using advanced language models and vector search capabilities.

## Features

### Core Functionality
- **Document Upload & Processing**: Upload PDFs and extract structured content using docling
- **AI-Powered Analysis**: Extract financial facts, investment data, and key metrics using OpenAI GPT-4
- **Vector Search**: Store document embeddings in Pinecone for semantic search and retrieval
- **Deep Research Agent**: Generate comprehensive content outlines and analysis using LangGraph
- **Chat/RAG Agent**: Interactive chat with document context and retrieval-augmented generation

### Technical Highlights
- **LangGraph Agents**: Two specialized agents for research and chat functionality
- **Pinecone Integration**: Vector database for efficient semantic search
- **PostgreSQL**: Metadata storage and chat session management
- **FastAPI**: RESTful API with automatic documentation
- **Docling**: Advanced document parsing for financial documents

## 📋 System Requirements
- Python 3.11+
- Node.js 18+
- pnpm (recommended) or npm
- PostgreSQL 15+ (or set `DATABASE_URL` to SQLite for local only)
- OpenAI API Key
- Pinecone API Key

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd doc-agent
```

### 2. Set Up Environment Variables
Create a `.env` file in the project root and configure your keys and settings. These variables are required for both local runs and Docker.

```env
# Database Configuration
# Use Postgres (recommended) or SQLite for local only
DATABASE_URL=postgresql://doc_agent:doc_agent_password@localhost:5432/financial_docs
# Example SQLite (for quick local runs):
# DATABASE_URL=sqlite:///./test_doc_processing.db

# OpenAI Configuration (required)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-1106-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Pinecone Configuration (required)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=financial-documents
PINECONE_DIMENSION=1536

# LangSmith (required for current configuration)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=doc-agent
LANGSMITH_TRACING=true

# Application Configuration
DEBUG=false
UPLOAD_DIRECTORY=/tmp/uploads
```

### 3. Set Up Database
Make sure PostgreSQL is running and create the database:

```bash
createdb financial_docs
```

The application will automatically create the required tables on startup.

## Running From Source (Full Stack)

### 1) Backend
- Create and activate a virtual environment (optional but recommended)
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  ```
- Install dependencies
  ```bash
  pip install -r requirements.txt
  ```
- Ensure your database is running and `DATABASE_URL` is set in `.env`
- Start the API
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```

### 2) Frontend
- In a new terminal, install dependencies and start the dev server
  ```bash
  cd client
  pnpm install
  # Ensure the API URL points to your backend
  echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
  pnpm dev
  ```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000` (docs at `/docs`)

Tip: To run the backend against SQLite for quick local testing, set `DATABASE_URL=sqlite:///./test_doc_processing.db` in `.env`.

## Run with Docker and Makefile 🐳 

This project includes a Makefile and Compose setup for easy Docker-based runs.

### Prerequisites
- Docker and Docker Compose
- A `.env` file in the project root with the variables shown above

### Quick start (development, with hot reload)
```bash
make dev
```
Services:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000` (health at `/health`, docs at `/docs`)
- Postgres: `localhost:5432` (credentials set in `docker-compose.yml`)

### Production-like run
```bash
make build
make start
```

### Useful commands
```bash
make help         # list available commands
make logs         # tail logs for all services
make logs-backend # tail backend logs
make logs-frontend# tail frontend logs
make status       # service status and resource usage
make health       # quick health checks for services
make stop         # stop all services
make clean        # stop and remove volumes (DANGER: deletes data)
```

### Without make
```bash
# Development (hot reload)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production-like
docker-compose up -d --build
```

Notes:
- Compose reads your root `.env` for required keys (`OPENAI_API_KEY`, `PINECONE_API_KEY`, `LANGSMITH_API_KEY`, etc.).
- Uploads are persisted to the local `./uploads` directory.

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   LangGraph      │    │   PostgreSQL    │
│   Web Server    │────│   Agents         │────│   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Docling       │    │   OpenAI         │    │   Pinecone      │
│   Parser        │    │   LLM            │    │   Vector Store  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Agent Architecture

#### Deep Research Agent
The Deep Research Agent uses a multi-step workflow:

1. **Topic Analysis**: Understand research requirements
2. **Question Generation**: Create specific research questions
3. **Information Retrieval**: Search document embeddings
4. **Content Outline**: Structure findings into organized outline
5. **Detailed Content**: Generate comprehensive content for each section

#### Chat/RAG Agent
The Chat Agent provides conversational interaction:

1. **Context Loading**: Load chat history and session context
2. **Retrieval Decision**: Determine if RAG is needed
3. **Information Retrieval**: Search relevant document chunks
4. **Response Generation**: Generate contextual response
5. **Conversation Storage**: Save interaction history

### Data Models

#### Documents
- Document metadata and processing status
- Financial facts and investment data
- File information and processing timestamps

#### Chat Sessions
- Session configuration and user context
- Message history and conversation state
- RAG context and retrieval settings

#### Research Tasks
- Research topics and custom queries
- Generated content outlines and findings
- Source citations and processing metadata

## 📚 API Documentation

The system provides interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔍 Example Workflow

### Complete Document Analysis Workflow

1. **Upload Document**
   ```bash
   curl -X POST "http://localhost:8000/upload" \
        -F "file=@cim_document.pdf"
   ```

2. **Wait for Processing**
   ```bash
   curl "http://localhost:8000/documents/{document_id}/status"
   ```

3. **Conduct Research**
   ```bash
   curl -X POST "http://localhost:8000/documents/{document_id}/research/start" \
        -H "Content-Type: application/json" \
        -d '{"topic": "Investment Highlights"}'
   ```

4. **Start Chat Session**
   ```bash
   curl -X POST "http://localhost:8000/conversation/new" \
        -H "Content-Type: application/json" \
        -d '{"document_id": "{document_id}"}'
   ```

5. **Ask Questions**
   ```bash
   curl -X POST "http://localhost:8000/conversation" \
        -H "Content-Type: application/json" \
        -d '{"message": "What are the key risks?", "session_id": "{session_id}"}'
   ```

## 📊 Monitoring

### System Statistics

Get system statistics:
```bash
curl "http://localhost:8000/system/stats"
```

Response:
```json
{
  "documents": {
    "total": 15,
    "processed": 14,
    "embedded": 12,
    "processing_rate": "93.3%"
  },
  "chat": {
    "total_sessions": 8,
    "active_sessions": 3
  },
  "research": {
    "total_tasks": 23,
    "completed_tasks": 21,
    "completion_rate": "91.3%"
  },
  "vector_store": {
    "total_vectors": 1247,
    "dimension": 3072,
    "index_fullness": 0.02
  },
  "system": {
    "uptime": "N/A",
    "timestamp": "2024-01-15T11:45:00Z"
  }
}
```

### Health Check

Check system health:
```bash
curl "http://localhost:8000/system/health"
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T11:45:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "openai": "configured",
    "pinecone": "configured"
  }
}
```

## 🔐 Security Considerations

- Environment variables for sensitive configuration
- File upload validation and size limits
- Input sanitization for chat messages
- Database connection security
- API rate limiting (to be implemented)

## 🎯 Future Enhancements

- [ ] User authentication and authorization
- [ ] Document comparison and analysis
- [ ] Batch document processing
- [ ] Advanced search filters
- [ ] Export functionality for research reports
- [ ] WebSocket support for real-time updates
- [ ] Advanced monitoring and metrics