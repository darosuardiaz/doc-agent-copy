"""
Deep Research Agent. Uses ChatOpenAI and Vector Search on indexed documents.
"""
import logging
from typing import Dict, Any, List, Optional, Literal
import asyncio
from datetime import datetime
import json

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from app.config import get_settings
from app.tools import vector_search_tool
from app.database.models import ResearchTask
from app.database.connection import get_db_session

settings = get_settings()
logger = logging.getLogger(__name__)

# Constants
MAX_TOKENS_PER_SOURCE = 1000
CHARS_PER_TOKEN = 4


class ResearchState(BaseModel):
    """State for the Deep Research Agent following reference implementation."""
    # Core state fields from reference
    research_topic: str
    search_query: str = ""
    research_loop_count: int = 0
    running_summary: str = ""
    sources_gathered: List[str] = Field(default_factory=list)
    vector_search_results: List[str] = Field(default_factory=list)
    
    # Additional fields for our implementation
    document_id: str
    task_id: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)


class ResearchStateInput(BaseModel):
    """Input schema for the research workflow."""
    research_topic: str
    document_id: str
    task_id: Optional[str] = None


class ResearchStateOutput(BaseModel):
    """Output schema for the research workflow."""
    running_summary: str
    sources_gathered: List[str]
    research_topic: str
    document_id: str
    task_id: Optional[str]
    errors: List[str]
    retrieved_chunks: List[Dict[str, Any]]


class Configuration(BaseModel):
    """Configuration for the research agent."""
    max_research_loops: int = Field(default=3, description="Maximum number of research loops")
    similarity_threshold: float = Field(default=0.6, description="Similarity threshold for vector search")
    top_k: int = Field(default=5, description="Number of top results to retrieve")
    temperature: float = Field(default=0.1, description="LLM temperature")
    

# Prompts following the reference implementation pattern
QUERY_WRITER_INSTRUCTIONS = """You are a research query specialist for financial document analysis.
Your task is to generate a concise, document-internal search query to find information within a single financial document (not the web).

Rules:
- Target headings, section titles, and key phrases likely present in the document
- Avoid web operators, URLs, tickers, or site: filters
- Keep it short (3-12 words), descriptive, and specific

Current Date: {current_date}
Research Topic: {research_topic}

Generate a specific, focused search query optimized for semantic similarity search within financial documents."""

QUERY_WRITER_JSON_INSTRUCTIONS = """
Respond with a JSON object in the following format:
{
    "query": "Your specific search query",
    "rationale": "Brief explanation of why this query is relevant"
}"""

SUMMARIZER_INSTRUCTIONS = """You are a financial research analyst creating comprehensive summaries.
Your task is to synthesize information from document chunks into a coherent summary.

Focus on:
- Key financial metrics and data points
- Strategic insights and implications
- Investment highlights and risks
- Specific facts and figures from the source material

FORMATTING REQUIREMENTS:
- Format your response in clean, well-structured Markdown
- Use appropriate headings (## for main sections, ### for subsections)
- Use bullet points for lists of key points
- Use **bold** for important metrics and figures
- Use *italics* for emphasis where appropriate
- Include tables using markdown syntax for financial data when relevant

Be specific and cite information accurately."""

REFLECTION_INSTRUCTIONS = """You are analyzing a research summary to identify knowledge gaps.
Research Topic: {research_topic}

Review the current summary and identify:
1. What important information is still missing?
2. What aspects need more detail or clarification?
3. What follow-up questions would provide valuable insights?

Generate one concise, document-internal follow-up search query (no web operators or site: filters) that best addresses the most important gap."""

REFLECTION_JSON_INSTRUCTIONS = """
Respond with a JSON object in the following format:
{
    "knowledge_gap": "Description of what information is missing or needs clarification",
    "follow_up_query": "A specific search query to address this gap"
}"""


def get_current_date():
    """Get current date in readable format."""
    return datetime.now().strftime("%B %d, %Y")


def deduplicate_and_format_sources(chunks: List[Dict[str, Any]], max_tokens_per_source: int) -> str:
    """Format vector search results into a readable string."""
    formatted_sources = []
    seen_content = set()
    
    for chunk in chunks:
        content = chunk.get('content', '')
        chunk_id = chunk.get('chunk_id', '')
        
        # Skip if we've seen similar content
        content_preview = content[:100]
        if content_preview in seen_content:
            continue
        seen_content.add(content_preview)
        
        # Truncate if too long
        max_chars = max_tokens_per_source * CHARS_PER_TOKEN
        if len(content) > max_chars:
            content = content[:max_chars] + "..."
        
        # Format the chunk
        page_num = chunk.get('page_number', 'Unknown')
        similarity = chunk.get('similarity_score', 0)
        
        formatted_source = f"[Page {page_num} | Similarity: {similarity:.2f}]\n{content}\n"
        formatted_sources.append(formatted_source)
    
    return "\n---\n".join(formatted_sources)


