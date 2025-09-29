# AI-Powered Financial Document Processing System

A comprehensive AI system for uploading, processing, and researching financial documents using advanced language models and vector search capabilities.

## 🚀 Features

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

- Python 3.8+
- PostgreSQL 12+
- OpenAI API Key
- Pinecone API Key

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd doc-agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
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

### 4. Set Up Database
Make sure PostgreSQL is running and create the database:

```bash
createdb financial_docs
```

The application will automatically create the required tables on startup.

### 5. Run the Application
```bash
python -m app.main
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## 🧑‍💻 Running From Source (Full Stack)

This runs the backend (FastAPI) and frontend (Next.js) locally.

### Prerequisites
- Python 3.11+
- Node.js 18+
- pnpm (recommended) or npm
- PostgreSQL 15+ (or set `DATABASE_URL` to SQLite for local only)

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

## 🐳 Run with Docker and Makefile

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

## 🔧 API Usage

### Document Management

#### Upload Document
```bash
curl -X POST "http://localhost:8000/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@financial_report.pdf"
```

Response:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "financial_report.pdf",
  "file_size": 1024000,
  "status": "uploaded",
  "processing_started": true
}
```

#### Check Processing Status
```bash
curl -X GET "http://localhost:8000/documents/{document_id}/status"
```

Response:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "financial_report.pdf",
  "is_processed": true,
  "is_embedded": true,
  "processing_error": null,
  "embedding_count": 127,
  "progress_percentage": 100
}
```

#### List Documents
```bash
curl -X GET "http://localhost:8000/documents"
```

Response:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "filename": "financial_report.pdf",
    "original_filename": "Q3_Financial_Report.pdf",
    "file_size": 1024000,
    "is_processed": true,
    "is_embedded": true,
    "created_at": "2024-01-15T10:30:00Z",
    "page_count": 45,
    "word_count": 12500
  },
  {
    "id": "456e7890-e12b-34c5-d678-901234567890",
    "filename": "investment_memo.pdf",
    "original_filename": "Investment_Memo_CompanyXYZ.pdf",
    "file_size": 756000,
    "is_processed": true,
    "is_embedded": false,
    "created_at": "2024-01-14T14:20:00Z",
    "page_count": 32,
    "word_count": 8900
  }
]
```

#### Get Document Details
```bash
curl -X GET "http://localhost:8000/documents/{document_id}"
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "financial_report.pdf",
  "original_filename": "Q3_Financial_Report.pdf",
  "file_path": "/tmp/uploads/123e4567-e89b-12d3-a456-426614174000.pdf",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "page_count": 45,
  "word_count": 12500,
  "financial_facts": {
    "revenue": "$150M",
    "growth_rate": "25%",
    "market_cap": "$2.5B"
  },
  "investment_data": {
    "sector": "fintech",
    "stage": "Series C",
    "valuation": "$500M"
  },
  "key_metrics": {
    "customer_count": 150000,
    "arr": "$120M",
    "churn_rate": "2.1%"
  },
  "is_processed": true,
  "is_embedded": true,
  "processing_error": null,
  "pinecone_namespace": "doc_123e4567",
  "embedding_count": 127,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:32:45Z"
}
```

#### Delete Document
```bash
curl -X DELETE "http://localhost:8000/documents/{document_id}"
```

Response:
```json
{
  "message": "Document deleted successfully"
}
```

### Deep Research

#### Start Research Task
```bash
curl -X POST "http://localhost:8000/documents/{document_id}/research/start" \
     -H "Content-Type: application/json" \
     -d '{
       "topic": "Key Investment Highlights",
       "custom_query": "What are the main investment opportunities and risks?"
     }'
```

