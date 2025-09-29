"""
Document processing service using docling for parsing financial documents.
"""
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, PictureDescriptionApiOptions
from docling_core.types.doc.document import ImageRefMode
from docling.document_converter import PdfFormatOption
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument

from app.config import get_settings
from app.database.models import Document, DocumentChunk
from app.database.connection import get_db_session

# Force CPU usage to avoid MPS compatibility issues on macOS
import torch
torch.set_default_device('cpu')

# Set environment variable to force CPU usage for docling models (fixes MPS compatibility issues)
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TORCH_DEVICE"] = "cpu"

settings = get_settings()
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing documents using docling."""
    
    def __init__(self):
        """Initialize the document processor."""
        self.pipeline_options = PdfPipelineOptions()
        self.pipeline_options.do_ocr = True  # Enable OCR for scanned documents
        self.pipeline_options.do_table_structure = True  # Extract table structure
        self.pipeline_options.table_structure_options.do_cell_matching = True
        self.pipeline_options.generate_picture_images=True # Enable picture extraction
        self.pipeline_options.do_picture_description=True # Enable picture description
        self.pipeline_options.picture_description_options=PictureDescriptionApiOptions()
        self.pipeline_options.picture_description_options.url = "https://api.openai.com/v1/chat/completions"
        self.pipeline_options.picture_description_options.prompt = "Describe this image in sentences in a single paragraph. Include reference numerical values in the description."
        self.pipeline_options.picture_description_options.params = {"model": settings.OPENAI_MODEL}
        self.pipeline_options.picture_description_options.headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
        self.pipeline_options.picture_description_options.timeout = 60
        self.pipeline_options.enable_remote_services=True
        
        # Initialize document converter with optimized settings
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=self.pipeline_options)
            }
        )
        
        # Initialize text splitter for creating chunks
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
            add_start_index=True
        )
        
        # Thread pool for async processing
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def process_document(self, document_id: str, file_path: str) -> Dict[str, Any]:
        """
        Process a document asynchronously.
        
        Args:
            document_id: UUID of the document in the database
            file_path: Path to the uploaded file
            
        Returns:
            Dictionary containing processing results and metadata
        """
        try:
            logger.info(f"Starting document processing for {document_id}")
            
            # Run the synchronous processing in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._process_document_sync, 
                document_id, 
                file_path
            )
            
            logger.info(f"Document processing completed for {document_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            # Update document with error status
            with get_db_session() as db:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.processing_error = str(e)
                    document.is_processed = False
            
            raise e
    
    def _process_document_sync(self, document_id: str, file_path: str) -> Dict[str, Any]:
        """
        Synchronously process a document using docling.
        
        Args:
            document_id: UUID of the document in the database
            file_path: Path to the uploaded file
            
        Returns:
            Dictionary containing processing results and metadata
        """
        # Convert document using docling
        conversion_result = self.converter.convert(file_path)
        
        # Extract the main document
        doc = conversion_result.document
        
        # Get document metadata
        metadata = self._extract_document_metadata(doc)
        
        # Get full text content
        full_text = doc.export_to_markdown(mark_annotations=True, include_annotations=True)
        
        # Create text chunks
        chunks = self._create_text_chunks(full_text, document_id)
        
        # Extract tables if present
        tables = self._extract_tables(doc)
        
        # Extract images
        images = self._extract_images(doc)
        
        # Store results in database
        with get_db_session() as db:
            # Update document metadata
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.page_count = metadata.get('page_count', 0)
                document.word_count = metadata.get('word_count', 0)
                document.is_processed = True
                document.processing_error = None
                document.extracted_images = images
                
                # Store document chunks
                for i, chunk_data in enumerate(chunks):
                    chunk = DocumentChunk(
                        document_id=document_id,
                        content=chunk_data['content'],
                        chunk_index=i,
                        page_number=chunk_data.get('page_number'),
                        token_count=chunk_data.get('token_count'),
                        char_count=len(chunk_data['content'])
                    )
                    db.add(chunk)
        
        return {
            'document_id': document_id,
            'metadata': metadata,
            'chunk_count': len(chunks),
            'tables': tables,
            'full_text_length': len(full_text),
            'processing_status': 'completed',
            'image_count': len(images)
        }
    
    def _extract_document_metadata(self, doc) -> Dict[str, Any]:
        """Extract metadata from the docling document."""
        metadata = {}
        
        try:
            # Basic document information
            if hasattr(doc, 'pages') and doc.pages:
                metadata['page_count'] = len(doc.pages)
            else:
                metadata['page_count'] = 0
            
            # Get full text for word count
            full_text = doc.export_to_markdown()
            word_count = len(full_text.split()) if full_text else 0
            metadata['word_count'] = word_count
            
            # Extract document title if available
            if hasattr(doc, 'description') and doc.description:
                if hasattr(doc.description, 'title'):
                    metadata['title'] = doc.description.title
            
            # Try to extract document structure information
            if hasattr(doc, 'body') and doc.body:
                metadata['has_structured_content'] = True
            else:
                metadata['has_structured_content'] = False
                
        except Exception as e:
            logger.warning(f"Error extracting metadata: {str(e)}")
            metadata['extraction_error'] = str(e)
        
        return metadata
    
    def _create_text_chunks(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Create text chunks using LangChain's text splitter.
        
        Args:
            text: Full document text
            document_id: Document UUID
            
        Returns:
            List of chunk dictionaries
        """
        if not text:
            return []
        
        # Create LangChain documents for splitting
        langchain_docs = [LangchainDocument(
            page_content=text,
            metadata={'document_id': document_id}
        )]
        
        # Split into chunks
        split_docs = self.text_splitter.split_documents(langchain_docs)
        
        chunks = []
        for i, doc in enumerate(split_docs):
            chunk_data = {
                'content': doc.page_content,
                'metadata': doc.metadata,
                'token_count': self._estimate_token_count(doc.page_content),
                'char_count': len(doc.page_content),
                'start_index': doc.metadata.get('start_index', 0)
            }
            
            # Try to determine page number from start index
            # This is a rough estimation
            chunk_data['page_number'] = self._estimate_page_number(
                chunk_data['start_index'], 
                len(text)
            )
            
            chunks.append(chunk_data)
        
        return chunks
    
    def _extract_tables(self, doc) -> List[Dict[str, Any]]:
        """Extract tables from the document."""
        tables = []
        
        try:
            if hasattr(doc, 'tables') and doc.tables:
                for i, table in enumerate(doc.tables):
                    table_data = {
                        'table_id': i,
                        'content': str(table),
                        'type': 'table'
                    }
                    
                    # Try to extract table as CSV if possible
                    if hasattr(table, 'export_to_dataframe'):
                        try:
                            df = table.export_to_dataframe(doc)
                            table_data['csv_data'] = df.to_csv(index=False)
                            table_data['row_count'] = len(df)
                            table_data['column_count'] = len(df.columns)
                        except Exception as e:
                            logger.warning(f"Could not export table {i} to dataframe: {e}")
                    
                    tables.append(table_data)              
        except Exception as e:
            logger.warning(f"Error extracting tables: {str(e)}")
        
        return tables
    
    def _extract_images(self, doc) -> List[Dict[str, Any]]:
        """Extract images and their captions from the document."""
        images = []
        if not hasattr(doc, 'pictures'):
            return images
        
        for i, pic in enumerate(doc.pictures):
            try:
                # Extract caption
                caption = None
                try:
                    caption = pic.caption_text(doc=doc)
                except Exception as e:
                    logger.warning(f"Error extracting caption for image {i}: {e}")
                
                # Get page number from provenance information
                page_number = None
                if hasattr(pic, 'prov') and pic.prov:
                    page_number = pic.prov[0].page_no
                else:
                    logger.warning(f"Could not find page number for image {i}")
                
                # Clean and validate caption
                if caption:
                    caption = caption.strip()
                    if not caption:  # Empty after stripping
                        caption = None
                
                # Generate fallback caption if needed
                if not caption:
                    if page_number:
                        caption = f"Image {i+1} (page {page_number})"
                    else:
                        caption = f"Image {i+1}"
                
                image_data = {
                    'picture_id': i,
                    'image_uri': str(pic.image.uri) if pic.image else None,
                    'caption': caption,
                    'page_number': page_number,
                }

                images.append(image_data)                
            except Exception as e:
                logger.warning(f"Could not extract image {i}: {e}")
                pass
        
        logger.info(f"Successfully extracted {len(images)} images with captions and page numbers")
        return images

    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count (rough approximation: 4 characters per token)."""
        return len(text) // 4
    
    def _estimate_page_number(self, start_index: int, total_length: int) -> Optional[int]:
        """Estimate page number based on character position."""
        if total_length == 0:
            return None
        
        # Rough estimation: 2000 characters per page (very approximate)
        estimated_page = (start_index // 2000) + 1
        return estimated_page
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate that the file can be processed.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is valid, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False
            
            # Check file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in settings.ALLOWED_FILE_TYPES:
                return False
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > settings.MAX_FILE_SIZE:
                return False
            
            # Try to read the file header
            with open(file_path, 'rb') as f:
                header = f.read(1024)
                if file_ext == '.pdf' and not header.startswith(b'%PDF'):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file {file_path}: {str(e)}")
            return False
    
    async def cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary files after processing."""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up file {file_path}: {str(e)}")


# Global instance
document_processor = DocumentProcessor()