"""
Embedding service for generating and storing document embeddings in Pinecone using LangChain.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from datetime import datetime
import hashlib

from openai import AsyncOpenAI
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document as LangChainDocument

from app.config import get_settings
from app.database.models import Document, DocumentChunk
from app.database.connection import get_db_session

settings = get_settings()
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing document embeddings."""
    
    def __init__(self):
        """Initialize the embedding service."""
        # Initialize OpenAI client (still needed for some operations)
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Initialize Pinecone client (for index management)
        self.pinecone = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Initialize LangChain embeddings
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize or get Pinecone index
        self.index = self._initialize_pinecone_index()
        
        # Initialize PineconeVectorStore
        self.vector_store = PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings,
            text_key="content"
        )
    
    def _initialize_pinecone_index(self):
        """Initialize or connect to the Pinecone index."""
        try:
            # Check if index exists
            existing_indexes = self.pinecone.list_indexes()
            index_names = [idx.name for idx in existing_indexes]
            
            if settings.PINECONE_INDEX_NAME not in index_names:
                # Create the index
                logger.info(f"Creating Pinecone index: {settings.PINECONE_INDEX_NAME}")
                self.pinecone.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=settings.PINECONE_DIMENSION,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info("Pinecone index created successfully")
            else:
                # Check if existing index has correct dimensions
                index_stats = self.pinecone.describe_index(settings.PINECONE_INDEX_NAME)
                if index_stats.dimension != settings.PINECONE_DIMENSION:
                    logger.error(f"Pinecone index dimension mismatch! "
                               f"Expected: {settings.PINECONE_DIMENSION}, "
                               f"Found: {index_stats.dimension}")
                    
                    logger.info("Deleting existing index with wrong dimensions...")
                    self.pinecone.delete_index(settings.PINECONE_INDEX_NAME)
                    
                    logger.info("Creating new index with correct dimensions...")
                    self.pinecone.create_index(
                        name=settings.PINECONE_INDEX_NAME,
                        dimension=settings.PINECONE_DIMENSION,
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud="aws",
                            region="us-east-1"
                        )
                    )
                    logger.info("Pinecone index recreated successfully")
            
            # Connect to the index
            index = self.pinecone.Index(settings.PINECONE_INDEX_NAME)
            logger.info(f"Connected to Pinecone index: {settings.PINECONE_INDEX_NAME}")
            return index
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone index: {str(e)}")
            raise e
    
    async def embed_document(self, document_id: str) -> Dict[str, Any]:
        """
        Generate embeddings for all chunks of a document and store in Pinecone.
        
        Args:
            document_id: UUID of the document
            
        Returns:
            Dictionary containing embedding results
        """
        try:
            logger.info(f"Starting embedding process for document {document_id}")
            
            # Get document and its chunks from database
            with get_db_session() as db:
                document = db.query(Document).filter(Document.id == document_id).first()
                if not document:
                    raise ValueError(f"Document {document_id} not found")
                
                chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == document_id
                ).order_by(DocumentChunk.chunk_index).all()
                
                if not chunks:
                    raise ValueError(f"No chunks found for document {document_id}")
                
                # Extract all needed data while still in session context
                chunk_data = []
                for chunk in chunks:
                    chunk_info = {
                        'id': chunk.id,
                        'content': chunk.content,
                        'chunk_index': chunk.chunk_index,
                        'page_number': chunk.page_number or 0,
                        'char_count': chunk.char_count,
                        'token_count': chunk.token_count,
                        'created_at': chunk.created_at.isoformat()
                    }
                    chunk_data.append(chunk_info)
                
                # Extract document metadata
                doc_filename = document.filename
                doc_original_filename = document.original_filename
            
            # Prepare LangChain documents for embedding
            langchain_docs = []
            for chunk in chunk_data:
                metadata = {
                    'document_id': str(document_id),
                    'chunk_id': str(chunk['id']),
                    'chunk_index': chunk['chunk_index'],
                    'page_number': chunk['page_number'],
                    'filename': doc_filename,
                    'original_filename': doc_original_filename,
                    'char_count': chunk['char_count'],
                    'token_count': chunk['token_count'],
                    'created_at': chunk['created_at']
                }
                
                doc = LangChainDocument(
                    page_content=chunk['content'],
                    metadata=metadata
                )
                langchain_docs.append(doc)
            
            # Use PineconeVectorStore to add documents with custom IDs
            doc_ids = [self._generate_vector_id(document_id, chunk['id']) for chunk in chunk_data]
            
            # Process in batches to avoid memory issues
            batch_size = 100
            embedded_count = 0
            
            for i in range(0, len(langchain_docs), batch_size):
                batch_docs = langchain_docs[i:i + batch_size]
                batch_ids = doc_ids[i:i + batch_size]
                batch_chunk_data = chunk_data[i:i + batch_size]
                
                # Add documents to vector store with namespace
                await asyncio.to_thread(
                    self.vector_store.add_documents,
                    documents=batch_docs,
                    ids=batch_ids,
                    namespace=self._get_namespace(document_id)
                )
                
                embedded_count += len(batch_docs)
                logger.info(f"Embedded batch {i//batch_size + 1}: {len(batch_docs)} vectors")
                
                # Update chunk records with Pinecone IDs
                with get_db_session() as db:
                    for j, chunk_info in enumerate(batch_chunk_data):
                        vector_id = batch_ids[j]
                        chunk_record = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_info['id']).first()
                        if chunk_record:
                            chunk_record.pinecone_id = vector_id
                            chunk_record.embedding_model = settings.OPENAI_EMBEDDING_MODEL
            
            # Update document record
            with get_db_session() as db:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.is_embedded = True
                    document.embedding_count = embedded_count
                    document.pinecone_namespace = self._get_namespace(document_id)
            
            logger.info(f"Successfully embedded {embedded_count} chunks for document {document_id}")
            
            return {
                'document_id': document_id,
                'embedded_count': embedded_count,
                'namespace': self._get_namespace(document_id),
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error embedding document {document_id}: {str(e)}")
            
            # Update document with error status
            with get_db_session() as db:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.is_embedded = False
                    document.processing_error = f"Embedding error: {str(e)}"
            
            raise e
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using OpenAI."""
        try:
            # Use OpenAI's embedding endpoint
            response = await self.openai_client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=texts
            )
            
            embeddings = [item.embedding for item in response.data]
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise e
    
    def _generate_vector_id(self, document_id: str, chunk_id: str) -> str:
        """Generate a unique vector ID for Pinecone."""
        combined = f"{document_id}_{chunk_id}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_namespace(self, document_id: str) -> str:
        """Get the namespace for a document in Pinecone."""
        return f"doc_{str(document_id).replace('-', '_')}"
    
    async def search_similar_chunks(
        self,
        query: str,
        document_id: Optional[str] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query: Search query text
            document_id: Optional document ID to limit search scope
            top_k: Number of similar chunks to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar chunks with metadata and similarity scores
        """
        try:
            # Determine namespace for search
            namespace = self._get_namespace(document_id) if document_id else None

            # Prefer normalized relevance scores when available
            use_relevance_scores = hasattr(self.vector_store, 'similarity_search_with_relevance_scores')

            # Execute search (avoid passing score_threshold because support varies by version)
            try:
                if use_relevance_scores:
                    if namespace:
                        search_results = await asyncio.to_thread(
                            self.vector_store.similarity_search_with_relevance_scores,  # type: ignore[attr-defined]
                            query,
                            k=top_k,
                            namespace=namespace
                        )
                    else:
                        search_results = await asyncio.to_thread(
                            self.vector_store.similarity_search_with_relevance_scores,  # type: ignore[attr-defined]
                            query,
                            k=top_k
                        )
                else:
                    if namespace:
                        search_results = await asyncio.to_thread(
                            self.vector_store.similarity_search_with_score,
                            query,
                            k=top_k,
                            namespace=namespace
                        )
                    else:
                        search_results = await asyncio.to_thread(
                            self.vector_store.similarity_search_with_score,
                            query,
                            k=top_k
                        )
            except TypeError:
                # Fallback if the underlying method signature differs (e.g., namespace unsupported)
                if use_relevance_scores:
                    search_results = await asyncio.to_thread(
                        self.vector_store.similarity_search_with_relevance_scores,  # type: ignore[attr-defined]
                        query,
                        k=top_k
                    )
                else:
                    search_results = await asyncio.to_thread(
                        self.vector_store.similarity_search_with_score,
                        query,
                        k=top_k
                    )

            # Process results
            similar_chunks: List[Dict[str, Any]] = []
            top_scores: List[float] = []
            for doc, score in search_results:
                score_value = float(score)
                top_scores.append(score_value)
                # If relevance scores are available, treat threshold as normalized similarity
                # Otherwise, include results without filtering (to avoid false negatives from distance semantics)
                if use_relevance_scores and score_value < similarity_threshold:
                    continue

                chunk_id = doc.metadata.get('chunk_id')

                # Get full chunk content from database
                with get_db_session() as db:
                    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
                    if chunk:
                        similar_chunks.append({
                            'chunk_id': chunk_id,
                            'content': doc.page_content,
                            'similarity_score': score_value,
                            'metadata': doc.metadata,
                            'page_number': chunk.page_number,
                            'chunk_index': chunk.chunk_index
                        })

            # If no results found, relax constraints once: lower threshold and increase k
            if not similar_chunks and similarity_threshold > 0.3:
                logger.info(
                    f"No similar chunks found (scores={top_scores[:3]}). Retrying with relaxed threshold and k."
                )
                return await self.search_similar_chunks(
                    query=query,
                    document_id=document_id,
                    top_k=max(top_k, 12),
                    similarity_threshold=0.3
                )

            logger.info(
                f"Found {len(similar_chunks)} similar chunks for query: {query[:50]}... Top scores: {top_scores[:3]}"
            )
            return similar_chunks
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            raise e
    
    async def delete_document_embeddings(self, document_id: str) -> bool:
        """
        Delete all embeddings for a document from Pinecone.
        
        Args:
            document_id: UUID of the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            namespace = self._get_namespace(document_id)
            
            # Get all vector IDs for this document
            with get_db_session() as db:
                chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == document_id,
                    DocumentChunk.pinecone_id.isnot(None)
                ).all()
                
                vector_ids = [chunk.pinecone_id for chunk in chunks]
            
            if vector_ids:
                # Delete from Pinecone using the direct index (PineconeVectorStore doesn't have a bulk delete method)
                await asyncio.to_thread(
                    self.index.delete,
                    ids=vector_ids,
                    namespace=namespace
                )
                logger.info(f"Deleted {len(vector_ids)} vectors for document {document_id}")
            
            # Update database records
            with get_db_session() as db:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.is_embedded = False
                    document.embedding_count = 0
                    document.pinecone_namespace = None
                
                # Clear Pinecone IDs from chunks
                db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == document_id
                ).update({
                    'pinecone_id': None,
                    'embedding_model': None
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting embeddings for document {document_id}: {str(e)}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index."""
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats.total_vector_count,
                'index_fullness': stats.index_fullness,
                'namespaces': dict(stats.namespaces) if stats.namespaces else {}
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            return {}


# Global instance
embedding_service = EmbeddingService()