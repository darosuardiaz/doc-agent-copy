"""
Chat/RAG Agent for conversational interaction with financial documents.
Uses Pinecone for retrieval-augmented generation with document context.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
import asyncio
from datetime import datetime
import json

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.embedding_service import embedding_service
from app.database.models import Document, ChatSession, ChatMessage
from app.database.connection import get_db_session
from app.prompts.chat_agent import FINANCIAL_ANALYST_SYSTEM_PROMPT, RAG_CONTEXT_TEMPLATE

settings = get_settings()
logger = logging.getLogger(__name__)


class ChatState(BaseModel):
    """State for the Chat/RAG Agent."""
    message: str
    session_id: Optional[str] = None
    document_id: Optional[str] = None
    use_rag: bool = True
    chat_history: List[Dict[str, str]] = Field(default_factory=list)
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    context_used: str = ""
    response: str = ""
    sources_used: List[Dict[str, Any]] = Field(default_factory=list)
    response_metadata: Dict[str, Any] = Field(default_factory=dict)
    current_step: str = "start"
    errors: List[str] = Field(default_factory=list)


class ChatRAGAgent:
    """Agent for conversational interaction with financial documents using RAG."""
    
    def __init__(self):
        """Initialize the Chat/RAG Agent."""
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,  # Slightly more creative for conversation
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Create the chat workflow
        self.workflow = self._create_workflow()
        
        # System prompt for financial document conversations
        self.system_prompt = FINANCIAL_ANALYST_SYSTEM_PROMPT
    
    def _create_workflow(self) -> StateGraph:
        """Create the langraph workflow for chat interactions."""
        workflow = StateGraph(ChatState)
        
        # Add nodes for each step of the chat process
        workflow.add_node("load_context", self._load_chat_context)
        workflow.add_node("retrieve_information", self._retrieve_relevant_information)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("save_interaction", self._save_chat_interaction)
        
        # Define conditional routing
        workflow.add_conditional_edges(
            "load_context",
            self._should_retrieve,
            {
                "retrieve": "retrieve_information",
                "generate": "generate_response"
            }
        )
        
        workflow.add_edge("retrieve_information", "generate_response")
        workflow.add_edge("generate_response", "save_interaction")
        workflow.add_edge("save_interaction", END)
        
        # Set entry point
        workflow.set_entry_point("load_context")
        
        return workflow.compile()
    
    async def chat(
            self, 
            message: str, 
            session_id: Optional[str] = None,
            document_id: Optional[str] = None,
            use_rag: bool = True
        ) -> Dict[str, Any]:
        """
        Process a chat message and generate a response.
        
        Args:
            message: User's message
            session_id: Optional chat session ID
            document_id: Optional document ID for context
            use_rag: Whether to use retrieval-augmented generation
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            start_time = asyncio.get_event_loop().time()
            logger.info(f"Processing chat message: {message[:50]}...")
            
            # Create or get session
            if not session_id:
                session_id = await self._create_chat_session(document_id)
            
            # Initialize chat state
            initial_state = ChatState(
                message=message,
                session_id=session_id,
                document_id=document_id,
                use_rag=use_rag
            )
            
            # Execute the chat workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            response_time = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"Chat response generated in {response_time:.2f}s")
            
            return {
                'message': final_state.response,
                'session_id': session_id,
                'sources_used': final_state.sources_used if use_rag else None,
                'response_time': response_time,
                'token_count': final_state.response_metadata.get('token_count'),
                'context_chunks_used': len(final_state.retrieved_chunks) if use_rag else 0,
                'errors': final_state.errors if final_state.errors else None
            }
            
        except Exception as e:
            logger.error(f"Error in chat processing: {str(e)}")
            return {
                'message': f"I apologize, but I encountered an error processing your message: {str(e)}",
                'session_id': session_id,
                'sources_used': None,
                'response_time': 0,
                'error': str(e)
            }
    
    async def _load_chat_context(self, state: ChatState) -> ChatState:
        """Load chat history and context."""
        try:
            if state.session_id:
                # Load recent chat history
                with get_db_session() as db:
                    recent_messages = db.query(ChatMessage).filter(
                        ChatMessage.session_id == state.session_id
                    ).order_by(ChatMessage.created_at.desc()).limit(10).all()
                    
                    # Convert to chat history format (reverse order)
                    chat_history = []
                    for msg in reversed(recent_messages):
                        chat_history.append({
                            'role': msg.role,
                            'content': msg.content
                        })
                    
                    state.chat_history = chat_history
            
            state.current_step = "context_loaded"
            return state
            
        except Exception as e:
            logger.error(f"Error loading chat context: {str(e)}")
            state.errors.append(f"Context loading error: {str(e)}")
            return state
    
    def _should_retrieve(self, state: ChatState) -> str:
        """Decide whether to retrieve information based on the message."""
        if not state.use_rag or not state.document_id:
            return "generate"
        
        # Simple heuristic: if the message is a question or asks for specific information
        message_lower = state.message.lower()
        retrieval_keywords = [
            'what', 'how', 'when', 'where', 'why', 'who', 'which',
            'tell me', 'explain', 'show me', 'find', 'search',
            'revenue', 'profit', 'financial', 'investment', 'data',
            'metrics', 'performance', 'growth', 'risk'
        ]
        
        if any(keyword in message_lower for keyword in retrieval_keywords):
            return "retrieve"
        else:
            return "generate"  # For general conversation, greetings, etc.
    
    async def _retrieve_relevant_information(self, state: ChatState) -> ChatState:
        """Retrieve relevant information from the document."""
        try:
            logger.info("Retrieving relevant information for chat")
            
            # Search for relevant chunks
            similar_chunks = await embedding_service.search_similar_chunks(
                query=state.message,
                document_id=state.document_id,
                top_k=8,
                similarity_threshold=0.6
            )
            
            state.retrieved_chunks = similar_chunks
            
            # Create context string from retrieved chunks
            context_parts = []
            sources_used = []
            
            for i, chunk in enumerate(similar_chunks):
                # Format context
                page_info = f"Page {chunk.get('page_number', '?')}" if chunk.get('page_number') else "Source document"
                context_parts.append(f"[{page_info}] {chunk['content'][:500]}...")
                
                # Track sources
                sources_used.append({
                    'chunk_id': chunk['chunk_id'],
                    'page_number': chunk.get('page_number'),
                    'similarity_score': chunk['similarity_score'],
                    'preview': chunk['content'][:100] + "..."
                })
            
            state.context_used = "\n\n".join(context_parts)
            state.sources_used = sources_used
            
            # Also try to get document metadata for additional context
            if state.document_id:
                with get_db_session() as db:
                    document = db.query(Document).filter(Document.id == state.document_id).first()
                    if document and document.financial_facts:
                        # Add key financial facts to context
                        facts_summary = "Key Financial Facts:\n"
                        for key, value in document.financial_facts.items():
                            if isinstance(value, dict) and value:
                                facts_summary += f"- {key}: {value}\n"
                        
                        state.context_used = facts_summary + "\n\n" + state.context_used
            
            state.current_step = "information_retrieved"
            logger.info(f"Retrieved {len(similar_chunks)} relevant chunks")
            
            return state
            
        except Exception as e:
            logger.error(f"Error retrieving information: {str(e)}")
            state.errors.append(f"Information retrieval error: {str(e)}")
            # Continue without RAG if retrieval fails
            state.current_step = "information_retrieved"
            return state
    
    async def _generate_response(self, state: ChatState) -> ChatState:
        """Generate the chat response using the LLM."""
        try:
            logger.info("Generating chat response")
            
            # Prepare messages for the LLM
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add chat history
            for msg in state.chat_history[-6:]:  # Last 6 messages for context
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))
            
            # Prepare the current message with context
            if state.use_rag and state.context_used:
                user_message = RAG_CONTEXT_TEMPLATE.format(
                    context=state.context_used,
                    message=state.message
                )
            else:
                user_message = state.message
            
            messages.append(HumanMessage(content=user_message))
            
            # Generate response
            response = await self.llm.ainvoke(messages)
            
            state.response = response.content
            state.response_metadata = {
                'token_count': self._estimate_tokens(response.content),
                'model_used': settings.OPENAI_MODEL,
                'context_length': len(state.context_used) if state.context_used else 0
            }
            
            state.current_step = "response_generated"
            return state
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            state.errors.append(f"Response generation error: {str(e)}")
            state.response = f"I apologize, but I encountered an error generating a response: {str(e)}"
            return state
    
    async def _save_chat_interaction(self, state: ChatState) -> ChatState:
        """Save the chat interaction to the database."""
        try:
            if state.session_id:
                with get_db_session() as db:
                    # Save user message
                    user_message = ChatMessage(
                        session_id=state.session_id,
                        role="user",
                        content=state.message,
                        token_count=self._estimate_tokens(state.message)
                    )
                    db.add(user_message)
                    
                    # Save assistant response
                    assistant_message = ChatMessage(
                        session_id=state.session_id,
                        role="assistant",
                        content=state.response,
                        token_count=state.response_metadata.get('token_count'),
                        model_used=state.response_metadata.get('model_used'),
                        response_time=state.response_metadata.get('response_time'),
                        retrieved_chunks=state.sources_used if state.use_rag else None,
                        similarity_scores=[s.get('similarity_score') for s in state.sources_used] if state.sources_used else None
                    )
                    db.add(assistant_message)
                    
                    # Update session last activity
                    session = db.query(ChatSession).filter(ChatSession.id == state.session_id).first()
                    if session:
                        session.last_activity = datetime.now()
            
            state.current_step = "interaction_saved"
            return state
            
        except Exception as e:
            logger.error(f"Error saving chat interaction: {str(e)}")
            state.errors.append(f"Save interaction error: {str(e)}")
            return state
    
    async def _create_chat_session(self, document_id: Optional[str] = None) -> str:
        """Create a new chat session."""
        with get_db_session() as db:
            session = ChatSession(
                document_id=document_id,
                session_name=f"Chat Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                system_prompt=self.system_prompt[:1000]  # Truncate if too long
            )
            db.add(session)
            db.flush()
            session_id = str(session.id)
        
        logger.info(f"Created new chat session: {session_id}")
        return session_id
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        return len(text.split()) * 1.3  # Rough approximation
    
    async def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a session."""
        try:
            with get_db_session() as db:
                messages = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).order_by(ChatMessage.created_at).limit(limit).all()
                
                history = []
                for msg in messages:
                    history.append({
                        'id': str(msg.id),
                        'role': msg.role,
                        'content': msg.content,
                        'created_at': msg.created_at.isoformat(),
                        'token_count': msg.token_count,
                        'sources_used': len(msg.retrieved_chunks) if msg.retrieved_chunks else 0
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            return []
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a chat session."""
        try:
            with get_db_session() as db:
                session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
                if session:
                    message_count = db.query(ChatMessage).filter(
                        ChatMessage.session_id == session_id
                    ).count()
                    
                    return {
                        'id': str(session.id),
                        'document_id': str(session.document_id) if session.document_id else None,
                        'session_name': session.session_name,
                        'created_at': session.created_at.isoformat(),
                        'last_activity': session.last_activity.isoformat(),
                        'message_count': message_count,
                        'is_active': session.is_active
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting session info: {str(e)}")
            return None
    
    async def list_user_sessions(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """List chat sessions for a user."""
        try:
            with get_db_session() as db:
                query = db.query(ChatSession)
                if user_id:
                    query = query.filter(ChatSession.user_id == user_id)
                
                sessions = query.order_by(ChatSession.last_activity.desc()).limit(limit).all()
                
                session_list = []
                for session in sessions:
                    message_count = db.query(ChatMessage).filter(
                        ChatMessage.session_id == session.id
                    ).count()
                    
                    session_list.append({
                        'id': str(session.id),
                        'session_name': session.session_name,
                        'document_id': str(session.document_id) if session.document_id else None,
                        'created_at': session.created_at.isoformat(),
                        'last_activity': session.last_activity.isoformat(),
                        'message_count': message_count,
                        'is_active': session.is_active
                    })
                
                return session_list
                
        except Exception as e:
            logger.error(f"Error listing user sessions: {str(e)}")
            return []


# Global instance
chat_rag_agent = ChatRAGAgent()