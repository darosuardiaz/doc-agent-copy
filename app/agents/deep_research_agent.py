"""
Deep Research Agent for analyzing financial documents and generating content outlines.
Based on the local-deep-researcher architecture but using OpenAI instead of Ollama.
"""
import logging
from typing import Dict, Any, List, Optional, Annotated
import asyncio
from datetime import datetime
import json

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.embedding_service import embedding_service
from app.database.models import Document, ResearchTask
from app.database.connection import get_db_session
from app.prompts.research_agent import (
    TOPIC_ANALYSIS_SYSTEM_PROMPT, TOPIC_ANALYSIS_HUMAN_TEMPLATE,
    RESEARCH_QUESTIONS_SYSTEM_PROMPT, RESEARCH_QUESTIONS_HUMAN_TEMPLATE,
    CONTENT_OUTLINE_SYSTEM_PROMPT, CONTENT_OUTLINE_HUMAN_TEMPLATE,
    DETAILED_CONTENT_SYSTEM_PROMPT, DETAILED_CONTENT_HUMAN_TEMPLATE
)

settings = get_settings()
logger = logging.getLogger(__name__)


class ResearchState(BaseModel):
    """State for the Deep Research Agent."""
    document_id: str
    topic: str
    research_query: str
    research_questions: List[str] = Field(default_factory=list)
    retrieved_information: List[Dict[str, Any]] = Field(default_factory=list)
    content_outline: Dict[str, Any] = Field(default_factory=dict)
    detailed_sections: Dict[str, Any] = Field(default_factory=dict)
    sources_used: List[Dict[str, Any]] = Field(default_factory=list)
    current_step: str = "start"
    errors: List[str] = Field(default_factory=list)
    task_id: Optional[str] = None


