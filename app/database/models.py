"""
SQLAlchemy models for the financial document processing system.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid


Base = declarative_base()


class Document(Base):
    """Model for storing document metadata and information."""
    
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # File size in bytes
    mime_type = Column(String(100), nullable=False)
    
    # Document content metadata
    page_count = Column(Integer)
    word_count = Column(Integer)
    
    # Financial metadata (extracted from document)
    financial_facts = Column(JSON)  # Store structured financial data
    investment_data = Column(JSON)  # Store investment-related information
    key_metrics = Column(JSON)      # Store key financial metrics
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    is_embedded = Column(Boolean, default=False)
    processing_error = Column(Text)
    
    # Pinecone integration
    pinecone_namespace = Column(String(100))  # Namespace in Pinecone
    embedding_count = Column(Integer, default=0)  # Number of chunks embedded
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="document")
    document_chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    """Model for storing individual document chunks and their embeddings."""
    
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Chunk content and metadata
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    page_number = Column(Integer)
    
    # Embedding information
    pinecone_id = Column(String(100))  # ID in Pinecone vector store
    embedding_model = Column(String(100))  # Model used for embedding
    
    # Chunk metadata
    token_count = Column(Integer)
    char_count = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="document_chunks")


class ChatSession(Base):
    """Model for storing chat sessions and their context."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    
    # Session metadata
    session_name = Column(String(255))
    user_id = Column(String(100))  # For future user management
    
    # Session configuration
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    system_prompt = Column(Text)
    
    # Session status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    """Model for storing individual chat messages."""
    
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    
    # Message metadata
    token_count = Column(Integer)
    model_used = Column(String(100))
    response_time = Column(Float)  # Response time in seconds
    
    # RAG context (for assistant messages)
    retrieved_chunks = Column(JSON)  # Chunks used for context
    similarity_scores = Column(JSON)  # Similarity scores for retrieved chunks
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class ResearchTask(Base):
    """Model for storing deep research tasks and their results."""
    
    __tablename__ = "research_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Task details
    topic = Column(String(500), nullable=False)  # e.g., "Key Investment Highlights"
    research_query = Column(Text, nullable=False)
    
    # Task status
    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed
    
    # Results
    content_outline = Column(JSON)  # Generated content outline
    research_findings = Column(JSON)  # Detailed research findings
    sources_used = Column(JSON)  # Sources and chunks referenced
    
    # Task metadata
    processing_time = Column(Float)  # Time taken in seconds
    model_used = Column(String(100))
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    document = relationship("Document")


def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)