def format_sources(chunks: List[Dict[str, Any]]) -> str:
    """Format sources for citation."""
    sources = []
    for chunk in chunks:
        page_num = chunk.get('page_number', 'Unknown')
        chunk_idx = chunk.get('chunk_index', 'Unknown')
        sources.append(f"- Page {page_num}, Chunk {chunk_idx}")
    return "\n".join(sources)


class DeepResearchAgent:
    """Agent for conducting deep research on financial documents."""
    
    def __init__(self):
        """Initialize the Deep Research Agent."""
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        self.config = Configuration()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the langraph workflow following reference implementation."""
        workflow = StateGraph(
            ResearchState,
            input=ResearchStateInput,
            output=ResearchStateOutput,
            config_schema=Configuration
        )
        
        # Add nodes following reference pattern
        workflow.add_node("generate_query", self._generate_query)
        workflow.add_node("vector_search", self._vector_search)
        workflow.add_node("summarize_sources", self._summarize_sources)
        workflow.add_node("reflect_on_summary", self._reflect_on_summary)
        workflow.add_node("finalize_summary", self._finalize_summary)
        
        # Add edges following reference pattern
        workflow.add_edge(START, "generate_query")
        workflow.add_edge("generate_query", "vector_search")
        workflow.add_edge("vector_search", "summarize_sources")
        workflow.add_edge("summarize_sources", "reflect_on_summary")
        workflow.add_conditional_edges("reflect_on_summary", self._route_research)
        workflow.add_edge("finalize_summary", END)
        
        return workflow.compile()
    
    async def conduct_research(
            self, 
            document_id: str, 
            topic: str, 
            custom_query: Optional[str] = None,
            task_id: Optional[str] = None
        ) -> Dict[str, Any]:
        """Conduct deep research on a document for a specific topic."""
        try:
            logger.info(f"Starting deep research for document {document_id}, topic: {topic}")
            
            # Create research task in database if not provided
            if not task_id:
                task_id = await self._create_research_task(document_id, topic, custom_query or topic)
            
            # Initialize research state
            initial_state = ResearchStateInput(
                research_topic=topic,
                document_id=document_id,
                task_id=task_id
            )
            
            # Execute the research workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Handle the response
            if isinstance(final_state, dict):
                running_summary = final_state.get('running_summary', '')
                sources_gathered = final_state.get('sources_gathered', [])
                errors = final_state.get('errors', [])
                retrieved_chunks = final_state.get('retrieved_chunks', [])
            else:
                running_summary = final_state.running_summary
                sources_gathered = final_state.sources_gathered
                errors = final_state.errors
                retrieved_chunks = final_state.retrieved_chunks

            # Deduplicate sources and format them
            seen_pairs = set()
            structured_sources = []
            for ch in retrieved_chunks or []:
                page = ch.get('page_number')
                content = ch.get('content')
                relevance_score = ch.get('similarity_score')
                
                if page is None or content is None or relevance_score is None:
                    continue
                
                pair = (page, content[:50]) # Use a preview of content to deduplicate
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                
                structured_sources.append({
                    "page": page, 
                    "content": content,
                    "relevance_score": relevance_score
                })
            
            # Update database with results
            await self._update_research_task(
                task_id,
                running_summary,
                structured_sources,
                "completed" if not errors else "failed",
                errors
            )
            
            logger.info(f"Deep research completed for document {document_id}")
            
            return {
                'task_id': task_id,
                'document_id': document_id,
                'topic': topic,
                'summary': running_summary,
                'sources': structured_sources,
                'status': 'completed' if not errors else 'failed',
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error in deep research for document {document_id}: {str(e)}")
            if task_id:
                await self._update_research_task(task_id, "", [], "failed", [str(e)])
            raise e
    
    async def _generate_query(self, state: ResearchState) -> Dict[str, Any]:
        """Generate a search query based on the research topic."""
        try:
            current_date = get_current_date()
            formatted_prompt = QUERY_WRITER_INSTRUCTIONS.format(
                current_date=current_date,
                research_topic=state.research_topic
            )
            
            messages = [
                SystemMessage(content=formatted_prompt + "\n" + QUERY_WRITER_JSON_INSTRUCTIONS),
                HumanMessage(content="Generate a query for searching within this financial document:")
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                parsed_json = json.loads(response.content)
                search_query = parsed_json.get("query", state.research_topic)
            except json.JSONDecodeError:
                logger.warning("Failed to parse query JSON, using fallback")
                search_query = f"Tell me about {state.research_topic}"
            
            return {"search_query": search_query}
            
        except Exception as e:
            logger.error(f"Error generating query: {str(e)}")
            state.errors.append(f"Query generation error: {str(e)}")
            return {"search_query": state.research_topic}
    
    async def _vector_search(self, state: ResearchState) -> Dict[str, Any]:
        """Perform vector search using the generated query."""
        try:
            logger.info(f"Performing vector search with query: {state.search_query}")

            result = await vector_search_tool.search(
                query=state.search_query,
                document_id=state.document_id,
                top_k=self.config.top_k,
                similarity_threshold=self.config.similarity_threshold,
                max_tokens_per_source=MAX_TOKENS_PER_SOURCE,
            )

            similar_chunks = result.get("similar_chunks", [])
            search_str = result.get("formatted_results", "")
            sources_str = result.get("formatted_sources", "")

            return {
                "sources_gathered": state.sources_gathered + [sources_str],
                "research_loop_count": state.research_loop_count + 1,
                "vector_search_results": state.vector_search_results + [search_str],
                "retrieved_chunks": state.retrieved_chunks + similar_chunks,
            }
            
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            state.errors.append(f"Vector search error: {str(e)}")
            return {
                "research_loop_count": state.research_loop_count + 1,
                "vector_search_results": state.vector_search_results + ["No results found"]
            }
    
    async def _summarize_sources(self, state: ResearchState) -> Dict[str, Any]:
        """Summarize the vector search results."""
        try:
            existing_summary = state.running_summary
            most_recent_search = state.vector_search_results[-1] if state.vector_search_results else ""
            
            if existing_summary:
                human_message_content = (
                    f"<Existing Summary>\n{existing_summary}\n</Existing Summary>\n\n"
                    f"<New Context>\n{most_recent_search}\n</New Context>\n"
                    f"Update the Existing Summary with the New Context on this topic:\n"
                    f"<User Input>\n{state.research_topic}\n</User Input>\n"
                )
            else:
                human_message_content = (
                    f"<Context>\n{most_recent_search}\n</Context>\n"
                    f"Create a Summary using the Context on this topic:\n"
                    f"<User Input>\n{state.research_topic}\n</User Input>\n"
                )
            
            messages = [
                SystemMessage(content=SUMMARIZER_INSTRUCTIONS),
                HumanMessage(content=human_message_content)
            ]
            
            response = await self.llm.ainvoke(messages)
            running_summary = response.content
            
            return {"running_summary": running_summary}
            
        except Exception as e:
            logger.error(f"Error summarizing sources: {str(e)}")
            state.errors.append(f"Summarization error: {str(e)}")
            return {"running_summary": state.running_summary}
    
    async def _reflect_on_summary(self, state: ResearchState) -> Dict[str, Any]:
        """Reflect on the summary to identify knowledge gaps."""
        try:
            formatted_prompt = REFLECTION_INSTRUCTIONS.format(
                research_topic=state.research_topic
            )
            
            messages = [
                SystemMessage(content=formatted_prompt + "\n" + REFLECTION_JSON_INSTRUCTIONS),
                HumanMessage(
                    content=f"Reflect on our existing knowledge:\n===\n{state.running_summary}\n===\n"
                    f"Identify a knowledge gap and generate a follow-up search query:"
                )
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                parsed_json = json.loads(response.content)
                search_query = parsed_json.get("follow_up_query", f"More details about {state.research_topic}")
            except json.JSONDecodeError:
                logger.warning("Failed to parse reflection JSON, using fallback")
                search_query = f"Additional information about {state.research_topic}"
            
            return {"search_query": search_query}
            
        except Exception as e:
            logger.error(f"Error in reflection: {str(e)}")
            state.errors.append(f"Reflection error: {str(e)}")
            return {"search_query": state.research_topic}
    
    async def _finalize_summary(self, state: ResearchState) -> Dict[str, Any]:
        """Finalize the research summary."""
        try:
            # Deduplicate sources
            seen_sources = set()
            unique_sources = []
            
            for source in state.sources_gathered:
                for line in source.split("\n"):
                    if line.strip() and line not in seen_sources:
                        seen_sources.add(line)
                        unique_sources.append(line)
            
            return {"running_summary": state.running_summary}
            
        except Exception as e:
            logger.error(f"Error finalizing summary: {str(e)}")
            state.errors.append(f"Finalization error: {str(e)}")
            return {"running_summary": state.running_summary}
    
    def _route_research(self, state: ResearchState) -> Literal["finalize_summary", "vector_search"]:
        """Route the research flow based on loop count."""
        if state.research_loop_count < self.config.max_research_loops:
            return "vector_search"
        else:
            return "finalize_summary"
    
    async def _create_research_task(self, document_id: str, topic: str, query: str) -> str:
        """Create a research task in the database."""
        with get_db_session() as db:
            task = ResearchTask(
                document_id=document_id,
                topic=topic,
                research_query=query,
                status="in_progress"
            )
            db.add(task)
            db.flush()  # To get the ID
            task_id = str(task.id)
        return task_id
    
    async def _update_research_task(
            self, 
            task_id: str, 
            summary: str,
            sources: List[str],
            status: str,
            errors: List[str]
        ) -> None:
        """Update the research task in the database."""
        with get_db_session() as db:
            task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
            if task:
                task.research_findings = {"summary": summary}
                task.sources_used = sources
                task.status = status
                task.completed_at = datetime.now()
                
                if errors:
                    task.error_message = "; ".join(errors)


# Global instance
deep_research_agent = DeepResearchAgent()