Response:
```json
{
  "task_id": "456e7890-e12b-34c5-d678-901234567890",
  "content_outline": {
    "1": {
      "title": "Executive Summary",
      "description": "Overview of key investment opportunities"
    },
    "2": {
      "title": "Market Analysis",
      "description": "Current market conditions and trends"
    },
    "3": {
      "title": "Financial Performance",
      "description": "Revenue, profitability, and growth metrics"
    },
    "4": {
      "title": "Risk Assessment",
      "description": "Identified risks and mitigation strategies"
    }
  },
  "research_findings": {
    "1": {
      "content": "The company shows strong fundamentals with 25% YoY revenue growth and expanding market share in the fintech sector...",
      "key_points": ["Strong revenue growth", "Market leadership", "Innovative technology stack"]
    },
    "2": {
      "content": "Market analysis reveals favorable conditions with increasing demand for digital financial services...",
      "key_points": ["Growing market", "Regulatory support", "Competitive positioning"]
    }
  },
  "sources_used": [
    {
      "page": 5,
      "content": "Revenue increased 25% year-over-year to $150M",
      "relevance_score": 0.95
    },
    {
      "page": 12,
      "content": "Market opportunity estimated at $2.5B by 2025",
      "relevance_score": 0.88
    }
  ],
  "processing_time": 45.2
}
```

#### Get Research Results
```bash
curl -X GET "http://localhost:8000/documents/{document_id}/research/tasks/{task_id}"
```

Response:
```json
{
  "id": "456e7890-e12b-34c5-d678-901234567890",
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "topic": "Key Investment Highlights",
  "custom_query": "What are the main investment opportunities and risks?",
  "status": "completed",
  "content_outline": {
    "1": {
      "title": "Executive Summary",
      "description": "Overview of key investment opportunities"
    }
  },
  "research_findings": {
    "1": {
      "content": "The company shows strong fundamentals...",
      "key_points": ["Strong revenue growth", "Market leadership"]
    }
  },
  "sources_used": [
    {
      "page": 5,
      "content": "Revenue increased 25% year-over-year",
      "relevance_score": 0.95
    }
  ],
  "created_at": "2024-01-15T11:00:00Z",
  "completed_at": "2024-01-15T11:02:30Z",
  "processing_time": 45.2
}
```

#### List Research Tasks
```bash
curl -X GET "http://localhost:8000/documents/{document_id}/research/tasks"
```

Response:
```json
[
  {
    "id": "456e7890-e12b-34c5-d678-901234567890",
    "document_id": "123e4567-e89b-12d3-a456-426614174000",
    "topic": "Key Investment Highlights",
    "status": "completed",
    "created_at": "2024-01-15T11:00:00Z",
    "completed_at": "2024-01-15T11:02:30Z",
    "processing_time": 45.2
  },
  {
    "id": "789e0123-e45f-67g8-h901-234567890123",
    "document_id": "123e4567-e89b-12d3-a456-426614174000",
    "topic": "Risk Analysis",
    "status": "in_progress",
    "created_at": "2024-01-15T11:15:00Z",
    "completed_at": null,
    "processing_time": null
  }
]
```

### Chat Interface

#### Send Message
```bash
curl -X POST "http://localhost:8000/conversation" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What is the company revenue?",
       "document_id": "123e4567-e89b-12d3-a456-426614174000",
       "use_rag": true
     }'
```

Response:
```json
{
  "message": "Based on the financial report, the company's revenue for the fiscal year was $150 million, representing a 25% increase compared to the previous year. This growth was driven primarily by expansion in the fintech sector and increased market penetration.",
  "session_id": "789e0123-e45f-67g8-h901-234567890123",
  "sources_used": [
    {
      "page": 5,
      "content": "Total revenue for FY2024: $150M (25% YoY growth)",
      "relevance_score": 0.96
    },
    {
      "page": 8,
      "content": "Revenue growth attributed to fintech expansion",
      "relevance_score": 0.89
    }
  ],
  "response_time": 1.8,
  "token_count": 156
}
```

#### Create Chat Session
```bash
curl -X POST "http://localhost:8000/conversation/new" \
     -H "Content-Type: application/json" \
     -d '{
       "document_id": "123e4567-e89b-12d3-a456-426614174000",
       "session_name": "Financial Analysis Session"
     }'
```

