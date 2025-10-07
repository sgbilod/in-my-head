"""
API endpoint for conversation management with Redis caching.

Features:
- Create, list, update, delete conversations
- Send messages with streaming SSE support
- Integrated with CachedRAGService for optimal performance
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import logging
import json
import asyncio
from datetime import datetime
from uuid import uuid4

from src.services.cached_rag_service import get_cached_rag_service
from src.models.conversation import (
    Conversation,
    Message,
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversations", tags=["conversations"])

# In-memory storage for demo (replace with database in production)
conversations_db: Dict[str, Conversation] = {}


@router.post("/", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(data: ConversationCreate) -> Conversation:
    """
    Create a new conversation.
    
    Args:
        data: Conversation creation data
    
    Returns:
        Created conversation
    """
    conversation_id = str(uuid4())
    conversation = Conversation(
        id=conversation_id,
        title=data.title or "New Conversation",
        collection_id=data.collection_id,
        messages=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    conversations_db[conversation_id] = conversation
    logger.info(f"Created conversation: {conversation_id}")
    
    return conversation


@router.get("/", response_model=List[Conversation])
async def list_conversations(
    collection_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Conversation]:
    """
    List all conversations.
    
    Args:
        collection_id: Filter by collection
        limit: Max results
        offset: Skip results
    
    Returns:
        List of conversations
    """
    conversations = list(conversations_db.values())
    
    # Filter by collection if specified
    if collection_id:
        conversations = [c for c in conversations if c.collection_id == collection_id]
    
    # Sort by updated_at descending
    conversations.sort(key=lambda c: c.updated_at, reverse=True)
    
    # Apply pagination
    return conversations[offset:offset + limit]


@router.get("/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str) -> Conversation:
    """
    Get conversation by ID.
    
    Args:
        conversation_id: Conversation ID
    
    Returns:
        Conversation details
    """
    if conversation_id not in conversations_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )
    
    return conversations_db[conversation_id]


@router.patch("/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: str,
    data: ConversationUpdate
) -> Conversation:
    """
    Update conversation (rename, etc).
    
    Args:
        conversation_id: Conversation ID
        data: Update data
    
    Returns:
        Updated conversation
    """
    if conversation_id not in conversations_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )
    
    conversation = conversations_db[conversation_id]
    
    if data.title is not None:
        conversation.title = data.title
    
    conversation.updated_at = datetime.utcnow()
    
    logger.info(f"Updated conversation: {conversation_id}")
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str):
    """
    Delete conversation.
    
    Args:
        conversation_id: Conversation ID
    """
    if conversation_id not in conversations_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )
    
    del conversations_db[conversation_id]
    logger.info(f"Deleted conversation: {conversation_id}")


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    data: MessageCreate,
    stream: bool = True
):
    """
    Send a message and get AI response.
    
    Supports streaming via SSE for real-time response.
    
    Args:
        conversation_id: Conversation ID
        data: Message content
        stream: Enable streaming response
    
    Returns:
        StreamingResponse with SSE events or JSON response
    """
    if conversation_id not in conversations_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )
    
    conversation = conversations_db[conversation_id]
    
    # Add user message
    user_message = Message(
        id=str(uuid4()),
        role="user",
        content=data.content,
        timestamp=datetime.utcnow(),
    )
    conversation.messages.append(user_message)
    
    # Get cached RAG service
    rag_service = get_cached_rag_service()
    
    if stream:
        # Streaming response
        async def generate_stream():
            try:
                # Retrieve context
                context = await rag_service.retrieve_context_async(
                    query=data.content,
                    collection_id=conversation.collection_id,
                    limit=10,
                    use_reranking=True
                )
                
                # Create assistant message
                assistant_message_id = str(uuid4())
                assistant_message = Message(
                    id=assistant_message_id,
                    role="assistant",
                    content="",
                    timestamp=datetime.utcnow(),
                    citations=context.citations,
                )
                
                # Stream response (placeholder - integrate with LLM streaming)
                response_text = f"Based on {len(context.chunks)} documents, here's the answer:\n\n"
                response_text += context.context_text[:500] + "..."
                
                # Simulate streaming
                for char in response_text:
                    assistant_message.content += char
                    yield f"data: {json.dumps({'content': char, 'done': False})}\n\n"
                    await asyncio.sleep(0.01)  # Simulate typing speed
                
                # Add to conversation
                conversation.messages.append(assistant_message)
                conversation.updated_at = datetime.utcnow()
                
                # Send done event
                yield f"data: {json.dumps({'content': '', 'done': True, 'message_id': assistant_message_id})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    
    else:
        # Non-streaming response
        context = await rag_service.retrieve_context_async(
            query=data.content,
            collection_id=conversation.collection_id,
            limit=10,
            use_reranking=True
        )
        
        assistant_message = Message(
            id=str(uuid4()),
            role="assistant",
            content=f"Based on {len(context.chunks)} documents: {context.context_text[:500]}...",
            timestamp=datetime.utcnow(),
            citations=context.citations,
        )
        
        conversation.messages.append(assistant_message)
        conversation.updated_at = datetime.utcnow()
        
        return {"message": assistant_message}


@router.get("/{conversation_id}/messages", response_model=List[Message])
async def get_messages(conversation_id: str) -> List[Message]:
    """
    Get all messages in a conversation.
    
    Args:
        conversation_id: Conversation ID
    
    Returns:
        List of messages
    """
    if conversation_id not in conversations_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )
    
    return conversations_db[conversation_id].messages


@router.get("/{conversation_id}/cache-stats")
async def get_conversation_cache_stats(conversation_id: str) -> Dict[str, Any]:
    """
    Get caching statistics for debugging.
    
    Args:
        conversation_id: Conversation ID
    
    Returns:
        Cache statistics
    """
    rag_service = get_cached_rag_service()
    stats = await rag_service.get_cache_stats()
    
    return {
        "conversation_id": conversation_id,
        "cache_stats": stats,
    }
