"""
Chunking API Routes.

FastAPI endpoints for document chunking operations:
- POST /chunks/document/{document_id} - Chunk a document
- GET /chunks/document/{document_id} - Get document chunks
- GET /chunks/{chunk_id} - Get specific chunk
- DELETE /chunks/document/{document_id} - Delete all chunks for document
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import logging

from src.services.chunker_service import (
    ChunkerService,
    ChunkingStrategy,
    get_chunker_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chunks", tags=["chunking"])


# ==================== Request/Response Schemas ====================

class ChunkDocumentRequest(BaseModel):
    """Request to chunk a document."""
    document_id: str = Field(..., description="Document UUID")
    content: str = Field(..., description="Document text content")
    strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.SENTENCE,
        description="Chunking strategy to use"
    )
    chunk_size: Optional[int] = Field(
        default=None,
        description="Target chunk size (overrides default)",
        ge=50,
        le=5000
    )
    chunk_overlap: Optional[int] = Field(
        default=None,
        description="Chunk overlap size (overrides default)",
        ge=0,
        le=500
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "content": "This is a sample document. It has multiple sentences. Each sentence adds meaning.",
                "strategy": "sentence",
                "chunk_size": 500,
                "chunk_overlap": 50
            }
        }


class ChunkMetadataResponse(BaseModel):
    """Chunk metadata response."""
    chunk_id: str
    document_id: str
    chunk_index: int
    start_position: int
    end_position: int
    sentence_count: int
    word_count: int
    char_count: int


class ChunkResponse(BaseModel):
    """Single chunk response."""
    content: str
    metadata: ChunkMetadataResponse


class ChunkDocumentResponse(BaseModel):
    """Response from document chunking operation."""
    document_id: str
    strategy: str
    total_chunks: int
    chunks: List[ChunkResponse]
    statistics: dict
    processing_time_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "strategy": "sentence",
                "total_chunks": 5,
                "chunks": [
                    {
                        "content": "This is a sample document. It has multiple sentences.",
                        "metadata": {
                            "chunk_id": "doc_chunk_0",
                            "document_id": "123e4567-e89b-12d3-a456-426614174000",
                            "chunk_index": 0,
                            "start_position": 0,
                            "end_position": 54,
                            "sentence_count": 2,
                            "word_count": 10,
                            "char_count": 54
                        }
                    }
                ],
                "statistics": {
                    "total_chunks": 5,
                    "avg_chunk_size": 120.5,
                    "min_chunk_size": 54,
                    "max_chunk_size": 200,
                    "avg_word_count": 25,
                    "avg_sentence_count": 3
                },
                "processing_time_ms": 125.5
            }
        }


class ChunkStatisticsResponse(BaseModel):
    """Statistics about chunks."""
    total_chunks: int
    avg_chunk_size: float
    min_chunk_size: int
    max_chunk_size: int
    avg_word_count: float
    avg_sentence_count: float
    total_characters: int
    total_words: int
    total_sentences: int


# ==================== API Endpoints ====================

@router.post("/document", response_model=ChunkDocumentResponse)
async def chunk_document(
    request: ChunkDocumentRequest,
    chunker: ChunkerService = Depends(get_chunker_service)
) -> ChunkDocumentResponse:
    """
    Chunk a document using the specified strategy.
    
    **Strategies:**
    - `sentence`: Respects sentence boundaries, combines sentences to target size
    - `paragraph`: Preserves paragraph structure, splits large paragraphs
    - `fixed`: Fixed character count with configurable overlap
    - `semantic`: Groups semantically related sentences (basic implementation)
    
    **Parameters:**
    - `chunk_size`: Target size in characters (default: 500)
    - `chunk_overlap`: Overlap between chunks (default: 50)
    
    **Returns:**
    - List of chunks with metadata and statistics
    """
    import time
    
    start_time = time.time()
    
    try:
        logger.info(
            f"Chunking document {request.document_id} with strategy={request.strategy.value}"
        )
        
        # Validate content
        if not request.content or len(request.content.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Document content cannot be empty"
            )
        
        # Chunk document
        chunks = chunker.chunk_document(
            document_id=request.document_id,
            content=request.content,
            strategy=request.strategy,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        
        # Calculate statistics
        statistics = chunker.get_chunk_statistics(chunks)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Build response
        response = ChunkDocumentResponse(
            document_id=request.document_id,
            strategy=request.strategy.value,
            total_chunks=len(chunks),
            chunks=[
                ChunkResponse(
                    content=chunk.content,
                    metadata=ChunkMetadataResponse(**chunk.metadata.to_dict())
                )
                for chunk in chunks
            ],
            statistics=statistics,
            processing_time_ms=processing_time_ms
        )
        
        logger.info(
            f"Successfully chunked document {request.document_id}: "
            f"{len(chunks)} chunks in {processing_time_ms:.2f}ms"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Invalid chunking parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to chunk document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to chunk document: {str(e)}"
        )


@router.get("/statistics/{document_id}", response_model=ChunkStatisticsResponse)
async def get_chunk_statistics(
    document_id: str,
    strategy: ChunkingStrategy = Query(
        default=ChunkingStrategy.SENTENCE,
        description="Chunking strategy"
    ),
    chunk_size: Optional[int] = Query(
        default=None,
        description="Chunk size",
        ge=50,
        le=5000
    ),
    chunker: ChunkerService = Depends(get_chunker_service)
) -> ChunkStatisticsResponse:
    """
    Calculate chunking statistics without storing chunks.
    
    Useful for previewing how a document will be chunked before
    committing to a strategy.
    """
    # This would need document content from database
    # For now, return a placeholder response
    raise HTTPException(
        status_code=501,
        detail="Statistics endpoint requires database integration"
    )


@router.get("/health")
async def health_check():
    """Health check endpoint for chunking service."""
    return {
        "status": "healthy",
        "service": "chunking",
        "strategies": [s.value for s in ChunkingStrategy]
    }
