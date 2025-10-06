"""
RAG API Routes.

FastAPI endpoints for Retrieval-Augmented Generation:
- POST /rag/retrieve - Retrieve context for query
- POST /rag/query - Full RAG query (retrieve + generate)
- GET /rag/health - Service health check
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import logging

from src.services.rag_service import get_rag_service, RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


# ==================== Request/Response Schemas ====================

class RetrieveRequest(BaseModel):
    """Request to retrieve context for a query."""
    query: str = Field(..., description="User query", min_length=1)
    top_k: int = Field(
        default=5,
        description="Number of chunks to retrieve",
        ge=1,
        le=20
    )
    use_reranking: bool = Field(
        default=True,
        description="Apply cross-encoder re-ranking"
    )
    collection_name: str = Field(
        default="chunk_embeddings",
        description="Qdrant collection to search"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional Qdrant filters"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is machine learning?",
                "top_k": 5,
                "use_reranking": True,
                "collection_name": "chunk_embeddings"
            }
        }


class ChunkResult(BaseModel):
    """A retrieved chunk with metadata."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    chunk_index: int
    metadata: Dict[str, Any] = {}


class CitationResponse(BaseModel):
    """Citation information."""
    document_id: str
    document_title: str
    chunk_id: str
    chunk_index: int
    relevance_score: float
    excerpt: str


class RetrieveResponse(BaseModel):
    """Response from context retrieval."""
    query: str
    context_text: str
    chunks: List[ChunkResult]
    citations: List[CitationResponse]
    total_tokens: int
    strategy: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is machine learning?",
                "context_text": "Machine learning is a subset of AI...",
                "chunks": [
                    {
                        "chunk_id": "chunk-123",
                        "document_id": "doc-456",
                        "content": "Machine learning enables...",
                        "score": 0.95,
                        "chunk_index": 0,
                        "metadata": {}
                    }
                ],
                "citations": [
                    {
                        "document_id": "doc-456",
                        "document_title": "AI Basics",
                        "chunk_id": "chunk-123",
                        "chunk_index": 0,
                        "relevance_score": 0.95,
                        "excerpt": "Machine learning enables..."
                    }
                ],
                "total_tokens": 342,
                "strategy": "hybrid_rerank"
            }
        }


class RAGQueryRequest(BaseModel):
    """Request for full RAG query (retrieve + generate)."""
    query: str = Field(..., description="User question", min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    use_reranking: bool = Field(default=True)
    collection_name: str = Field(default="chunk_embeddings")
    model: str = Field(
        default="claude-sonnet-4",
        description="LLM model to use"
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=500, ge=50, le=4000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the benefits of machine learning?",
                "top_k": 5,
                "use_reranking": True,
                "model": "claude-sonnet-4",
                "temperature": 0.7,
                "max_tokens": 500
            }
        }


class RAGQueryResponse(BaseModel):
    """Response from full RAG query."""
    query: str
    answer: str
    citations: List[CitationResponse]
    context_used: str
    model: str
    tokens_used: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the benefits of machine learning?",
                "answer": "Machine learning offers several key benefits...",
                "citations": [
                    {
                        "document_id": "doc-456",
                        "document_title": "AI Basics",
                        "chunk_id": "chunk-123",
                        "chunk_index": 0,
                        "relevance_score": 0.95,
                        "excerpt": "Machine learning enables..."
                    }
                ],
                "context_used": "Machine learning is...",
                "model": "claude-sonnet-4",
                "tokens_used": 450
            }
        }


# ==================== API Endpoints ====================

