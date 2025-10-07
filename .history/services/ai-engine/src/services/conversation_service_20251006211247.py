"""
Conversation management service.

Handles:
- Creating and managing conversations
- Adding messages to conversations
- Integrating RAG for context retrieval
- Tracking citations in conversations
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
import asyncpg
import json

from src.services.rag_service import get_rag_service
from src.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Service for conversation management with RAG integration.
    
    Features:
    - Multi-turn conversations
    - RAG context retrieval per message
    - Citation tracking
    - Conversation history
    """
    
    def __init__(self, db_url: str):
        """
        Initialize conversation service.
        
        Args:
            db_url: PostgreSQL connection URL
        """
        self.db_url = db_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Create database connection pool."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=2,
                max_size=10
            )
            logger.info("✅ Conversation service pool created")
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Conversation service pool closed")
    
    async def create_conversation(
        self,
        user_id: UUID,
        title: str
    ) -> Dict[str, Any]:
        """
        Create a new conversation.
        
        Args:
            user_id: User ID
            title: Conversation title
            
        Returns:
            Conversation record
        """
        conversation_id = uuid4()
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow("""
                INSERT INTO conversations (id, user_id, title)
                VALUES ($1, $2, $3)
                RETURNING id, user_id, title, created_at, updated_at
            """, conversation_id, user_id, title)
            
            conversation = dict(record)
            logger.info(f"Created conversation: {conversation['id']}")
            
            return conversation
    
    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for access control)
            
        Returns:
            Conversation record or None
        """
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow("""
                SELECT id, user_id, title, created_at, updated_at
                FROM conversations
                WHERE id = $1 AND user_id = $2
            """, conversation_id, user_id)
            
            if record:
                return dict(record)
            return None
    
    async def list_conversations(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List user's conversations.
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations
            offset: Pagination offset
            
        Returns:
            List of conversation records
        """
        async with self.pool.acquire() as conn:
            records = await conn.fetch("""
                SELECT 
                    c.id, c.user_id, c.title,
                    c.created_at, c.updated_at,
                    COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON m.conversation_id = c.id
                WHERE c.user_id = $1
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT $2 OFFSET $3
            """, user_id, limit, offset)
            
            return [dict(r) for r in records]
    
    async def delete_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete conversation and all messages.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for access control)
            
        Returns:
            True if deleted, False if not found
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM conversations
                WHERE id = $1 AND user_id = $2
            """, conversation_id, user_id)
            
            deleted = result.endswith("1")
            
            if deleted:
                logger.info(f"Deleted conversation: {conversation_id}")
            
            return deleted
    
    async def add_user_message(
        self,
        conversation_id: UUID,
        content: str
    ) -> Dict[str, Any]:
        """
        Add user message to conversation.
        
        Args:
            conversation_id: Conversation ID
            content: Message content
            
        Returns:
            Message record
        """
        message_id = uuid4()
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow("""
                INSERT INTO messages (
                    id, conversation_id, role, content
                ) VALUES ($1, $2, $3, $4)
                RETURNING 
                    id, conversation_id, role, content,
                    rag_context, citations, model,
                    tokens_used, created_at
            """, message_id, conversation_id, 'user', content)
            
            message = dict(record)
            logger.info(
                f"Added user message to {conversation_id}: "
                f"{len(content)} chars"
            )
            
            return message
    
    async def add_assistant_message(
        self,
        conversation_id: UUID,
        content: str,
        query: str,
        model: str = "claude-sonnet-4",
        temperature: float = 0.7,
        use_rag: bool = True,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Add assistant message with RAG.
        
        Args:
            conversation_id: Conversation ID
            content: User's query (for RAG retrieval)
            query: User's query text
            model: LLM model to use
            temperature: LLM temperature
            use_rag: Whether to use RAG retrieval
            top_k: Number of chunks to retrieve
            
        Returns:
            Assistant message record with RAG context
        """
        rag_context_json = None
        citations_json = None
        tokens_used = 0
        answer = content
        
        if use_rag:
            # Retrieve context
            rag_service = get_rag_service()
            context = await rag_service.retrieve(
                query=query,
                top_k=top_k,
                use_reranking=True
            )
            
            # Generate answer
            llm_service = get_llm_service()
            try:
                llm_response = await llm_service.generate(
                    query=query,
                    context=context,
                    model=model,
                    temperature=temperature
                )
                
                answer = llm_response.answer
                tokens_used = llm_response.tokens_used
                
                # Extract citations
                used_citations = rag_service.extract_citations(
                    context, answer
                )
                
                # Build JSON for storage
                rag_context_json = {
                    'chunks': [
                        {
                            'chunk_id': str(c.chunk_id),
                            'document_id': str(c.document_id),
                            'content': c.content,
                            'score': c.score
                        }
                        for c in context.chunks
                    ]
                }
                
                citations_json = {
                    'citations': [
                        {
                            'document_id': str(cit.document_id),
                            'document_title': cit.document_title,
                            'chunk_id': str(cit.chunk_id),
                            'relevance_score': cit.relevance_score,
                            'excerpt': cit.excerpt
                        }
                        for cit in used_citations
                    ]
                }
                
            except ValueError as ve:
                # LLM not configured - use context only
                logger.warning(f"LLM not available: {ve}")
                answer = f"[Context Retrieved]\n\n{context.context_text}"
                tokens_used = context.total_tokens
        
        # Store assistant message
        message_id = uuid4()
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow("""
                INSERT INTO messages (
                    id, conversation_id, role, content,
                    rag_context, citations,
                    model, tokens_used
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING 
                    id, conversation_id, role, content,
                    rag_context, citations, model,
                    tokens_used, created_at
            """,
                message_id,
                conversation_id,
                'assistant',
                answer,
                rag_context_json,  # Pass dict directly, asyncpg handles JSONB
                citations_json,     # Pass dict directly, asyncpg handles JSONB
                model,
                tokens_used
            )
            
            message = dict(record)
            logger.info(
                f"Added assistant message to {conversation_id}: "
                f"{len(answer)} chars, {tokens_used} tokens"
            )
            
            return message
    
    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get messages in conversation.
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages
            offset: Pagination offset
            
        Returns:
            List of message records
        """
        async with self.pool.acquire() as conn:
            records = await conn.fetch("""
                SELECT 
                    id, conversation_id, role, content,
                    rag_context, citations, model,
                    tokens_used, created_at
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
                LIMIT $2 OFFSET $3
            """, conversation_id, limit, offset)
            
            return [dict(r) for r in records]


# Singleton instance
_conversation_service: Optional[ConversationService] = None


def get_conversation_service(db_url: Optional[str] = None) -> ConversationService:
    """Get singleton conversation service."""
    global _conversation_service
    
    if _conversation_service is None:
        if db_url is None:
            db_url = (
                "postgresql://inmyhead:inmyhead_dev_pass@"
                "localhost:5434/inmyhead_dev"
            )
        _conversation_service = ConversationService(db_url)
    
    return _conversation_service
