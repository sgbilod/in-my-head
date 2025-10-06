"""
Conversation API routes.

Endpoints:
- POST /conversations - Create conversation
- GET /conversations - List conversations
- GET /conversations/{id} - Get conversation details
- DELETE /conversations/{id} - Delete conversation
- POST /conversations/{id}/messages - Send message (with RAG)
- GET /conversations/{id}/messages - Get message history
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from uuid import UUID
import logging

from src.services.conversation_service import (
    get_conversation_service,
    ConversationService
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ==================== Request/Response Schemas ====================

class CreateConversationRequest(BaseModel):
    """Request to create a conversation."""
    user_id: UUID = Field(..., description="User ID")
    title: str = Field(..., description="Conversation title", min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Machine Learning Q&A"
            }
        }


class ConversationResponse(BaseModel):
    """Conversation record response."""
    id: UUID
    user_id: UUID
    title: str
    created_at: str
    updated_at: str
    message_count: Optional[int] = None


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str = Field(..., description="Message content", min_length=1)
    model: str = Field(
        default="claude-sonnet-4",
        description="LLM model to use"
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    use_rag: bool = Field(
        default=True,
        description="Use RAG for context retrieval"
    )
    top_k: int = Field(default=5, ge=1, le=20)
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "What is machine learning?",
                "model": "claude-sonnet-4",
                "temperature": 0.7,
                "use_rag": True,
                "top_k": 5
            }
        }


class CitationInfo(BaseModel):
    """Citation information in a message."""
    document_id: str
    document_title: str
    chunk_id: str
    relevance_score: float
    excerpt: str


class MessageResponse(BaseModel):
    """Message record response."""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    citations: Optional[List[CitationInfo]] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    created_at: str


# ==================== API Endpoints ====================

@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    conv_service: ConversationService = Depends(get_conversation_service)
) -> ConversationResponse:
    """
    Create a new conversation.
    
    Returns:
        New conversation record
    """
    try:
        # Initialize service
        await conv_service.initialize()
        
        # Create conversation
        conversation = await conv_service.create_conversation(
            user_id=request.user_id,
            title=request.title
        )
        
        return ConversationResponse(
            id=conversation['id'],
            user_id=conversation['user_id'],
            title=conversation['title'],
            created_at=conversation['created_at'].isoformat(),
            updated_at=conversation['updated_at'].isoformat(),
            message_count=0
        )
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    user_id: UUID,
    limit: int = 50,
    offset: int = 0,
    conv_service: ConversationService = Depends(get_conversation_service)
) -> List[ConversationResponse]:
    """
    List user's conversations.
    
    Args:
        user_id: User ID
        limit: Maximum number of conversations
        offset: Pagination offset
    
    Returns:
        List of conversations
    """
    try:
        await conv_service.initialize()
        
        conversations = await conv_service.list_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return [
            ConversationResponse(
                id=conv['id'],
                user_id=conv['user_id'],
                title=conv['title'],
                created_at=conv['created_at'].isoformat(),
                updated_at=conv['updated_at'].isoformat(),
                message_count=conv['message_count']
            )
            for conv in conversations
        ]
        
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list conversations: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    user_id: UUID,
    conv_service: ConversationService = Depends(get_conversation_service)
) -> ConversationResponse:
    """
    Get conversation details.
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID (for access control)
    
    Returns:
        Conversation record
    """
    try:
        await conv_service.initialize()
        
        conversation = await conv_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        
        return ConversationResponse(
            id=conversation['id'],
            user_id=conversation['user_id'],
            title=conversation['title'],
            created_at=conversation['created_at'].isoformat(),
            updated_at=conversation['updated_at'].isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get conversation {conversation_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    user_id: UUID,
    conv_service: ConversationService = Depends(get_conversation_service)
):
    """
    Delete conversation and all messages.
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID (for access control)
    
    Returns:
        Success message
    """
    try:
        await conv_service.initialize()
        
        deleted = await conv_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        
        return {"status": "deleted", "conversation_id": str(conversation_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to delete conversation {conversation_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete conversation: {str(e)}"
        )


@router.post(
    "/{conversation_id}/messages",
    response_model=List[MessageResponse]
)
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    conv_service: ConversationService = Depends(get_conversation_service)
) -> List[MessageResponse]:
    """
    Send a message in conversation and get assistant response.
    
    Creates two messages:
    1. User message with query
    2. Assistant message with RAG-powered response
    
    Args:
        conversation_id: Conversation ID
        request: Message request
    
    Returns:
        Both user and assistant messages
    """
    try:
        await conv_service.initialize()
        
        # Add user message
        user_msg = await conv_service.add_user_message(
            conversation_id=conversation_id,
            content=request.content
        )
        
        # Generate assistant response with RAG
        assistant_msg = await conv_service.add_assistant_message(
            conversation_id=conversation_id,
            content=request.content,
            query=request.content,
            model=request.model,
            temperature=request.temperature,
            use_rag=request.use_rag,
            top_k=request.top_k
        )
        
        # Format responses
        messages = []
        
        # User message
        messages.append(MessageResponse(
            id=user_msg['id'],
            conversation_id=user_msg['conversation_id'],
            role=user_msg['role'],
            content=user_msg['content'],
            created_at=user_msg['created_at'].isoformat()
        ))
        
        # Assistant message with citations
        citations = None
        if assistant_msg['citations']:
            citations_data = assistant_msg['citations'].get('citations', [])
            citations = [
                CitationInfo(
                    document_id=cit['document_id'],
                    document_title=cit['document_title'],
                    chunk_id=cit['chunk_id'],
                    relevance_score=cit['relevance_score'],
                    excerpt=cit['excerpt']
                )
                for cit in citations_data
            ]
        
        messages.append(MessageResponse(
            id=assistant_msg['id'],
            conversation_id=assistant_msg['conversation_id'],
            role=assistant_msg['role'],
            content=assistant_msg['content'],
            citations=citations,
            model=assistant_msg['model'],
            tokens_used=assistant_msg['tokens_used'],
            created_at=assistant_msg['created_at'].isoformat()
        ))
        
        return messages
        
    except Exception as e:
        logger.error(
            f"Failed to send message in {conversation_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: UUID,
    limit: int = 100,
    offset: int = 0,
    conv_service: ConversationService = Depends(get_conversation_service)
) -> List[MessageResponse]:
    """
    Get message history for a conversation.
    
    Args:
        conversation_id: Conversation ID
        limit: Maximum number of messages
        offset: Pagination offset
    
    Returns:
        List of messages
    """
    try:
        await conv_service.initialize()
        
        messages_data = await conv_service.get_messages(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset
        )
        
        messages = []
        for msg in messages_data:
            citations = None
            if msg['citations']:
                citations_data = msg['citations'].get('citations', [])
                citations = [
                    CitationInfo(
                        document_id=cit['document_id'],
                        document_title=cit['document_title'],
                        chunk_id=cit['chunk_id'],
                        relevance_score=cit['relevance_score'],
                        excerpt=cit['excerpt']
                    )
                    for cit in citations_data
                ]
            
            messages.append(MessageResponse(
                id=msg['id'],
                conversation_id=msg['conversation_id'],
                role=msg['role'],
                content=msg['content'],
                citations=citations,
                model=msg['model'],
                tokens_used=msg['tokens_used'],
                created_at=msg['created_at'].isoformat()
            ))
        
        return messages
        
    except Exception as e:
        logger.error(
            f"Failed to get messages for {conversation_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get messages: {str(e)}"
        )
