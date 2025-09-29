"""
Agent-style metadata extraction for financial documents.
Reimplements the old service using a LangGraph workflow similar to ChatAgentWithTools.
"""
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from app.config import get_settings
from app.database.models import Document, DocumentChunk
from app.database.connection import get_db_session
from app.database.schemas import FinancialFacts, InvestmentData
from app.prompts.metadata_extraction import (
    FINANCIAL_FACTS_SYSTEM_PROMPT,
    INVESTMENT_DATA_SYSTEM_PROMPT,
    DOCUMENT_SUMMARY_SYSTEM_PROMPT,
    DOCUMENT_SUMMARY_USER_TEMPLATE,
)
from app.tools import vector_search_tool


settings = get_settings()
logger = logging.getLogger(__name__)


class ExtractionState(BaseModel):
    """State for the Metadata Extraction Agent."""
    document_id: str
    full_text: Optional[str] = None
    chunk_count: int = 0
    financial_facts: Optional[Dict[str, Any]] = None
    investment_data: Optional[Dict[str, Any]] = None
    key_metrics: Optional[Dict[str, Any]] = None
    document_structure: Optional[Dict[str, Any]] = None
    document_images: Optional[List[Dict[str, Any]]] = None
    errors: List[str] = Field(default_factory=list)
    current_step: str = "start"


