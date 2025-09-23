"""
FastAPI main application for the AI-powered financial document processing system.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routes import router
from app.database.connection import init_database
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting AI Financial Document Processing System")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        logger.info("Database initialized successfully")
        
        # Ensure upload directory exists
        if not os.path.exists(settings.UPLOAD_DIRECTORY):
            os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
            logger.info(f"Created upload directory: {settings.UPLOAD_DIRECTORY}")
        
        # Test API connections (optional)
        logger.info("Testing external service connections...")
        
        # Test OpenAI (optional - just log configuration)
        if settings.OPENAI_API_KEY:
            logger.info("OpenAI API key configured")
        else:
            logger.warning("OpenAI API key not configured")
        
        # Test Pinecone (optional)
        if settings.PINECONE_API_KEY:
            logger.info("Pinecone API key configured")
        else:
            logger.warning("Pinecone API key not configured")
        
        logger.info("System startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise e
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Financial Document Processing System")


# Create FastAPI application
app = FastAPI(
    title="AI Financial Document Processing System",
    description="""
    An AI-powered system for uploading, processing, and researching financial documents.
    
    ## Features
    
    * **Document Upload & Processing**: Upload PDFs and extract structured content using docling
    * **AI-Powered Analysis**: Extract financial facts, investment data, and key metrics
    * **Vector Search**: Store document embeddings in Pinecone for semantic search
    * **Deep Research Agent**: Generate comprehensive content outlines and analysis
    * **Chat/RAG Agent**: Interactive chat with document context and retrieval-augmented generation
    
    ## Workflow
    
    1. Upload a financial document (PDF)
    2. System processes the document with docling
    3. Content is embedded and stored in Pinecone
    4. Metadata and financial facts are extracted
    5. Use the research agent to generate detailed analysis
    6. Chat with the document using the RAG-enabled chat agent
    
    ## Technology Stack
    
    * **Framework**: FastAPI + LangGraph
    * **Document Processing**: docling
    * **Vector Store**: Pinecone
    * **LLM**: OpenAI GPT-4
    * **Database**: PostgreSQL
    """,
    version="1.0.0",
    contact={
        "name": "AI Financial Document Processing Team",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirects to documentation."""
    return RedirectResponse(url="/docs")


@app.get("/api", include_in_schema=False)
async def api_root():
    """API root endpoint."""
    return {
        "message": "AI Financial Document Processing System API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/system/health",
        "endpoints": {
            "documents": "/documents",
            "research": "/research",
            "chat": "/chat",
            "system": "/system"
        }
    }


# Custom exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return HTTPException(
        status_code=500,
        detail="An internal error occurred. Please try again later."
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )