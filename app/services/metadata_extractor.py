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
    FINANCIAL_FACTS_USER_TEMPLATE,
    INVESTMENT_DATA_USER_TEMPLATE,
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

        workflow.add_node("load_text", self._load_document_text)
        workflow.add_node("extract_financial_facts", self._node_extract_financial_facts)
        workflow.add_node("extract_investment_data", self._node_extract_investment_data)
        workflow.add_node("persist", self._node_persist)

        workflow.add_edge("load_text", "extract_financial_facts")
        workflow.add_edge("extract_financial_facts", "extract_investment_data")
        workflow.add_edge("extract_investment_data", "persist")
        workflow.add_edge("persist", END)

        workflow.set_entry_point("load_text")
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

    async def _load_document_text(self, state: ExtractionState) -> ExtractionState:
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

    async def _node_extract_financial_facts(self, state: ExtractionState) -> ExtractionState:
        try:
            # Retrieval-augmented: search for financial sections
            vs = await vector_search_tool.search(
                query="Extract financial statements, revenue, profit/loss, cash flow, debt, EBITDA, margins, growth.",
                document_id=state.document_id,
                top_k=12,
                similarity_threshold=0.55,
                max_tokens_per_source=800,
            )

            retrieved_chunks = vs.get("similar_chunks", [])
            relevant_images = state.document_images
            
            chunk_messages = [{"type": "text", "text": f"\n---\nChunk from page {chunk['page_number']} with similarity score {chunk['similarity_score']}:\n{chunk['content']}\n---"} for chunk in retrieved_chunks]
            image_messages = [{"type": "image_url", "image_url": {"url": img["image_uri"], "detail": "high"}} for img in relevant_images if img["image_uri"] is not None]

            # Build multimodal message content
            content = [
                {"type": "text", "text": "Task: look for financial figures in the image and the chunks"},
                *image_messages,
                *chunk_messages,
            ]

            messages = [SystemMessage(content=FINANCIAL_FACTS_SYSTEM_PROMPT), HumanMessage(content=content)]
            response = await self.llm.ainvoke(messages)

            raw = (response.content or "").strip()
            cleaned = self._safe_parse_financial_facts(raw)

            state.financial_facts = cleaned
            state.current_step = "financial_facts_extracted"
            return state
        except Exception as e:
            logger.error(f"Financial facts extraction error: {str(e)}")
            state.errors.append(f"financial_facts: {str(e)}")
            state.financial_facts = self._empty_financial_facts()
            return state

    async def _node_extract_investment_data(self, state: ExtractionState) -> ExtractionState:
        try:
            # Retrieval-augmented: search for investment-oriented sections
            vs = await vector_search_tool.search(
                query="Investment highlights, risks, market opportunity, business model, strategy, exit.",
                document_id=state.document_id,
                top_k=12,
                similarity_threshold=0.55,
                max_tokens_per_source=800,
            )

            retrieved_context = vs.get("formatted_results", "")

            system = INVESTMENT_DATA_SYSTEM_PROMPT
            user = INVESTMENT_DATA_USER_TEMPLATE.format(text=retrieved_context)

            messages = [SystemMessage(content=system), { 'role': 'user', 'content': user }]
            response = await self.llm.ainvoke(messages)

            raw = (response.content or "").strip()
            cleaned = self._safe_parse_investment_data(raw)

            state.investment_data = cleaned
            state.current_step = "investment_data_extracted"
            return state
        except Exception as e:
            logger.error(f"Investment data extraction error: {str(e)}")
            state.errors.append(f"investment_data: {str(e)}")
            state.investment_data = self._empty_investment_data()
            return state

    async def _node_persist(self, state: ExtractionState) -> ExtractionState:
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

    # --------------------
    # Helpers
    # --------------------
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
    
    def _clean_financial_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        def clean_currency(value: Any) -> str:
            if value is None or value == "null" or value == "":
                return "USD"
            if isinstance(value, str) and value.strip():
                return value.strip().upper()
            return "USD"
        
        def clean_num(value: Any) -> Any:
            if value is None or value == "null" or value == "":
                return None
            if isinstance(value, (int, float)):
                return value
            if isinstance(value, str):
                try:
                    return float(value) if '.' in value else int(value)
                except Exception:
                    return None
            return None
        
        cleaned: Dict[str, Any] = {}
        try:
            rev = data.get('revenue', {}) if isinstance(data, dict) else {}
            cleaned['revenue'] = {
                'current_year': clean_num(rev.get('current_year')),
                'previous_year': clean_num(rev.get('previous_year')),
                'currency': clean_currency(rev.get('currency')),
                'period': rev.get('period', 'annual') if rev.get('period') and rev.get('period') != 'null' else 'annual',
            }
            pl = data.get('profit_loss', {}) if isinstance(data, dict) else {}
            cleaned['profit_loss'] = {
                'net_income': clean_num(pl.get('net_income')),
                'gross_profit': clean_num(pl.get('gross_profit')),
                'operating_profit': clean_num(pl.get('operating_profit')),
                'currency': clean_currency(pl.get('currency')),
            }
            cf = data.get('cash_flow', {}) if isinstance(data, dict) else {}
            cleaned['cash_flow'] = {
                'operating_cash_flow': clean_num(cf.get('operating_cash_flow')),
                'free_cash_flow': clean_num(cf.get('free_cash_flow')),
                'currency': clean_currency(cf.get('currency')),
            }
            de = data.get('debt_equity', {}) if isinstance(data, dict) else {}
            cleaned['debt_equity'] = {
                'total_debt': clean_num(de.get('total_debt')),
                'equity': clean_num(de.get('equity')),
                'debt_to_equity_ratio': clean_num(de.get('debt_to_equity_ratio')),
            }
            om = data.get('other_metrics', {}) if isinstance(data, dict) else {}
            cleaned['other_metrics'] = {
                'ebitda': clean_num(om.get('ebitda')),
                'margin_percentage': clean_num(om.get('margin_percentage')),
                'growth_rate': clean_num(om.get('growth_rate')),
            }
            return cleaned
        except Exception:
            return data

    def _is_financial_data_empty(self, financial_data: Dict[str, Any]) -> bool:
        if not financial_data:
            return True
        numeric_values: List[Any] = []
        for _, section in financial_data.items():
            if isinstance(section, dict):
                for k, v in section.items():
                    if k not in ['currency', 'period']:
                        numeric_values.append(v)
        return all(v is None for v in numeric_values)

    def _is_investment_data_empty(self, data: Dict[str, Any]) -> bool:
        if not data or not isinstance(data, dict):
            return True
        if any((data.get('investment_highlights') or [])):
                    return False
        if any((data.get('risk_factors') or [])):
                return False
        mo = data.get('market_opportunity') or {}
        if any([mo.get('market_size') is not None, mo.get('growth_rate') is not None, bool((mo.get('competitive_position') or '').strip())]):
                return False
        bm = data.get('business_model') or {}
        if bool((bm.get('type') or '').strip()) or any(bm.get('revenue_streams') or []) or any(bm.get('key_customers') or []):
                    return False
        es = data.get('exit_strategy') or {}
        if bool((es.get('timeline') or '').strip()) or es.get('target_multiple') is not None or any(es.get('potential_buyers') or []):
                    return False
        return True

    def _safe_parse_financial_facts(self, raw: str) -> Dict[str, Any]:
        try:
            import json
            data = json.loads(raw)
        except Exception:
            # Some providers may return non-JSON; try to locate JSON substring
            try:
                import json
                start = raw.find('{')
                end = raw.rfind('}')
                data = json.loads(raw[start:end+1]) if start != -1 and end != -1 else {}
            except Exception:
                data = {}
        cleaned = self._clean_financial_data(data)
        if self._is_financial_data_empty(cleaned):
            return self._empty_financial_facts()
        return cleaned

    def _safe_parse_investment_data(self, raw: str) -> Dict[str, Any]:
        try:
            import json
            data = json.loads(raw)
        except Exception:
            try:
                import json
                start = raw.find('{')
                end = raw.rfind('}')
                data = json.loads(raw[start:end+1]) if start != -1 and end != -1 else {}
            except Exception:
                data = {}
        cleaned = self._clean_investment_data(data)
        if self._is_investment_data_empty(cleaned):
            return self._empty_investment_data()
        return cleaned

    def _clean_investment_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        try:
            cleaned: Dict[str, Any] = {}
            def clean_list(val: Any) -> List[str]:
                if isinstance(val, list):
                    return [str(x).strip() for x in val if x and str(x).strip()]
                return []

            cleaned['investment_highlights'] = clean_list(raw.get('investment_highlights', []))
            cleaned['risk_factors'] = clean_list(raw.get('risk_factors', []))

            mo = raw.get('market_opportunity', {}) if isinstance(raw, dict) else {}
            cleaned['market_opportunity'] = {
                'market_size': mo.get('market_size'),
                'growth_rate': mo.get('growth_rate'),
                'competitive_position': (str(mo.get('competitive_position')).strip() if mo.get('competitive_position') else None),
            }

            bm = raw.get('business_model', {}) if isinstance(raw, dict) else {}
            cleaned['business_model'] = {
                'type': (str(bm.get('type')).strip() if bm.get('type') else None),
                'revenue_streams': clean_list(bm.get('revenue_streams', [])),
                'key_customers': clean_list(bm.get('key_customers', [])),
            }

            es = raw.get('exit_strategy', {}) if isinstance(raw, dict) else {}
            cleaned['exit_strategy'] = {
                'timeline': (str(es.get('timeline')).strip() if es.get('timeline') else None),
                'target_multiple': es.get('target_multiple'),
                'potential_buyers': clean_list(es.get('potential_buyers', [])),
            }
            return cleaned
        except Exception:
            return self._empty_investment_data()
    
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
    
    async def summarize_document(self, document_id: str, max_length: int = 500) -> str:
        try:
            with get_db_session() as db:
                chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == document_id
                ).order_by(DocumentChunk.chunk_index).limit(5).all()
                if not chunks:
                    return "No content available for summarization."
            text = "\n\n".join([c.content for c in chunks])
            messages = [
                SystemMessage(content=DOCUMENT_SUMMARY_SYSTEM_PROMPT.format(max_length=max_length)),
                { 'role': 'user', 'content': DOCUMENT_SUMMARY_USER_TEMPLATE.format(text=text[:3000]) },
            ]
            response = await self.llm.ainvoke(messages)
            return (response.content or "").strip()
        except Exception as e:
            logger.error(f"Error generating summary for document {document_id}: {str(e)}")
            return f"Error generating summary: {str(e)}"


metadata_extractor = MetadataExtractor()

