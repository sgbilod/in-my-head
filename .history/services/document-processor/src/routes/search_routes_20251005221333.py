"""
Search Routes
API endpoints for document search functionality
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from src.database.connection import get_db
from src.services.search_service import SearchService
from src.models.schemas import (
    SearchRequest, 
    SearchResponse, 
    SimilarityRequest,
    SimilarityResponse
)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/semantic", response_model=List[SearchResponse])
async def semantic_search(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Perform semantic search across documents
    
    Args:
        request: Search request with query text
        db: Database session
    
    Returns:
        List of matching documents with similarity scores
    """
    service = SearchService(db)
    results = await service.semantic_search(
        query=request.query,
        limit=request.limit or 10,
        min_similarity=request.min_similarity or 0.5,
        user_id=None  # TODO: Get from auth
    )
    
    return results


@router.post("/similarity", response_model=List[SimilarityResponse])
async def find_similar_documents(
    request: SimilarityRequest,
    db: Session = Depends(get_db)
):
    """
    Find documents similar to a given document
    
    Args:
        request: Request with document ID
        db: Database session
    
    Returns:
        List of similar documents with similarity scores
    """
    service = SearchService(db)
    results = await service.find_similar(
        document_id=request.document_id,
        limit=request.limit or 10,
        min_similarity=request.min_similarity or 0.5,
        user_id=None  # TODO: Get from auth
    )
    
    return results


@router.post("/generate-embeddings")
async def generate_embeddings(
    db: Session = Depends(get_db)
):
    """
    Generate embeddings for all documents missing them
    
    Args:
        db: Database session
    
    Returns:
        Status message
    """
    service = SearchService(db)
    count = await service.generate_missing_embeddings()
    
    return {
        "message": f"Generated embeddings for {count} documents",
        "count": count
    }