class MetadataExtractor:
    """Agent for extracting financial metadata using a staged workflow."""

    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            model="gpt-4.1-nano-2025-04-14",
            temperature=0.0,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self.workflow = self._create_workflow()


    def _create_workflow(self):
        workflow = StateGraph(ExtractionState)

        workflow.add_node("load_document", self._load_document)
        workflow.add_node("extract_financial_facts", self._extract_financial_facts)
        workflow.add_node("extract_investment_data", self._extract_investment_data)
        workflow.add_node("persist", self._save)

        workflow.add_edge("load_document", "extract_financial_facts")
        workflow.add_edge("extract_financial_facts", "extract_investment_data")
        workflow.add_edge("extract_investment_data", "persist")
        workflow.add_edge("persist", END)

        workflow.set_entry_point("load_document")
        return workflow.compile()
    
    async def extract_metadata(self, document_id: str) -> Dict[str, Any]:
        state = ExtractionState(document_id=document_id)
        final_state = await self.workflow.ainvoke(state)

        return {
            'financial_facts': final_state.get('financial_facts'),
            'investment_data': final_state.get('investment_data'),
            'key_metrics': final_state.get('key_metrics'),
            'document_structure': final_state.get('document_structure'),
            'extraction_timestamp': str(datetime.now(timezone.utc).isoformat()),
            'errors': final_state.get('errors') or None,
        }

    # --------------------
    # Nodes
    # --------------------

    async def _extract_financial_facts(self, state: ExtractionState) -> ExtractionState:
        try:
            vs = await vector_search_tool.search(
                query="financial statements; revenue; profit; income; profit; cash flow; debt; equity; EBITDA; margin; growth; guidance; bookings",
                document_id=state.document_id,
                top_k=12,
                similarity_threshold=0.55,
                max_tokens_per_source=800,
            )

            retrieved_chunks = vs.get("similar_chunks", [])
            relevant_pages = set(chunk.get("page_number") for chunk in retrieved_chunks)

            chunk_messages = [{"type": "text", "text": f"\n---\nChunk from page {chunk['page_number']} with similarity score {chunk['similarity_score']}:\n{chunk['content']}\n---"} for chunk in retrieved_chunks]
            image_messages = [{"type": "image_url", "image_url": {"url": img["image_uri"], "detail": "high"}} for img in state.document_images if img["page_number"] in relevant_pages]

            content = [
                {"type": "text", "text": "Task: Extract financial facts from images and text chunks"},
                *image_messages,
                *chunk_messages,
            ]

            messages = [SystemMessage(content=FINANCIAL_FACTS_SYSTEM_PROMPT), HumanMessage(content=content)]
            response = await self.llm.with_structured_output(FinancialFacts).ainvoke(messages)

            state.financial_facts = response.model_dump()
            state.current_step = "financial_facts_extracted"

            return state
        except Exception as e:
            logger.error(f"Financial facts extraction error: {str(e)}")
            state.errors.append(f"financial_facts: {str(e)}")
            state.financial_facts = self._empty_financial_facts()
            return state

    async def _extract_investment_data(self, state: ExtractionState) -> ExtractionState:
        try:
            vs = await vector_search_tool.search(
                query="Investment, risks, market opportunity, business model, strategy, exit.",
                document_id=state.document_id,
                top_k=12,
                similarity_threshold=0.55,
                max_tokens_per_source=800,
            )

            retrieved_chunks = vs.get("similar_chunks", [])
            relevant_pages = set(chunk.get("page_number") for chunk in retrieved_chunks)

            chunk_messages = [{"type": "text", "text": f"\n---\nChunk from page {chunk['page_number']} with similarity score {chunk['similarity_score']}:\n{chunk['content']}\n---"} for chunk in retrieved_chunks]
            image_messages = [{"type": "image_url", "image_url": {"url": img["image_uri"], "detail": "high"}} for img in state.document_images if img["page_number"] in relevant_pages]

            content = [
                {"type": "text", "text": "Task: Extract investment facts from images and text chunks"},
                *image_messages,
                *chunk_messages,
            ]

            messages = [SystemMessage(content=INVESTMENT_DATA_SYSTEM_PROMPT), HumanMessage(content=content)]
            response = await self.llm.with_structured_output(InvestmentData).ainvoke(messages)

            state.investment_data = response.model_dump()
            state.current_step = "investment_data_extracted"

            return state
        except Exception as e:
            logger.error(f"Investment data extraction error: {str(e)}")
            state.errors.append(f"investment_data: {str(e)}")
            state.investment_data = self._empty_investment_data()
            return state

    def _extract_document_structure(self, text: str) -> Dict[str, Any]:
        structure: Dict[str, Any] = {}
        section_patterns = [r'^[0-9]+\.\s+[A-Z]', r'^[IVX]+\.\s+[A-Z]', r'^[A-Z][A-Z\s]+$']
        sections = 0
        for pattern in section_patterns:
            sections += len(re.findall(pattern, text, re.MULTILINE))
        structure['estimated_sections'] = sections
        table_indicators = ['table', 'figure', '|', '\t']
        table_score = sum(text.lower().count(ind) for ind in table_indicators)
        structure['estimated_tables'] = min(table_score // 10, 50)
        bullet_patterns = [r'^\s*[•\-\*]\s+', r'^\s*\d+\.\s+']
        bullet_points = 0
        for pattern in bullet_patterns:
            bullet_points += len(re.findall(pattern, text, re.MULTILINE))
        structure['bullet_points'] = bullet_points
        word_count = len(text.split())
        structure['estimated_reading_time_minutes'] = max(1, word_count // 200)
        complexity = min(10, (sections * 0.5 + structure['estimated_tables'] * 0.3 + bullet_points * 0.1 + word_count / 1000))
        structure['complexity_score'] = round(complexity, 1)
        return structure
    
    async def _summarize_document(self, state: ExtractionState, max_length: int = 5000) -> str:
        try:
            messages = [
                SystemMessage(content=DOCUMENT_SUMMARY_SYSTEM_PROMPT.format(max_length=max_length)),
                HumanMessage(content=DOCUMENT_SUMMARY_USER_TEMPLATE.format(text=state.full_text[:max_length])),
            ]
            response = await self.llm.ainvoke(messages)
            return (response.content or "").strip()
        except Exception as e:
            logger.error(f"Error generating summary for document {state.document_id}: {str(e)}")
            return f"Error generating summary: {str(e)}"

    # --------------------
    # Helpers
    # --------------------

    async def _load_document(self, state: ExtractionState) -> ExtractionState:
        try:
            with get_db_session() as db:
                document = db.query(Document).filter(Document.id == state.document_id).first()
                if not document:
                    raise FileNotFoundError("Document not found in database")
                
                chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == state.document_id
                ).order_by(DocumentChunk.chunk_index).all()
                
                state.full_text = "\n\n".join([c.content for c in chunks])
                state.chunk_count = len(chunks)
                state.document_images = document.extracted_images or []
                
            state.document_structure = self._extract_document_structure(state.full_text or "")
            state.current_step = "loaded_text"
            return state
        except Exception as e:
            logger.error(f"Error loading document text: {str(e)}")
            state.errors.append(f"load_text: {str(e)}")
            return state

    async def _save(self, state: ExtractionState) -> ExtractionState:
        try:
            with get_db_session() as db:
                document = db.query(Document).filter(Document.id == state.document_id).first()
                if document:
                    document.financial_facts = state.financial_facts or self._empty_financial_facts()
                    document.investment_data = state.investment_data or self._empty_investment_data()
                    document.key_metrics = self._ensure_json_serializable(state.document_structure or {})
                    db.commit()
            state.current_step = "persisted"
            return state
        except Exception as e:
            logger.error(f"Persist error: {str(e)}")
            state.errors.append(f"persist: {str(e)}")
            return state

    def _ensure_json_serializable(self, data: Any) -> Any:
        try:
            if isinstance(data, dict):
                result = {}
                for k, v in data.items():
                    key = str(k) if not isinstance(k, str) else k
                    result[key] = self._ensure_json_serializable(v)
                return result
            if isinstance(data, (list, tuple, set)):
                return [self._ensure_json_serializable(x) for x in data]
            if isinstance(data, (str, int, float, bool)) or data is None:
                return data
            if hasattr(data, '__dict__'):
                return self._ensure_json_serializable(vars(data))
            return str(data)
        except Exception:
            return str(data)

    def _empty_financial_facts(self) -> Dict[str, Any]:
        return {
            'revenue': {'current_year': None, 'previous_year': None, 'currency': 'USD', 'period': 'annual'},
            'profit_loss': {'net_income': None, 'gross_profit': None, 'operating_profit': None, 'currency': 'USD'},
            'cash_flow': {'operating_cash_flow': None, 'free_cash_flow': None, 'currency': 'USD'},
            'debt_equity': {'total_debt': None, 'equity': None, 'debt_to_equity_ratio': None},
            'other_metrics': {'ebitda': None, 'margin_percentage': None, 'growth_rate': None},
        }

    def _empty_investment_data(self) -> Dict[str, Any]:
        return {
            'investment_highlights': [],
            'risk_factors': [],
            'market_opportunity': {'market_size': None, 'growth_rate': None, 'competitive_position': None},
            'business_model': {'type': None, 'revenue_streams': [], 'key_customers': []},
            'strategic_initiatives': [],
            'exit_strategy': {'timeline': None, 'target_multiple': None, 'potential_buyers': []},
        }
    


metadata_extractor = MetadataExtractor()

