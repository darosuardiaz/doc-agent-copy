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
    
        # Heuristic regexes for direct extraction fallback
        self.heuristic_patterns = {
            'revenue_current': [
                r'(?:total\s+)?revenue[s]?\s*(?:and\s+other\s+income\s*)?[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?',
                r'net\s+revenue[s]?\s*[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?',
                r'total\s+net\s+revenue[s]?\s*[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?'
            ],
            'net_income': [
                r'net\s+(?:income|earnings|profit)[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?',
                r'(?:net\s+)?income\s+(?:from\s+operations\s*)?[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?'
            ],
            'gross_profit': [
                r'gross\s+profit[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?'
            ],
            'operating_income': [
                r'(?:income|loss)\s+from\s+operations[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?',
                r'operating\s+(?:income|profit|earnings)[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?'
            ],
            'operating_cash_flow': [
                r'(?:net\s+)?cash\s+(?:provided\s+by\s+|from\s+)?operating\s+activities[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?',
                r'operating\s+cash\s+flows?[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?'
            ],
            'free_cash_flow': [
                r'free\s+cash\s+flows?[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?'
            ],
            'total_debt': [
                r'total\s+debt[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?',
                r'long[- ]term\s+debt[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?'
            ],
            'stockholders_equity': [
                r'(?:total\s+)?stockholders[^\d\n]*?equity[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?',
                r'shareholders[^\d\n]*?equity[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?'
            ],
            'total_assets': [
                r'total\s+assets[^\d\n]*?[\$]?([\d,]+(?:\.\d+)?)\s*(millions?|thousands?|m|k|billion|b)?'
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
            
            # Log text analysis info for debugging
            logger.info(f"Full text length: {len(full_text)} characters")
            logger.info(f"Number of chunks: {len(chunk_contents)}")
            logger.info(f"Preview of text (first 500 chars): {full_text[:500]}")
            
            # Extract metadata using multiple methods with robust error handling
            financial_facts = None
            
            try:
                # Safely extract results with type checking and error handling
                financial_facts = await self._extract_financial_facts_ai(full_text)
                logger.info(f"Primary extraction result: {financial_facts}")
                print(f"Financial facts: {financial_facts}")
            except Exception as e:
                logger.error(f"Primary AI extraction failed: {str(e)}")
                financial_facts = {
                    'revenue': {'current_year': None, 'previous_year': None, 'currency': 'USD', 'period': 'annual'},
                    'profit_loss': {'net_income': None, 'gross_profit': None, 'operating_profit': None, 'currency': 'USD'},
                    'cash_flow': {'operating_cash_flow': None, 'free_cash_flow': None, 'currency': 'USD'},
                    'debt_equity': {'total_debt': None, 'equity': None, 'debt_to_equity_ratio': None},
                    'other_metrics': {'ebitda': None, 'margin_percentage': None, 'growth_rate': None}
                }
            
            # If no financial data found in main extraction, try alternative approaches
            if self._is_financial_data_empty(financial_facts):
                try:
                    logger.info("No financial data found in primary extraction, trying alternative approaches...")
                    alternative_facts = await self._extract_financial_facts_alternative(full_text)
                    if not self._is_financial_data_empty(alternative_facts):
                        financial_facts = alternative_facts
                        logger.info(f"Alternative extraction successful: {financial_facts}")
                    print(f"Alternative financial facts: {financial_facts}")
                except Exception as e:
                    logger.error(f"Alternative AI extraction failed: {str(e)}")

            # If still empty, try regex heuristic fallback
            if self._is_financial_data_empty(financial_facts):
                try:
                    logger.info("AI-based extraction returned empty values. Falling back to regex heuristic extraction...")
                    regex_facts = self._extract_financial_facts_regex(full_text)
                    logger.info(f"Regex extraction result: {regex_facts}")
                    print(f"Regex-based financial facts: {regex_facts}")
                    
                    # Merge regex facts into financial_facts where AI left None
                    if financial_facts and regex_facts:
                        for section, fields in regex_facts.items():
                            if section in financial_facts and isinstance(fields, dict):
                                for k, v in fields.items():
                                    if k in financial_facts[section] and financial_facts[section][k] in (None, 'null', '') and v is not None:
                                        financial_facts[section][k] = v
                                        logger.info(f"Populated {section}.{k} with regex value: {v}")
                    else:
                        financial_facts = regex_facts
                except Exception as e:
                    logger.error(f"Regex fallback extraction failed: {str(e)}")
                    
            # Ensure we always have a valid financial_facts structure
            if not financial_facts:
                financial_facts = {
                    'revenue': {'current_year': None, 'previous_year': None, 'currency': 'USD', 'period': 'annual'},
                    'profit_loss': {'net_income': None, 'gross_profit': None, 'operating_profit': None, 'currency': 'USD'},
                    'cash_flow': {'operating_cash_flow': None, 'free_cash_flow': None, 'currency': 'USD'},
                    'debt_equity': {'total_debt': None, 'equity': None, 'debt_to_equity_ratio': None},
                    'other_metrics': {'ebitda': None, 'margin_percentage': None, 'growth_rate': None}
                }
            
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
    
    def _clean_financial_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and validate financial data to ensure proper serialization.
        
        Args:
            data: Raw financial data dictionary
            
        Returns:
            Cleaned financial data dictionary
        """
        def clean_currency_field(currency_value: Any) -> str:
            """Clean currency field to ensure it's never the string 'null'."""
            if currency_value is None or currency_value == "null" or currency_value == "":
                return "USD"  # Default to USD if unclear
            if isinstance(currency_value, str) and currency_value.strip():
                return currency_value.strip().upper()
            return "USD"
        
        def clean_numeric_field(value: Any) -> Any:
            """Clean numeric field to ensure proper null handling."""
            if value is None or value == "null" or value == "":
                return None
            if isinstance(value, (int, float)):
                return value
            if isinstance(value, str):
                try:
                    return float(value) if '.' in value else int(value)
                except (ValueError, TypeError):
                    return None
            return None
        
        cleaned_data = {}
        
        try:
            # Clean revenue data
            if "revenue" in data and isinstance(data["revenue"], dict):
                revenue = data["revenue"]
                cleaned_data["revenue"] = {
                    "current_year": clean_numeric_field(revenue.get("current_year")),
                    "previous_year": clean_numeric_field(revenue.get("previous_year")),
                    "currency": clean_currency_field(revenue.get("currency")),
                    "period": revenue.get("period", "annual") if revenue.get("period") and revenue.get("period") != "null" else "annual"
                }
            
            # Clean profit_loss data  
            if "profit_loss" in data and isinstance(data["profit_loss"], dict):
                profit_loss = data["profit_loss"]
                cleaned_data["profit_loss"] = {
                    "net_income": clean_numeric_field(profit_loss.get("net_income")),
                    "gross_profit": clean_numeric_field(profit_loss.get("gross_profit")),
                    "operating_profit": clean_numeric_field(profit_loss.get("operating_profit")),
                    "currency": clean_currency_field(profit_loss.get("currency"))
                }
            
            # Clean cash_flow data
            if "cash_flow" in data and isinstance(data["cash_flow"], dict):
                cash_flow = data["cash_flow"]
                cleaned_data["cash_flow"] = {
                    "operating_cash_flow": clean_numeric_field(cash_flow.get("operating_cash_flow")),
                    "free_cash_flow": clean_numeric_field(cash_flow.get("free_cash_flow")),
                    "currency": clean_currency_field(cash_flow.get("currency"))
                }
            
            # Clean debt_equity data
            if "debt_equity" in data and isinstance(data["debt_equity"], dict):
                debt_equity = data["debt_equity"]
                cleaned_data["debt_equity"] = {
                    "total_debt": clean_numeric_field(debt_equity.get("total_debt")),
                    "equity": clean_numeric_field(debt_equity.get("equity")),
                    "debt_to_equity_ratio": clean_numeric_field(debt_equity.get("debt_to_equity_ratio"))
                }
            
            # Clean other_metrics data
            if "other_metrics" in data and isinstance(data["other_metrics"], dict):
                other_metrics = data["other_metrics"]
                cleaned_data["other_metrics"] = {
                    "ebitda": clean_numeric_field(other_metrics.get("ebitda")),
                    "margin_percentage": clean_numeric_field(other_metrics.get("margin_percentage")),
                    "growth_rate": clean_numeric_field(other_metrics.get("growth_rate"))
                }
            
            return cleaned_data
            
        except Exception as e:
            logger.warning(f"Error cleaning financial data: {str(e)}, returning original data")
            return data

    def _is_financial_data_empty(self, financial_data: Dict[str, Any]) -> bool:
        """
        Check if financial data is empty (all values are None/null).
        
        Args:
            financial_data: Financial data dictionary to check
            
        Returns:
            True if all financial values are None/null, False otherwise
        """
        if not financial_data:
            return True
        
        # Check if all numeric fields are None/null
        numeric_fields = []
        
        for category_name, category_data in financial_data.items():
            if isinstance(category_data, dict):
                for field_name, field_value in category_data.items():
                    # Skip currency and period fields, focus on numeric data
                    if field_name not in ['currency', 'period']:
                        numeric_fields.append(field_value)
        
        # If all numeric fields are None/null, consider it empty
        return all(value is None for value in numeric_fields)

    async def _extract_financial_facts_alternative(self, text: str) -> Dict[str, Any]:
        """
        Alternative approach to extract financial facts.
        
        Tries different strategies:
        1. Look at different parts of the document
        2. Use regex patterns to find financial keywords
        3. Focus on specific sections that might contain financial data
        
        Args:
            text: Full document text
            
        Returns:
            Financial facts dictionary
        """
        try:
            logger.info("Trying alternative financial extraction approaches...")
            
            # Strategy 1: Look for financial keywords and extract surrounding context
            financial_keywords = [
                'revenue', 'sales', 'income', 'profit', 'loss', 'ebitda', 
                'cash flow', 'debt', 'equity', 'assets', 'liabilities',
                'million', 'billion', '$', '€', '£', '%'
            ]
            
            # Find sections with financial keywords
            text_lower = text.lower()
            financial_sections = []
            
            for keyword in financial_keywords:
                start_pos = 0
                while True:
                    pos = text_lower.find(keyword, start_pos)
                    if pos == -1:
                        break
                    
                    # Extract 500 characters around the keyword
                    section_start = max(0, pos - 250)
                    section_end = min(len(text), pos + 250)
                    section = text[section_start:section_end]
                    financial_sections.append(section)
                    
                    start_pos = pos + 1
            
            # Remove duplicates and combine sections
            unique_sections = list(set(financial_sections))
            combined_financial_text = "\n\n".join(unique_sections[:10])  # Limit to first 10 unique sections
            
            if combined_financial_text:
                logger.info(f"Found {len(unique_sections)} sections with financial keywords")
                logger.info(f"Combined financial text length: {len(combined_financial_text)}")
                
                # Try AI extraction on the focused financial content
                result = await self._extract_financial_facts_core(combined_financial_text)
                if not self._is_financial_data_empty(result):
                    logger.info("Alternative extraction found financial data!")
                    return result
            
            # Strategy 2: Try different parts of the document
            text_length = len(text)
            if text_length > 8000:
                # Try middle section
                middle_start = text_length // 3
                middle_text = text[middle_start:middle_start + 8000]
                
                logger.info("Trying middle section of document...")
                result = await self._extract_financial_facts_core(middle_text)
                if not self._is_financial_data_empty(result):
                    logger.info("Found financial data in middle section!")
                    return result
                
                # Try end section
                end_text = text[-8000:]
                logger.info("Trying end section of document...")
                result = await self._extract_financial_facts_core(end_text)
                if not self._is_financial_data_empty(result):
                    logger.info("Found financial data in end section!")
                    return result
            
            logger.info("Alternative extraction methods did not find financial data")
            # Return empty structure with proper defaults
            return {
                'revenue': {'current_year': None, 'previous_year': None, 'currency': 'USD', 'period': 'annual'},
                'profit_loss': {'net_income': None, 'gross_profit': None, 'operating_profit': None, 'currency': 'USD'},
                'cash_flow': {'operating_cash_flow': None, 'free_cash_flow': None, 'currency': 'USD'},
                'debt_equity': {'total_debt': None, 'equity': None, 'debt_to_equity_ratio': None},
                'other_metrics': {'ebitda': None, 'margin_percentage': None, 'growth_rate': None}
            }
            
        except Exception as e:
            logger.error(f"Error in alternative financial extraction: {str(e)}")
            # Return empty structure with proper defaults on error
            return {
                'revenue': {'current_year': None, 'previous_year': None, 'currency': 'USD', 'period': 'annual'},
                'profit_loss': {'net_income': None, 'gross_profit': None, 'operating_profit': None, 'currency': 'USD'},
                'cash_flow': {'operating_cash_flow': None, 'free_cash_flow': None, 'currency': 'USD'},
                'debt_equity': {'total_debt': None, 'equity': None, 'debt_to_equity_ratio': None},
                'other_metrics': {'ebitda': None, 'margin_percentage': None, 'growth_rate': None}
            }

    async def _extract_financial_facts_core(self, text: str) -> Dict[str, Any]:
        """Core method for extracting financial facts using OpenAI GPT with structured output."""
        try:
            # Use provided text as-is (caller handles text length/selection)
            analysis_text = text
            
            logger.info(f"Sending {len(analysis_text)} characters to AI for financial extraction")
            logger.info(f"Text preview being analyzed: {analysis_text[:200]}...")
            
            response = await self.openai_client.beta.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": FINANCIAL_FACTS_SYSTEM_PROMPT},
                    {"role": "user", "content": FINANCIAL_FACTS_USER_TEMPLATE.format(text=analysis_text)}
                ],
                response_format=FinancialFacts,
                max_completion_tokens=settings.OPENAI_MAX_OUTPUT_TOKENS
            )
            
            # Check if response was truncated due to token limit
            if response.choices[0].finish_reason == "length":
                logger.warning("Financial facts extraction response was truncated due to token limit")
                # Continue processing instead of failing completely
            
            # Log response details for debugging
            logger.info(f"AI response finish reason: {response.choices[0].finish_reason}")
            
            financial_facts = response.choices[0].message.parsed
            if financial_facts:
                # Get the raw model dump
                raw_data = financial_facts.model_dump()
                logger.info(f"Raw AI extraction result: {raw_data}")
                
                # Clean and validate the data to ensure proper serialization
                cleaned_data = self._clean_financial_data(raw_data)
                logger.info(f"Cleaned extraction result: {cleaned_data}")
                return cleaned_data
            else:
                logger.warning("No financial facts parsed from response, returning empty structure")
                # Return empty structure instead of raising exception
                return {
                    'revenue': {'current_year': None, 'previous_year': None, 'currency': 'USD', 'period': 'annual'},
                    'profit_loss': {'net_income': None, 'gross_profit': None, 'operating_profit': None, 'currency': 'USD'},
                    'cash_flow': {'operating_cash_flow': None, 'free_cash_flow': None, 'currency': 'USD'},
                    'debt_equity': {'total_debt': None, 'equity': None, 'debt_to_equity_ratio': None},
                    'other_metrics': {'ebitda': None, 'margin_percentage': None, 'growth_rate': None}
                }
                    
        except Exception as e:
            logger.error(f"Error in AI financial facts extraction: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {repr(e)}")
            
            # Instead of re-raising, return empty structure to allow fallback processing
            logger.info("Returning empty financial structure due to AI extraction error")
            return {
                'revenue': {'current_year': None, 'previous_year': None, 'currency': 'USD', 'period': 'annual'},
                'profit_loss': {'net_income': None, 'gross_profit': None, 'operating_profit': None, 'currency': 'USD'},
                'cash_flow': {'operating_cash_flow': None, 'free_cash_flow': None, 'currency': 'USD'},
                'debt_equity': {'total_debt': None, 'equity': None, 'debt_to_equity_ratio': None},
                'other_metrics': {'ebitda': None, 'margin_percentage': None, 'growth_rate': None}
            }

    async def _extract_financial_facts_ai(self, text: str) -> Dict[str, Any]:
        """Extract financial facts using OpenAI GPT with structured output."""
        try:
            # Use more text for analysis - increase from 4000 to 8000 characters
            # This allows analysis of more content where financial data might be located
            analysis_text = text[:8000] if len(text) > 8000 else text
            
            return await self._extract_financial_facts_core(analysis_text)
                    
        except Exception as e:
            logger.error(f"Error in AI financial facts extraction: {str(e)}")
            raise e
    
    async def _extract_investment_data_ai(self, text: str) -> Dict[str, Any]:
        """Extract investment-related data using OpenAI GPT with structured output."""
        try:
            # Use more text for analysis - increase from 4000 to 8000 characters
            # This allows analysis of more content where investment data might be located
            analysis_text = text[:8000] if len(text) > 8000 else text
            
            # Try primary extraction approach
            result = await self._extract_investment_data_core(analysis_text)
            
            # Check if we got meaningful results
            if not self._is_investment_data_empty(result):
                return result
            
            logger.info("Primary investment data extraction returned empty results, trying alternative approaches...")
            
            # Try alternative extraction strategies
            result = await self._extract_investment_data_alternative(text)
            return result
                    
        except Exception as e:
            logger.error(f"Error in AI investment data extraction: {str(e)}")
            # Return empty structure instead of raising exception
            return {
                'investment_highlights': [],
                'risk_factors': [],
                'market_opportunity': {'market_size': None, 'growth_rate': None, 'competitive_position': None},
                'business_model': {'type': None, 'revenue_streams': [], 'key_customers': []},
                'strategic_initiatives': [],
                'exit_strategy': {'timeline': None, 'target_multiple': None, 'potential_buyers': []}
            }

    async def _extract_investment_data_core(self, text: str) -> Dict[str, Any]:
        """Core method for extracting investment data using OpenAI GPT with structured output."""
        try:
            # Use provided text as-is (caller handles text length/selection)
            analysis_text = text
            
            logger.info(f"Sending {len(analysis_text)} characters to AI for investment extraction")
            logger.info(f"Text preview being analyzed: {analysis_text[:200]}...")
            
            response = await self.openai_client.beta.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": INVESTMENT_DATA_SYSTEM_PROMPT},
                    {"role": "user", "content": INVESTMENT_DATA_USER_TEMPLATE.format(text=analysis_text)}
                ],
                response_format=InvestmentData,
                max_completion_tokens=settings.OPENAI_MAX_OUTPUT_TOKENS
            )
            
            # Check if response was truncated due to token limit
            if response.choices[0].finish_reason == "length":
                logger.warning("Investment data extraction response was truncated due to token limit")
                # Continue processing instead of failing completely
            
            # Log response details for debugging
            logger.info(f"AI response finish reason: {response.choices[0].finish_reason}")
            
            investment_data = response.choices[0].message.parsed
            if investment_data:
                # Get the raw model dump
                raw_data = investment_data.model_dump()
                logger.info(f"Raw AI investment extraction result: {raw_data}")
                
                # Clean and validate the data to ensure proper serialization
                cleaned_data = self._clean_investment_data(raw_data)
                logger.info(f"Cleaned investment extraction result: {cleaned_data}")
                return cleaned_data
            else:
                logger.warning("No investment data parsed from response, returning empty structure")
                # Return empty structure instead of raising exception
                return {
                    'investment_highlights': [],
                    'risk_factors': [],
                    'market_opportunity': {'market_size': None, 'growth_rate': None, 'competitive_position': None},
                    'business_model': {'type': None, 'revenue_streams': [], 'key_customers': []},
                    'strategic_initiatives': [],
                    'exit_strategy': {'timeline': None, 'target_multiple': None, 'potential_buyers': []}
                }
                    
        except Exception as e:
            logger.error(f"Error in AI investment data extraction: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {repr(e)}")
            
            # Instead of re-raising, return empty structure to allow fallback processing
            logger.info("Returning empty investment structure due to AI extraction error")
            return {
                'investment_highlights': [],
                'risk_factors': [],
                'market_opportunity': {'market_size': None, 'growth_rate': None, 'competitive_position': None},
                'business_model': {'type': None, 'revenue_streams': [], 'key_customers': []},
                'strategic_initiatives': [],
                'exit_strategy': {'timeline': None, 'target_multiple': None, 'potential_buyers': []}
            }

    def _is_investment_data_empty(self, data: Dict[str, Any]) -> bool:
        """
        Check if investment data is essentially empty (all fields are None/empty).
        
        Args:
            data: Investment data dictionary to check
            
        Returns:
            True if the data is empty/meaningless, False otherwise
        """
        if not data or not isinstance(data, dict):
            return True
        
        # Check if all list fields are empty
        list_fields = ['investment_highlights', 'risk_factors', 'strategic_initiatives']
        for field in list_fields:
            field_value = data.get(field, [])
            if isinstance(field_value, list) and len(field_value) > 0:
                # Check if any item in the list is meaningful (not empty string)
                if any(item and str(item).strip() for item in field_value):
                    return False
        
        # Check nested objects
        market_opp = data.get('market_opportunity', {})
        if isinstance(market_opp, dict):
            if (market_opp.get('market_size') is not None or 
                market_opp.get('growth_rate') is not None or 
                (market_opp.get('competitive_position') and str(market_opp.get('competitive_position')).strip())):
                return False
        
        business_model = data.get('business_model', {})
        if isinstance(business_model, dict):
            if (business_model.get('type') and str(business_model.get('type')).strip()):
                return False
            revenue_streams = business_model.get('revenue_streams', [])
            if isinstance(revenue_streams, list) and len(revenue_streams) > 0:
                if any(item and str(item).strip() for item in revenue_streams):
                    return False
            key_customers = business_model.get('key_customers', [])
            if isinstance(key_customers, list) and len(key_customers) > 0:
                if any(item and str(item).strip() for item in key_customers):
                    return False
        
        exit_strategy = data.get('exit_strategy', {})
        if isinstance(exit_strategy, dict):
            if (exit_strategy.get('timeline') and str(exit_strategy.get('timeline')).strip()):
                return False
            if exit_strategy.get('target_multiple') is not None:
                return False
            potential_buyers = exit_strategy.get('potential_buyers', [])
            if isinstance(potential_buyers, list) and len(potential_buyers) > 0:
                if any(item and str(item).strip() for item in potential_buyers):
                    return False
        
        # If all checks passed, consider it empty
        return True

    async def _extract_investment_data_alternative(self, text: str) -> Dict[str, Any]:
        """
        Alternative approach to extract investment data.
        
        Tries different strategies:
        1. Look at different parts of the document
        2. Use regex patterns to find investment keywords
        3. Focus on specific sections that might contain investment data
        
        Args:
            text: Full document text
            
        Returns:
            Investment data dictionary
        """
        try:
            logger.info("Trying alternative investment extraction approaches...")
            
            # Strategy 1: Look for investment keywords and extract surrounding context
            investment_keywords = [
                'investment', 'risk', 'opportunity', 'market', 'strategy',
                'business model', 'revenue stream', 'customer', 'exit',
                'acquisition', 'ipo', 'valuation', 'competitive', 'growth'
            ]
            
            # Find sections with investment keywords
            text_lower = text.lower()
            investment_sections = []
            
            for keyword in investment_keywords:
                start_pos = 0
                while True:
                    pos = text_lower.find(keyword, start_pos)
                    if pos == -1:
                        break
                    
                    # Extract 500 characters around the keyword
                    section_start = max(0, pos - 250)
                    section_end = min(len(text), pos + 250)
                    section = text[section_start:section_end]
                    investment_sections.append(section)
                    
                    start_pos = pos + 1
            
            # Remove duplicates and combine sections
            unique_sections = list(set(investment_sections))
            combined_investment_text = "\n\n".join(unique_sections[:10])  # Limit to first 10 unique sections
            
            if combined_investment_text:
                logger.info(f"Found {len(unique_sections)} sections with investment keywords")
                logger.info(f"Combined investment text length: {len(combined_investment_text)}")
                
                # Try AI extraction on the focused investment content
                result = await self._extract_investment_data_core(combined_investment_text)
                if not self._is_investment_data_empty(result):
                    logger.info("Alternative extraction found investment data!")
                    return result
            
            # Strategy 2: Try different parts of the document
            text_length = len(text)
            if text_length > 8000:
                # Try middle section
                middle_start = text_length // 3
                middle_text = text[middle_start:middle_start + 8000]
                
                logger.info("Trying middle section of document...")
                result = await self._extract_investment_data_core(middle_text)
                if not self._is_investment_data_empty(result):
                    logger.info("Found investment data in middle section!")
                    return result
                
                # Try end section
                end_text = text[-8000:]
                logger.info("Trying end section of document...")
                result = await self._extract_investment_data_core(end_text)
                if not self._is_investment_data_empty(result):
                    logger.info("Found investment data in end section!")
                    return result
            
            logger.info("Alternative extraction methods did not find investment data")
            # Return empty structure with proper defaults
            return {
                'investment_highlights': [],
                'risk_factors': [],
                'market_opportunity': {'market_size': None, 'growth_rate': None, 'competitive_position': None},
                'business_model': {'type': None, 'revenue_streams': [], 'key_customers': []},
                'strategic_initiatives': [],
                'exit_strategy': {'timeline': None, 'target_multiple': None, 'potential_buyers': []}
            }
            
        except Exception as e:
            logger.error(f"Error in alternative investment extraction: {str(e)}")
            # Return empty structure with proper defaults on error
            return {
                'investment_highlights': [],
                'risk_factors': [],
                'market_opportunity': {'market_size': None, 'growth_rate': None, 'competitive_position': None},
                'business_model': {'type': None, 'revenue_streams': [], 'key_customers': []},
                'strategic_initiatives': [],
                'exit_strategy': {'timeline': None, 'target_multiple': None, 'potential_buyers': []}
            }

    def _clean_investment_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and validate investment data to ensure proper serialization.
        
        Args:
            raw_data: Raw investment data from AI
            
        Returns:
            Cleaned and validated investment data
        """
        try:
            cleaned = {}
            
            # Clean list fields
            list_fields = ['investment_highlights', 'risk_factors', 'strategic_initiatives']
            for field in list_fields:
                field_value = raw_data.get(field, [])
                if isinstance(field_value, list):
                    # Filter out empty strings and ensure all items are strings
                    cleaned_list = [str(item).strip() for item in field_value if item and str(item).strip()]
                    cleaned[field] = cleaned_list
                else:
                    cleaned[field] = []
            
            # Clean market_opportunity
            market_opp = raw_data.get('market_opportunity', {})
            if isinstance(market_opp, dict):
                cleaned_market = {}
                cleaned_market['market_size'] = market_opp.get('market_size')
                cleaned_market['growth_rate'] = market_opp.get('growth_rate')
                competitive_pos = market_opp.get('competitive_position')
                cleaned_market['competitive_position'] = str(competitive_pos).strip() if competitive_pos else None
                cleaned['market_opportunity'] = cleaned_market
            else:
                cleaned['market_opportunity'] = {'market_size': None, 'growth_rate': None, 'competitive_position': None}
            
            # Clean business_model
            business_model = raw_data.get('business_model', {})
            if isinstance(business_model, dict):
                cleaned_business = {}
                bm_type = business_model.get('type')
                cleaned_business['type'] = str(bm_type).strip() if bm_type else None
                
                # Clean revenue_streams
                revenue_streams = business_model.get('revenue_streams', [])
                if isinstance(revenue_streams, list):
                    cleaned_business['revenue_streams'] = [str(item).strip() for item in revenue_streams if item and str(item).strip()]
                else:
                    cleaned_business['revenue_streams'] = []
                
                # Clean key_customers
                key_customers = business_model.get('key_customers', [])
                if isinstance(key_customers, list):
                    cleaned_business['key_customers'] = [str(item).strip() for item in key_customers if item and str(item).strip()]
                else:
                    cleaned_business['key_customers'] = []
                
                cleaned['business_model'] = cleaned_business
            else:
                cleaned['business_model'] = {'type': None, 'revenue_streams': [], 'key_customers': []}
            
            # Clean exit_strategy
            exit_strategy = raw_data.get('exit_strategy', {})
            if isinstance(exit_strategy, dict):
                cleaned_exit = {}
                timeline = exit_strategy.get('timeline')
                cleaned_exit['timeline'] = str(timeline).strip() if timeline else None
                cleaned_exit['target_multiple'] = exit_strategy.get('target_multiple')
                
                # Clean potential_buyers
                potential_buyers = exit_strategy.get('potential_buyers', [])
                if isinstance(potential_buyers, list):
                    cleaned_exit['potential_buyers'] = [str(item).strip() for item in potential_buyers if item and str(item).strip()]
                else:
                    cleaned_exit['potential_buyers'] = []
                
                cleaned['exit_strategy'] = cleaned_exit
            else:
                cleaned['exit_strategy'] = {'timeline': None, 'target_multiple': None, 'potential_buyers': []}
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning investment data: {str(e)}")
            # Return safe defaults on error
            return {
                'investment_highlights': [],
                'risk_factors': [],
                'market_opportunity': {'market_size': None, 'growth_rate': None, 'competitive_position': None},
                'business_model': {'type': None, 'revenue_streams': [], 'key_customers': []},
                'strategic_initiatives': [],
                'exit_strategy': {'timeline': None, 'target_multiple': None, 'potential_buyers': []}
            }

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

    def _extract_financial_facts_regex(self, text: str) -> Dict[str, Any]:
        """
        Heuristic regex-based extraction to populate financial facts
        when AI returns empty results. Returns only fields we can infer.
        """
        try:
            text_lower = text.lower()
            result = {
                'revenue': {'current_year': None, 'previous_year': None, 'currency': 'USD', 'period': 'annual'},
                'profit_loss': {'net_income': None, 'gross_profit': None, 'operating_profit': None, 'currency': 'USD'},
                'cash_flow': {'operating_cash_flow': None, 'free_cash_flow': None, 'currency': 'USD'},
                'debt_equity': {'total_debt': None, 'equity': None, 'debt_to_equity_ratio': None},
                'other_metrics': {'ebitda': None, 'margin_percentage': None, 'growth_rate': None}
            }

            def parse_amount(match_tuple):
                if not match_tuple:
                    return None
                value_str, scale = match_tuple
                try:
                    value = float(value_str.replace(',', ''))
                    if scale and scale.lower() in ('millions', 'million', 'm'):
                        value *= 1_000_000
                    elif scale and scale.lower() in ('thousands', 'thousand', 'k'):
                        value *= 1_000
                    elif scale and scale.lower() in ('billions', 'billion', 'b'):
                        value *= 1_000_000_000
                    return value
                except Exception:
                    return None

            def find_first_match(patterns):
                """Find the first match from a list of patterns."""
                for pattern in patterns:
                    m = re.search(pattern, text_lower, re.IGNORECASE)
                    if m:
                        return m
                return None

            # Revenue current
            if 'revenue_current' in self.heuristic_patterns:
                m = find_first_match(self.heuristic_patterns['revenue_current'])
                if m and result['revenue']['current_year'] is None:
                    result['revenue']['current_year'] = parse_amount((m.group(1), m.group(2) if len(m.groups()) > 1 else None))

            # Net income
            if 'net_income' in self.heuristic_patterns:
                m = find_first_match(self.heuristic_patterns['net_income'])
                if m:
                    result['profit_loss']['net_income'] = parse_amount((m.group(1), m.group(2) if len(m.groups()) > 1 else None))

            # Gross profit
            if 'gross_profit' in self.heuristic_patterns:
                m = find_first_match(self.heuristic_patterns['gross_profit'])
                if m:
                    result['profit_loss']['gross_profit'] = parse_amount((m.group(1), m.group(2) if len(m.groups()) > 1 else None))

            # Operating income
            if 'operating_income' in self.heuristic_patterns:
                m = find_first_match(self.heuristic_patterns['operating_income'])
                if m:
                    result['profit_loss']['operating_profit'] = parse_amount((m.group(1), m.group(2) if len(m.groups()) > 1 else None))

            # Operating cash flow
            if 'operating_cash_flow' in self.heuristic_patterns:
                m = find_first_match(self.heuristic_patterns['operating_cash_flow'])
                if m:
                    result['cash_flow']['operating_cash_flow'] = parse_amount((m.group(1), m.group(2) if len(m.groups()) > 1 else None))

            # Free cash flow
            if 'free_cash_flow' in self.heuristic_patterns:
                m = find_first_match(self.heuristic_patterns['free_cash_flow'])
                if m:
                    result['cash_flow']['free_cash_flow'] = parse_amount((m.group(1), m.group(2) if len(m.groups()) > 1 else None))

            # Total debt
            if 'total_debt' in self.heuristic_patterns:
                m = find_first_match(self.heuristic_patterns['total_debt'])
                if m:
                    result['debt_equity']['total_debt'] = parse_amount((m.group(1), m.group(2) if len(m.groups()) > 1 else None))

            # Stockholders equity
            if 'stockholders_equity' in self.heuristic_patterns:
                m = find_first_match(self.heuristic_patterns['stockholders_equity'])
                if m:
                    result['debt_equity']['equity'] = parse_amount((m.group(1), m.group(2) if len(m.groups()) > 1 else None))

            return self._clean_financial_data(result)
        except Exception as e:
            logger.warning(f"Regex fallback extraction failed: {str(e)}")
            return {
                'revenue': {'current_year': None, 'previous_year': None, 'currency': 'USD', 'period': 'annual'},
                'profit_loss': {'net_income': None, 'gross_profit': None, 'operating_profit': None, 'currency': 'USD'},
                'cash_flow': {'operating_cash_flow': None, 'free_cash_flow': None, 'currency': 'USD'},
                'debt_equity': {'total_debt': None, 'equity': None, 'debt_to_equity_ratio': None},
                'other_metrics': {'ebitda': None, 'margin_percentage': None, 'growth_rate': None}
            }
    
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