class DeepResearchAgent:
    """Agent for conducting deep research on financial documents."""
    
    def __init__(self):
        """Initialize the Deep Research Agent."""
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Create the research workflow
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the langraph workflow for deep research."""
        workflow = StateGraph(ResearchState)
        
        # Add nodes for each step of the research process
        workflow.add_node("analyze_topic", self._analyze_topic)
        workflow.add_node("generate_questions", self._generate_research_questions)
        workflow.add_node("retrieve_information", self._retrieve_information)
        workflow.add_node("create_outline", self._create_content_outline)
        workflow.add_node("generate_content", self._generate_detailed_content)
        workflow.add_node("finalize_research", self._finalize_research)
        
        # Define the workflow edges
        workflow.set_entry_point("analyze_topic")
        workflow.add_edge("analyze_topic", "generate_questions")
        workflow.add_edge("generate_questions", "retrieve_information")
        workflow.add_edge("retrieve_information", "create_outline")
        workflow.add_edge("create_outline", "generate_content")
        workflow.add_edge("generate_content", "finalize_research")
        workflow.add_edge("finalize_research", END)
        
        return workflow.compile()
    
    async def conduct_research(
            self, 
            document_id: str, 
            topic: str, 
            custom_query: Optional[str] = None
        ) -> Dict[str, Any]:
        """
        Conduct deep research on a document for a specific topic.
        
        Args:
            document_id: UUID of the document to research
            topic: Research topic (e.g., "Key Investment Highlights")
            custom_query: Optional custom research query
            
        Returns:
            Dictionary containing research results
        """
        try:
            logger.info(f"Starting deep research for document {document_id}, topic: {topic}")
            
            # Create research task in database
            task_id = await self._create_research_task(document_id, topic, custom_query or topic)
            
            # Initialize research state
            initial_state = ResearchState(
                document_id=document_id,
                topic=topic,
                research_query=custom_query or topic,
                task_id=task_id
            )
            
            # Execute the research workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Handle both dict and object responses from langraph
            if isinstance(final_state, dict):
                # If langraph returns a dictionary instead of the state object
                content_outline = final_state.get('content_outline', {})
                detailed_sections = final_state.get('detailed_sections', {})
                sources_used = final_state.get('sources_used', [])
                research_questions = final_state.get('research_questions', [])
                errors = final_state.get('errors', [])
            else:
                # Normal case where langraph returns the state object
                content_outline = final_state.content_outline
                detailed_sections = final_state.detailed_sections
                sources_used = final_state.sources_used
                research_questions = final_state.research_questions
                errors = final_state.errors
            
            # Update database with results
            await self._update_research_task(
                task_id,
                content_outline,
                detailed_sections,
                sources_used,
                "completed" if not errors else "failed",
                errors
            )
            
            logger.info(f"Deep research completed for document {document_id}")
            
            return {
                'task_id': task_id,
                'document_id': document_id,
                'topic': topic,
                'content_outline': content_outline,
                'detailed_sections': detailed_sections,
                'sources_used': sources_used,
                'research_questions': research_questions,
                'status': 'completed' if not errors else 'failed',
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error in deep research for document {document_id}: {str(e)}")
            if task_id:
                await self._update_research_task(task_id, {}, {}, [], "failed", [str(e)])
            raise e
    
    async def _analyze_topic(self, state: ResearchState) -> ResearchState:
        """Analyze the research topic and document context."""
        try:
            logger.info(f"Analyzing topic: {state.topic}")
            
            # Get document information
            with get_db_session() as db:
                document = db.query(Document).filter(Document.id == state.document_id).first()
                if not document:
                    state.errors.append(f"Document {state.document_id} not found")
                    return state
                
                # Extract document attributes within the session scope
                doc_filename = document.filename
                doc_page_count = document.page_count or "Unknown"
                doc_word_count = document.word_count or "Unknown"
            
            # Create analysis prompt
            analysis_prompt = ChatPromptTemplate.from_messages([
                ("system", TOPIC_ANALYSIS_SYSTEM_PROMPT),
                ("human", TOPIC_ANALYSIS_HUMAN_TEMPLATE)
            ])
            
            messages = analysis_prompt.format_messages(
                filename=doc_filename,
                page_count=doc_page_count,
                word_count=doc_word_count,
                topic=state.topic,
                research_query=state.research_query
            )
            
            response = await self.llm.ainvoke(messages)
            
            # Parse the response
            try:
                analysis = json.loads(response.content)
                state.content_outline.update({
                    'topic_analysis': analysis,
                    'document_context': {
                        'filename': doc_filename,
                        'page_count': doc_page_count,
                        'word_count': doc_word_count
                    }
                })
            except json.JSONDecodeError:
                logger.warning("Failed to parse topic analysis JSON")
                state.content_outline['topic_analysis'] = {'raw_response': response.content}
            
            state.current_step = "analyze_topic_complete"
            return state
            
        except Exception as e:
            logger.error(f"Error in analyze_topic: {str(e)}")
            state.errors.append(f"Topic analysis error: {str(e)}")
            return state
    
    async def _generate_research_questions(self, state: ResearchState) -> ResearchState:
        """Generate specific research questions based on the topic."""
        try:
            logger.info("Generating research questions")
            
            question_prompt = ChatPromptTemplate.from_messages([
                ("system", RESEARCH_QUESTIONS_SYSTEM_PROMPT),
                ("human", RESEARCH_QUESTIONS_HUMAN_TEMPLATE)
            ])
            
            analysis = state.content_outline.get('topic_analysis', {})
            
            messages = question_prompt.format_messages(
                topic=state.topic,
                research_query=state.research_query,
                analysis=json.dumps(analysis, indent=2)
            )
            
            response = await self.llm.ainvoke(messages)
            
            # Parse questions
            try:
                questions = json.loads(response.content)
                if isinstance(questions, list):
                    state.research_questions = questions
                else:
                    state.research_questions = [str(questions)]
            except json.JSONDecodeError:
                # Fallback: split by lines and clean up
                lines = response.content.split('\n')
                state.research_questions = [
                    line.strip(' -"•') for line in lines 
                    if line.strip() and '?' in line
                ]
            
            state.current_step = "questions_generated"
            return state
            
        except Exception as e:
            logger.error(f"Error generating research questions: {str(e)}")
            state.errors.append(f"Question generation error: {str(e)}")
            return state
    
    async def _retrieve_information(self, state: ResearchState) -> ResearchState:
        """Retrieve relevant information from the document using vector search."""
        try:
            logger.info("Retrieving information from document")
            
            all_retrieved_info = []
            sources_used = []
            
            # Search for each research question
            for i, question in enumerate(state.research_questions):
                try:
                    # Search for similar chunks
                    similar_chunks = await embedding_service.search_similar_chunks(
                        query=question,
                        document_id=state.document_id,
                        top_k=5,
                        similarity_threshold=0.6
                    )
                    
                    for chunk in similar_chunks:
                        info_entry = {
                            'question': question,
                            'question_index': i,
                            'content': chunk['content'],
                            'similarity_score': chunk['similarity_score'],
                            'chunk_id': chunk['chunk_id'],
                            'page_number': chunk.get('page_number'),
                            'chunk_index': chunk.get('chunk_index')
                        }
                        all_retrieved_info.append(info_entry)
                        
                        # Track sources
                        source_entry = {
                            'chunk_id': chunk['chunk_id'],
                            'page_number': chunk.get('page_number'),
                            'similarity_score': chunk['similarity_score'],
                            'question': question
                        }
                        if source_entry not in sources_used:
                            sources_used.append(source_entry)
                
                except Exception as e:
                    logger.warning(f"Error retrieving info for question '{question}': {str(e)}")
                    continue
            
            # Also do a general search for the main topic
            try:
                topic_chunks = await embedding_service.search_similar_chunks(
                    query=state.topic,
                    document_id=state.document_id,
                    top_k=8,
                    similarity_threshold=0.5
                )
                
                for chunk in topic_chunks:
                    info_entry = {
                        'question': f"General topic: {state.topic}",
                        'question_index': -1,
                        'content': chunk['content'],
                        'similarity_score': chunk['similarity_score'],
                        'chunk_id': chunk['chunk_id'],
                        'page_number': chunk.get('page_number'),
                        'chunk_index': chunk.get('chunk_index')
                    }
                    all_retrieved_info.append(info_entry)
                    
            except Exception as e:
                logger.warning(f"Error in general topic search: {str(e)}")
            
            state.retrieved_information = all_retrieved_info
            state.sources_used = sources_used
            state.current_step = "information_retrieved"
            
            logger.info(f"Retrieved {len(all_retrieved_info)} information pieces from {len(sources_used)} sources")
            return state
            
        except Exception as e:
            logger.error(f"Error retrieving information: {str(e)}")
            state.errors.append(f"Information retrieval error: {str(e)}")
            return state
    
    async def _create_content_outline(self, state: ResearchState) -> ResearchState:
        """Create a structured content outline based on retrieved information."""
        try:
            logger.info("Creating content outline")
            
            # Prepare context from retrieved information
            context_chunks = []
            for info in state.retrieved_information[:20]:  # Limit context size
                context_chunks.append(f"[Page {info.get('page_number', '?')}] {info['content'][:300]}...")
            
            context = "\n\n".join(context_chunks)
            
            outline_prompt = ChatPromptTemplate.from_messages([
                ("system", CONTENT_OUTLINE_SYSTEM_PROMPT),
                ("human", CONTENT_OUTLINE_HUMAN_TEMPLATE)
            ])
            
            messages = outline_prompt.format_messages(
                topic=state.topic,
                questions="\n".join([f"- {q}" for q in state.research_questions]),
                context=context
            )
            
            response = await self.llm.ainvoke(messages)
            
            # Parse the outline
            try:
                outline = json.loads(response.content)
                state.content_outline.update({
                    'structured_outline': outline,
                    'creation_timestamp': datetime.now().isoformat()
                })
            except json.JSONDecodeError:
                logger.warning("Failed to parse content outline JSON")
                state.content_outline.update({
                    'raw_outline': response.content,
                    'parsing_error': 'JSON parsing failed'
                })
            
            state.current_step = "outline_created"
            return state
            
        except Exception as e:
            logger.error(f"Error creating content outline: {str(e)}")
            state.errors.append(f"Outline creation error: {str(e)}")
            return state
    
    async def _generate_detailed_content(self, state: ResearchState) -> ResearchState:
        """Generate detailed content for each section of the outline."""
        try:
            logger.info("Generating detailed content")
            
            structured_outline = state.content_outline.get('structured_outline', {})
            main_sections = structured_outline.get('main_sections', [])
            
            detailed_sections = {}
            
            for i, section in enumerate(main_sections):
                try:
                    section_title = section.get('section_title', f'Section {i+1}')
                    
                    # Find relevant information for this section
                    relevant_info = []
                    for info in state.retrieved_information:
                        # Simple relevance check based on keywords
                        section_keywords = section_title.lower().split()
                        info_text = info['content'].lower()
                        
                        if any(keyword in info_text for keyword in section_keywords):
                            relevant_info.append(info)
                    
                    # Limit to top relevant pieces
                    relevant_info = relevant_info[:5]
                    
                    content_prompt = ChatPromptTemplate.from_messages([
                        ("system", DETAILED_CONTENT_SYSTEM_PROMPT),
                        ("human", DETAILED_CONTENT_HUMAN_TEMPLATE)
                    ])
                    
                    relevant_context = "\n\n".join([
                        f"[Page {info.get('page_number', '?')}] {info['content']}"
                        for info in relevant_info
                    ])
                    
                    messages = content_prompt.format_messages(
                        section_title=section_title,
                        key_points=", ".join(section.get('key_points', [])),
                        supporting_data=", ".join(section.get('supporting_data', [])),
                        importance=section.get('importance', 'Not specified'),
                        relevant_context=relevant_context or "No specific information found for this section."
                    )
                    
                    response = await self.llm.ainvoke(messages)
                    
                    detailed_sections[section_title] = {
                        'content': response.content,
                        'word_count': len(response.content.split()),
                        'sources_used': len(relevant_info),
                        'section_metadata': section
                    }
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Error generating content for section '{section_title}': {str(e)}")
                    detailed_sections[section_title] = {
                        'content': f"Error generating content: {str(e)}",
                        'error': True
                    }
            
            state.detailed_sections = detailed_sections
            state.current_step = "content_generated"
            
            return state
            
        except Exception as e:
            logger.error(f"Error generating detailed content: {str(e)}")
            state.errors.append(f"Content generation error: {str(e)}")
            return state
    
    async def _finalize_research(self, state: ResearchState) -> ResearchState:
        """Finalize the research process."""
        try:
            logger.info("Finalizing research")
            
            # Add final metadata
            state.content_outline.update({
                'research_completed_at': datetime.now().isoformat(),
                'total_sections_generated': len(state.detailed_sections),
                'total_sources_used': len(state.sources_used),
                'research_quality_score': self._calculate_quality_score(state)
            })
            
            state.current_step = "completed"
            return state
            
        except Exception as e:
            logger.error(f"Error finalizing research: {str(e)}")
            state.errors.append(f"Finalization error: {str(e)}")
            return state
    
    def _calculate_quality_score(self, state: ResearchState) -> float:
        """Calculate a quality score for the research (0-10)."""
        try:
            score = 5.0  # Base score
            
            # Points for comprehensive questions
            if len(state.research_questions) >= 5:
                score += 1.0
            
            # Points for information retrieval
            if len(state.retrieved_information) >= 10:
                score += 1.0
            
            # Points for high similarity scores
            high_similarity_count = sum(
                1 for info in state.retrieved_information 
                if info.get('similarity_score', 0) > 0.8
            )
            if high_similarity_count >= 5:
                score += 1.0
            
            # Points for detailed sections
            if len(state.detailed_sections) >= 3:
                score += 1.0
            
            # Points for no errors
            if not state.errors:
                score += 1.0
            
            return min(10.0, score)
            
        except Exception:
            return 5.0
    
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
            content_outline: Dict[str, Any],
            research_findings: Dict[str, Any], 
            sources_used: List[Dict[str, Any]],
            status: str,
            errors: List[str]
        ) -> None:
        """Update the research task in the database."""
        with get_db_session() as db:
            task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
            if task:
                task.content_outline = content_outline
                task.research_findings = research_findings
                task.sources_used = sources_used
                task.status = status
                task.completed_at = datetime.now()
                
                if errors:
                    task.error_message = "; ".join(errors)


# Global instance
deep_research_agent = DeepResearchAgent()