Response:
```json
{
  "id": "789e0123-e45f-67g8-h901-234567890123",
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "session_name": "Financial Analysis Session",
  "user_id": null,
  "is_active": true,
  "created_at": "2024-01-15T11:30:00Z",
  "last_activity": "2024-01-15T11:30:00Z",
  "message_count": 0,
  "temperature": 0.7,
  "max_tokens": 1000,
  "system_prompt": null
}
```

#### List Chat Sessions
```bash
curl -X GET "http://localhost:8000/conversation/sessions"
```

Response:
```json
[
  {
    "id": "789e0123-e45f-67g8-h901-234567890123",
    "document_id": "123e4567-e89b-12d3-a456-426614174000",
    "session_name": "Financial Analysis Session",
    "user_id": null,
    "is_active": true,
    "created_at": "2024-01-15T11:30:00Z",
    "last_activity": "2024-01-15T11:35:20Z",
    "message_count": 5
  },
  {
    "id": "abc1234d-e56f-78g9-h012-345678901234",
    "document_id": "456e7890-e12b-34c5-d678-901234567890",
    "session_name": "Investment Memo Discussion",
    "user_id": null,
    "is_active": true,
    "created_at": "2024-01-15T10:45:00Z",
    "last_activity": "2024-01-15T11:20:15Z",
    "message_count": 12
  }
]
```

#### Get Chat History
```bash
curl -X GET "http://localhost:8000/conversation/{session_id}/history"
```

Response:
```json
[
  {
    "id": "msg_001",
    "session_id": "789e0123-e45f-67g8-h901-234567890123",
    "role": "user",
    "content": "What is the company revenue?",
    "created_at": "2024-01-15T11:32:00Z",
    "token_count": 7
  },
  {
    "id": "msg_002",
    "session_id": "789e0123-e45f-67g8-h901-234567890123",
    "role": "assistant",
    "content": "Based on the financial report, the company's revenue for the fiscal year was $150 million, representing a 25% increase compared to the previous year.",
    "created_at": "2024-01-15T11:32:02Z",
    "token_count": 156
  },
  {
    "id": "msg_003",
    "session_id": "789e0123-e45f-67g8-h901-234567890123",
    "role": "user",
    "content": "What were the main drivers of this growth?",
    "created_at": "2024-01-15T11:33:15Z",
    "token_count": 10
  }
]
```

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

## 🧪 Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run specific test categories:

```bash
# Unit tests only
pytest tests/test_basic.py::TestUtilityHelpers -v

# API tests only
pytest tests/test_basic.py::TestAPIEndpoints -v
```

Note: Integration tests require actual API keys and database setup.

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

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `PINECONE_API_KEY` | Pinecone API key | Required |
| `PINECONE_INDEX_NAME` | Pinecone index name | `financial-documents` |
| `DEBUG` | Enable debug mode | `false` |
| `MAX_FILE_SIZE` | Maximum upload size (bytes) | `52428800` (50MB) |
| `UPLOAD_DIRECTORY` | File upload directory | `/tmp/uploads` |

### Model Configuration

The system uses the following AI models:
- **LLM**: `gpt-4-1106-preview` (configurable via `OPENAI_MODEL`)
- **Embeddings**: `text-embedding-3-large` (configurable via `OPENAI_EMBEDDING_MODEL`)

## 🚨 Error Handling

The system includes comprehensive error handling:

- **File Upload Errors**: Size limits, format validation
- **Processing Errors**: Document parsing failures
- **API Errors**: Rate limiting, authentication issues
- **Database Errors**: Connection issues, constraint violations

All errors are logged and returned with appropriate HTTP status codes.

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:

1. Check the API documentation at `/docs`
2. Review the error logs
3. Check system status at `/system/health`
4. Open an issue on GitHub

## 🎯 Future Enhancements

- [ ] User authentication and authorization
- [ ] Document comparison and analysis
- [ ] Batch document processing
- [ ] Advanced search filters
- [ ] Export functionality for research reports
- [ ] WebSocket support for real-time updates
- [ ] Docker deployment configuration
- [ ] Kubernetes manifests
- [ ] Advanced monitoring and metrics