"""
Basic tests for the AI-powered financial document processing system.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.utils.helpers import (
    format_file_size, 
    normalize_financial_value, 
    calculate_text_similarity,
    validate_uuid
)


# Test client
client = TestClient(app)


class TestUtilityHelpers:
    """Test utility helper functions."""
    
    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(0) == "0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
    
    def test_normalize_financial_value(self):
        """Test financial value normalization."""
        assert normalize_financial_value("1000") == 1000.0
        assert normalize_financial_value("1,000") == 1000.0
        assert normalize_financial_value("1.5", "million") == 1500000.0
        assert normalize_financial_value("2", "billion") == 2000000000.0
        assert normalize_financial_value("invalid") is None
    
    def test_calculate_text_similarity(self):
        """Test text similarity calculation."""
        assert calculate_text_similarity("hello world", "hello world") == 1.0
        assert calculate_text_similarity("hello", "world") == 0.0
        assert calculate_text_similarity("", "") == 0.0
        
        # Test partial similarity
        similarity = calculate_text_similarity("hello world test", "hello world example")
        assert 0 < similarity < 1
    
    def test_validate_uuid(self):
        """Test UUID validation."""
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        invalid_uuid = "not-a-uuid"
        
        assert validate_uuid(valid_uuid) == True
        assert validate_uuid(invalid_uuid) == False


class TestAPIEndpoints:
    """Test API endpoints."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
    
    def test_api_root(self):
        """Test API root endpoint."""
        response = client.get("/api")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_list_documents_empty(self):
        """Test listing documents when none exist."""
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_nonexistent_document(self):
        """Test getting a document that doesn't exist."""
        fake_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.get(f"/api/v1/documents/{fake_id}")
        assert response.status_code == 404
    
    def test_invalid_document_id(self):
        """Test with invalid document ID format."""
        response = client.get("/api/v1/documents/invalid-id")
        assert response.status_code == 400


class TestDocumentProcessing:
    """Test document processing functionality."""
    
    @patch('app.services.document_processor.DocumentConverter')
    def test_document_processor_initialization(self, mock_converter):
        """Test document processor initialization."""
        from app.services.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        assert processor is not None
        assert hasattr(processor, 'converter')
        assert hasattr(processor, 'text_splitter')
    
    def test_file_validation(self):
        """Test file validation logic."""
        from app.services.document_processor import document_processor
        
        # Test with non-existent file
        result = document_processor.validate_file("/nonexistent/file.pdf")
        assert result == False


class TestEmbeddingService:
    """Test embedding service functionality."""
    
    @patch('pinecone.Pinecone')
    @patch('openai.AsyncOpenAI')
    def test_embedding_service_initialization(self, mock_openai, mock_pinecone):
        """Test embedding service initialization."""
        from app.services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        assert service is not None
        assert hasattr(service, 'openai_client')
        assert hasattr(service, 'pinecone')


class TestChatAgent:
    """Test chat agent functionality."""
    
    @patch('langchain_openai.ChatOpenAI')
    def test_chat_agent_initialization(self, mock_llm):
        """Test chat agent initialization."""
        from app.agents.chat_rag_agent import ChatRAGAgent
        
        agent = ChatRAGAgent()
        assert agent is not None
        assert hasattr(agent, 'llm')
        assert hasattr(agent, 'workflow')
        assert hasattr(agent, 'system_prompt')


class TestResearchAgent:
    """Test research agent functionality."""
    
    @patch('langchain_openai.ChatOpenAI')
    def test_research_agent_initialization(self, mock_llm):
        """Test research agent initialization."""
        from app.agents.deep_research_agent import DeepResearchAgent
        
        agent = DeepResearchAgent()
        assert agent is not None
        assert hasattr(agent, 'llm')
        assert hasattr(agent, 'workflow')


# Integration tests would require actual database and API keys
class TestIntegration:
    """Integration tests (require actual services)."""
    
    @pytest.mark.skip(reason="Requires actual database and API keys")
    def test_full_document_pipeline(self):
        """Test the complete document processing pipeline."""
        # This would test:
        # 1. Upload document
        # 2. Process with docling
        # 3. Generate embeddings
        # 4. Extract metadata
        # 5. Perform research
        # 6. Chat interaction
        pass
    
    @pytest.mark.skip(reason="Requires actual API keys")
    def test_openai_integration(self):
        """Test OpenAI integration."""
        pass
    
    @pytest.mark.skip(reason="Requires actual API keys")
    def test_pinecone_integration(self):
        """Test Pinecone integration."""
        pass


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])