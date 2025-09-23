"""
Metadata extraction service for financial documents.
Extracts key financial facts, investment data, and metrics from processed documents.
"""
import logging
import re
from typing import Dict, Any
from datetime import datetime, timezone

from openai import AsyncOpenAI

from app.config import get_settings
from app.database.models import Document, DocumentChunk
from app.database.connection import get_db_session
from app.database.schemas import FinancialFacts, InvestmentData
from app.prompts.metadata_extraction import (
    FINANCIAL_FACTS_SYSTEM_PROMPT, INVESTMENT_DATA_SYSTEM_PROMPT,
    DOCUMENT_SUMMARY_SYSTEM_PROMPT, FINANCIAL_FACTS_USER_TEMPLATE,
    INVESTMENT_DATA_USER_TEMPLATE, DOCUMENT_SUMMARY_USER_TEMPLATE
)

settings = get_settings()
logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Service for extracting financial metadata from documents."""
    
    def __init__(self):
        """Initialize the metadata extractor."""
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Financial patterns for regex extraction
        self.financial_patterns = {
            'revenue': [
                r'revenue[s]?\s*(?:of|:)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|m|billion|b)?',
                r'net\s+revenue[s]?\s*(?:of|:)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|m|billion|b)?',
                r'total\s+revenue[s]?\s*(?:of|:)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|m|billion|b)?',
            ],
            'profit': [
                r'net\s+(?:profit|income)[s]?\s*(?:of|:)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|m|billion|b)?',
                r'profit[s]?\s*(?:of|:)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|m|billion|b)?',
                r'earnings\s*(?:of|:)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|m|billion|b)?',
            ],
            'ebitda': [
                r'ebitda\s*(?:of|:)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|m|billion|b)?',
                r'adjusted\s+ebitda\s*(?:of|:)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|m|billion|b)?',
            ],
            'valuation': [
                r'valuation\s*(?:of|:)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|m|billion|b)?',
                r'enterprise\s+value\s*(?:of|:)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|m|billion|b)?',
                r'market\s+cap(?:italization)?\s*(?:of|:)?\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|m|billion|b)?',
            ]
        }
    
    def _ensure_json_serializable(self, data: Any) -> Any:
        """
        Ensure data is JSON serializable by converting non-serializable types.
        
        Note: This is primarily used for regex extraction results and complex data merging.
        Pydantic models handle their own serialization via model_dump().
        """
        try:
            if isinstance(data, dict):
                # Ensure all keys are JSON serializable (strings, numbers, bools, None)
                result = {}
                for k, v in data.items():
                    try:
                        # Convert key to string to ensure it's always hashable and serializable
                        if isinstance(k, (str, int, float, bool, type(None))):
                            # Test if the key is actually hashable
                            try:
                                hash(k)
                                serializable_key = str(k) if not isinstance(k, str) else k
                            except TypeError:
                                serializable_key = str(k)
                        else:
                            # For complex types (including dicts), convert to string
                            serializable_key = str(k)
                        
                        # Double-check the key is hashable after conversion
                        try:
                            hash(serializable_key)
                        except TypeError:
                            # If still not hashable, create a safe key
                            serializable_key = f"key_{abs(hash(str(k))) % 1000000}"
                        
                        # Recursively process the value
                        result[serializable_key] = self._ensure_json_serializable(v)
                        
                    except (TypeError, ValueError) as e:
                        # If any error occurs, create a safe key and log it
                        logger.warning(f"Converting problematic key {repr(k)} to safe key: {str(e)}")
                        try:
                            safe_key = f"key_{abs(hash(str(k))) % 1000000}"
                        except TypeError:
                            safe_key = f"key_{abs(id(k)) % 1000000}"
                        result[safe_key] = self._ensure_json_serializable(v)
                        
                return result
            elif isinstance(data, list):
                return [self._ensure_json_serializable(item) for item in data]
            elif isinstance(data, tuple):
                return [self._ensure_json_serializable(item) for item in data]
            elif isinstance(data, set):
                return [self._ensure_json_serializable(item) for item in data]
            elif isinstance(data, (str, int, float, bool, type(None))):
                return data
            elif hasattr(data, '__dict__'):
                # Handle objects with __dict__ by converting to dict
                return self._ensure_json_serializable(data.__dict__)
            else:
                # Convert other types to string
                return str(data)
        except Exception as e:
            logger.warning(f"Error ensuring JSON serializability for {repr(data)}: {str(e)}, converting to string")
            return str(data)
    
    async def extract_metadata(self, document_id: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from a document.
        
        Args:
            document_id: UUID of the document
            
        Returns:
            Dictionary containing extracted metadata
        """
        try:
            logger.info(f"Starting metadata extraction for document {document_id}")
            
            # Get document and chunks
            with get_db_session() as db:
                document = db.query(Document).filter(Document.id == document_id).first()
                if not document:
                    raise ValueError(f"Document {document_id} not found")
                
                chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == document_id
                ).order_by(DocumentChunk.chunk_index).all()
                
                # Extract content from chunks while still in session to avoid lazy loading issues
                chunk_contents = [chunk.content for chunk in chunks]
            
            # Combine all chunks for full text analysis
            full_text = "\n\n".join(chunk_contents)
            
            # Extract metadata using multiple methods
            # Safely extract results with type checking and error handling
            financial_facts = await self._extract_financial_facts_ai(full_text)
            print(f"Financial facts: {financial_facts}")
            
            investment_data = await self._extract_investment_data_ai(full_text)
            print(f"Investment data: {investment_data}")
            
            key_metrics = self._extract_key_metrics_regex(full_text)
            print(f"Key metrics: {key_metrics}")
            
            structure_info = self._extract_document_structure(full_text)
            print(f"Document structure: {structure_info}")
            
            # Combine all metadata
            metadata = {
                'financial_facts': financial_facts,
                'investment_data': investment_data,
                'key_metrics': key_metrics,
                'document_structure': structure_info,
                'extraction_timestamp': str(datetime.now(timezone.utc).isoformat())
            }
            
            # Update document in database
            logger.info(f"Updating document {document_id} with metadata")
            try:
                with get_db_session() as db:
                    document = db.query(Document).filter(Document.id == document_id).first()
                    if document:
                        # Ensure all data is JSON serializable before storing
                        # Combine key_metrics and structure_info safely
                        combined_metrics = {}
                        
                        # Safely combine metrics with error handling
                        try:
                            print(f"Key metrics: {key_metrics}")
                            if key_metrics and isinstance(key_metrics, dict):
                                # Ensure all keys are hashable before updating
                                safe_key_metrics = self._ensure_json_serializable(key_metrics)
                                if isinstance(safe_key_metrics, dict):
                                    # Double-check all keys are hashable before updating
                                    for k, v in safe_key_metrics.items():
                                        try:
                                            hash(k)
                                            combined_metrics[k] = v
                                        except TypeError:
                                            # If key is still not hashable, create a safe key
                                            safe_k = f"metric_{abs(hash(str(k))) % 1000000}"
                                            combined_metrics[safe_k] = v
                                            logger.warning(f"Converted unhashable key {repr(k)} to {safe_k}")
                                else:
                                    logger.warning("key_metrics is not a dict after serialization, skipping")
                        except Exception as e:
                            logger.warning(f"Error combining key_metrics: {str(e)}")
                        
                        try:
                            print(f"Structure info: {structure_info}")
                            if structure_info and isinstance(structure_info, dict):
                                # Ensure all keys are hashable before updating
                                safe_structure_info = self._ensure_json_serializable(structure_info)
                                if isinstance(safe_structure_info, dict):
                                    # Double-check all keys are hashable before updating
                                    for k, v in safe_structure_info.items():
                                        try:
                                            hash(k)
                                            combined_metrics[k] = v
                                        except TypeError:
                                            # If key is still not hashable, create a safe key
                                            safe_k = f"structure_{abs(hash(str(k))) % 1000000}"
                                            combined_metrics[safe_k] = v
                                            logger.warning(f"Converted unhashable key {repr(k)} to {safe_k}")
                                else:
                                    logger.warning("structure_info is not a dict after serialization, skipping")
                        except Exception as e:
                            logger.warning(f"Error combining structure_info: {str(e)}")
                        
                        logger.debug(f"Updating document {document_id} with metadata")
                        # financial_facts and investment_data are already serialized by Pydantic model_dump()
                        document.financial_facts = financial_facts
                        document.investment_data = investment_data
                        # combined_metrics may contain complex structures from regex extraction
                        document.key_metrics = self._ensure_json_serializable(combined_metrics)
                        db.commit()
                        logger.debug(f"Successfully updated document {document_id} metadata")
            except Exception as db_error:
                logger.error(f"Database error updating document {document_id}: {str(db_error)}")
                # Don't re-raise the database error, just log it
            
            logger.info(f"Metadata extraction completed for document {document_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata for document {document_id}: {str(e)}")
            raise e
    
    async def _extract_financial_facts_ai(self, text: str) -> Dict[str, Any]:
        """Extract financial facts using OpenAI GPT with structured output."""
        try:
            response = await self.openai_client.beta.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": FINANCIAL_FACTS_SYSTEM_PROMPT},
                    {"role": "user", "content": FINANCIAL_FACTS_USER_TEMPLATE.format(text=text[:4000])}
                ],
                response_format=FinancialFacts,
                max_completion_tokens=settings.OPENAI_MAX_OUTPUT_TOKENS
            )
            
            # Check if response was truncated due to token limit
            if response.choices[0].finish_reason == "length":
                raise Exception("Financial facts extraction response was truncated due to token limit")
            
            financial_facts = response.choices[0].message.parsed
            if financial_facts:
                return financial_facts.model_dump()
            else:
                raise Exception("No financial facts parsed from response")
                    
        except Exception as e:
            logger.error(f"Error in AI financial facts extraction: {str(e)}")
            raise e
    
    async def _extract_investment_data_ai(self, text: str) -> Dict[str, Any]:
        """Extract investment-related data using OpenAI GPT with structured output."""
        try:
            response = await self.openai_client.beta.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": INVESTMENT_DATA_SYSTEM_PROMPT},
                    {"role": "user", "content": INVESTMENT_DATA_USER_TEMPLATE.format(text=text[:4000])}
                ],
                response_format=InvestmentData,
                max_completion_tokens=settings.OPENAI_MAX_OUTPUT_TOKENS
            )
            
            # Check if response was truncated due to token limit
            if response.choices[0].finish_reason == "length":
                raise Exception("Investment data extraction response was truncated due to token limit")
            
            investment_data = response.choices[0].message.parsed
            if investment_data:
                return investment_data.model_dump()
            else:
                raise Exception("No investment data parsed from response")
                    
        except Exception as e:
            logger.error(f"Error in AI investment data extraction: {str(e)}")
            raise e
    
    def _extract_key_metrics_regex(self, text: str) -> Dict[str, Any]:
        """Extract key financial metrics using regex patterns."""
        metrics = {}
        
        # Convert text to lowercase for pattern matching
        text_lower = text.lower()
        
        # Extract financial figures using patterns
        for category, patterns in self.financial_patterns.items():
            try:
                # Ensure category is a string and hashable
                safe_category = str(category) if category is not None else "unknown"
                values = []
                
                # Ensure patterns is a list and contains valid patterns
                if not isinstance(patterns, (list, tuple)):
                    logger.warning(f"Invalid patterns for category {category}: {type(patterns)}")
                    continue
                    
                for pattern in patterns:
                    if not isinstance(pattern, str):
                        logger.warning(f"Skipping non-string pattern in {category}: {type(pattern)}")
                        continue  # Skip invalid patterns
                        
                    matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                    for match in matches:
                        try:
                            # Clean and convert the number
                            value_str = match.group(1).replace(',', '')
                            value = float(value_str)
                            
                            # Check for scale indicators in the surrounding text
                            context = text_lower[max(0, match.start()-20):match.end()+20]
                            if 'million' in context or ' m ' in context:
                                value *= 1_000_000
                            elif 'billion' in context or ' b ' in context:
                                value *= 1_000_000_000
                            
                            values.append(value)
                            
                        except (ValueError, IndexError, AttributeError):
                            continue
                
                if values:
                    metrics[safe_category] = {
                        'values': values,
                        'primary_value': max(values),  # Use the highest value as primary
                        'count': len(values)
                    }
            except Exception as e:
                logger.warning(f"Error processing category {category}: {str(e)}")
                continue
        
        # Extract percentages
        try:
            percentage_patterns = [
                r'(\d+(?:\.\d+)?)%',
                r'(\d+(?:\.\d+)?)\s*percent'
            ]
            
            percentages = []
            for pattern in percentage_patterns:
                if not isinstance(pattern, str):
                    continue  # Skip invalid patterns
                    
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    try:
                        value = float(match.group(1))
                        if 0 <= value <= 100:  # Basic validation for percentages
                            percentages.append(value)
                    except (ValueError, AttributeError, IndexError):
                        continue
            
            if percentages:
                metrics['percentages'] = {
                    'values': percentages,
                    'count': len(percentages)
                }
        except Exception as e:
            logger.warning(f"Error extracting percentages: {str(e)}")
        
        return metrics
    
    def _extract_document_structure(self, text: str) -> Dict[str, Any]:
        """Extract document structure information."""
        structure = {}
        
        # Count sections (indicated by headers or numbering)
        section_patterns = [
            r'^[0-9]+\.\s+[A-Z]',  # 1. SECTION
            r'^[IVX]+\.\s+[A-Z]',   # I. SECTION  
            r'^[A-Z][A-Z\s]+$',     # ALL CAPS HEADERS
        ]
        
        sections = 0
        for pattern in section_patterns:
            sections += len(re.findall(pattern, text, re.MULTILINE))
        
        structure['estimated_sections'] = sections
        
        # Count tables (rough estimation)
        table_indicators = ['table', 'figure', '|', '\t']
        table_score = sum(text.lower().count(indicator) for indicator in table_indicators)
        structure['estimated_tables'] = min(table_score // 10, 50)  # Cap at 50
        
        # Count bullet points
        bullet_patterns = [r'^\s*[•\-\*]\s+', r'^\s*\d+\.\s+']
        bullet_points = 0
        for pattern in bullet_patterns:
            bullet_points += len(re.findall(pattern, text, re.MULTILINE))
        
        structure['bullet_points'] = bullet_points
        
        # Estimate reading time (average 200 words per minute)
        word_count = len(text.split())
        structure['estimated_reading_time_minutes'] = max(1, word_count // 200)
        
        # Document complexity score (0-10)
        complexity = min(10, (
            sections * 0.5 + 
            structure['estimated_tables'] * 0.3 + 
            bullet_points * 0.1 + 
            word_count / 1000
        ))
        structure['complexity_score'] = round(complexity, 1)
        
        return structure
    
    async def summarize_document(self, document_id: str, max_length: int = 500) -> str:
        """Generate a concise summary of the document."""
        try:
            # Get document content
            with get_db_session() as db:
                chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == document_id
                ).order_by(DocumentChunk.chunk_index).limit(5).all()  # First 5 chunks
                
                if not chunks:
                    return "No content available for summarization."
                
                # Extract content from chunks while still in session to avoid lazy loading issues
                chunk_contents = [chunk.content for chunk in chunks]
            
            text = "\n\n".join(chunk_contents)
            
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": DOCUMENT_SUMMARY_SYSTEM_PROMPT.format(max_length=max_length)},
                    {"role": "user", "content": DOCUMENT_SUMMARY_USER_TEMPLATE.format(text=text[:3000])}
                ],
                max_completion_tokens=min(max_length // 2, settings.OPENAI_MAX_OUTPUT_TOKENS)
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary for document {document_id}: {str(e)}")
            return f"Error generating summary: {str(e)}"


# Global instance
metadata_extractor = MetadataExtractor()