@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_context(
    request: RetrieveRequest,
    rag: RAGService = Depends(get_rag_service)
) -> RetrieveResponse:
    """
    Retrieve relevant context for a query using hybrid search.
    
    **Process:**
    1. Vector similarity search
    2. Keyword matching (BM25-like)
    3. Hybrid score combination
    4. Optional cross-encoder re-ranking
    5. Context assembly with deduplication
    
    **Returns:**
    - Assembled context text
    - Individual chunks with scores
    - Citations for source attribution
    - Token count for context
    """
    try:
        logger.info(f"Retrieving context for query: {request.query[:100]}")
        
        # Retrieve context
        context = await rag.retrieve(
            query=request.query,
            collection_name=request.collection_name,
            top_k=request.top_k,
            use_reranking=request.use_reranking,
            filters=request.filters
        )
        
        # Build response
        response = RetrieveResponse(
            query=context.query,
            context_text=context.context_text,
            chunks=[
                ChunkResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    score=chunk.score,
                    chunk_index=chunk.chunk_index,
                    metadata=chunk.metadata
                )
                for chunk in context.chunks
            ],
            citations=[
                CitationResponse(
                    document_id=cit.document_id,
                    document_title=cit.document_title,
                    chunk_id=cit.chunk_id,
                    chunk_index=cit.chunk_index,
                    relevance_score=cit.relevance_score,
                    excerpt=cit.excerpt
                )
                for cit in context.citations
            ],
            total_tokens=context.total_tokens,
            strategy=context.strategy
        )
        
        logger.info(
            f"Retrieved {len(response.chunks)} chunks, "
            f"{response.total_tokens} tokens"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to retrieve context: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve context: {str(e)}"
        )


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    rag: RAGService = Depends(get_rag_service)
) -> RAGQueryResponse:
    """
    Full RAG query: retrieve context and generate answer.
    
    **Process:**
    1. Retrieve relevant context (hybrid search + re-ranking)
    2. Assemble context with citations
    3. Generate answer using LLM
    4. Extract used citations
    """
    try:
        logger.info(f"RAG query: {request.query[:100]}")
        
        # Retrieve context
        context = await rag.retrieve(
            query=request.query,
            collection_name=request.collection_name,
            top_k=request.top_k,
            use_reranking=request.use_reranking
        )
        
        # Generate answer using LLM
        from src.services.llm_service import get_llm_service
        import os
        
        llm = get_llm_service(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        try:
            llm_response = await llm.generate(
                query=request.query,
                context=context,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            answer = llm_response.answer
            tokens_used = llm_response.tokens_used
        except ValueError as ve:
            # No API keys configured - return context only
            logger.warning(f"LLM generation failed (no API keys?): {ve}")
            answer = (
                f"[Context Retrieved - LLM Not Configured]\n\n"
                f"Retrieved {len(context.chunks)} relevant chunks:\n\n"
                f"{context.context_text[:500]}..."
            )
            tokens_used = context.total_tokens
        
        # Extract citations that were used
        used_citations = rag.extract_citations(context, answer)
        
        response = RAGQueryResponse(
            query=request.query,
            answer=answer,
            citations=[
                CitationResponse(
                    document_id=cit.document_id,
                    document_title=cit.document_title,
                    chunk_id=cit.chunk_id,
                    chunk_index=cit.chunk_index,
                    relevance_score=cit.relevance_score,
                    excerpt=cit.excerpt
                )
                for cit in used_citations
            ],
            context_used=context.context_text[:500] + "...",
            model=request.model,
            tokens_used=tokens_used
        )
        
        logger.info(f"Generated answer with {len(response.citations)} citations")
        
        return response
        
    except Exception as e:
        logger.error(f"Failed RAG query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed RAG query: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for RAG service."""
    return {
        "status": "healthy",
        "service": "rag",
        "features": [
            "hybrid_search",
            "reranking",
            "context_assembly",
            "citation_extraction",
            "llm_generation",
            "streaming"
        ]
    }


@router.post("/query/stream")
async def rag_query_stream(
    request: RAGQueryRequest,
    rag: RAGService = Depends(get_rag_service)
):
    """
    Full RAG query with streaming response (SSE).
    
    **Process:**
    1. Retrieve relevant context (hybrid search + re-ranking)
    2. Assemble context with citations
    3. Stream answer from LLM in real-time
    
    **Returns:** Server-Sent Events (SSE) stream
    - data: answer_chunk - Pieces of the answer as they're generated
    - data: citations - Final citations after answer completes
    - data: done - Signal that streaming is complete
    """
    from fastapi.responses import StreamingResponse
    from src.services.llm_service import get_llm_service
    import os
    import json
    
    async def generate():
        try:
            logger.info(f"RAG query (streaming): {request.query[:100]}")
            
            # Retrieve context
            context = await rag.retrieve(
                query=request.query,
                collection_name=request.collection_name,
                top_k=request.top_k,
                use_reranking=request.use_reranking
            )
            
            # Initialize LLM
            llm = get_llm_service(
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
            
            # Stream answer
            full_answer = ""
            try:
                async for chunk in llm.generate_stream(
                    query=request.query,
                    context=context,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                ):
                    full_answer += chunk
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Send citations
                used_citations = rag.extract_citations(context, full_answer)
                citations_data = [
                    {
                        "document_id": cit.document_id,
                        "document_title": cit.document_title,
                        "chunk_id": cit.chunk_id,
                        "chunk_index": cit.chunk_index,
                        "relevance_score": cit.relevance_score,
                        "excerpt": cit.excerpt
                    }
                    for cit in used_citations
                ]
                yield f"data: {json.dumps({'citations': citations_data})}\n\n"
                
            except ValueError as ve:
                # No API keys - send context only
                logger.warning(f"LLM streaming failed: {ve}")
                fallback_msg = (
                    f"[Context Retrieved - LLM Not Configured]\n\n"
                    f"Retrieved {len(context.chunks)} relevant chunks."
                )
                yield f"data: {json.dumps({'chunk': fallback_msg})}\n\n"
            
            # Send done signal
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

