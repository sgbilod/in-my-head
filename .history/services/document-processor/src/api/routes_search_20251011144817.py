"""
Search API router.

Provides endpoints for:
- Semantic search
- Hybrid search (vector + keyword)
- Metadata filtering
"""

from typing import Optional, List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from ..vector_storage import VectorStore
from ..api.auth import get_api_key
from ..api.rate_limiter import rate_limit
from ..api.schemas import SearchRequest, SearchResponse, SearchResult

# Create router
router = APIRouter(prefix="/api/v1", tags=["search"])

# Initialize vector store
vector_store = VectorStore()


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search documents",
    description="Search documents using semantic and keyword search",
)
@rate_limit(cost=2)
async def search_documents(
    request: SearchRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Search documents using hybrid search.

    Combines:
    - Semantic search (vector similarity)
    - Keyword search (BM25)
    - Metadata filtering

    Args:
        request: Search request with query and filters

    Returns:
        Search results with scores and metadata

    Example:
        ```python
        import requests

        headers = {"X-API-Key": "your-api-key"}
        data = {
            "query": "machine learning",
            "topics": ["AI", "technology"],
            "limit": 10
        }

        response = requests.post(
            "http://localhost:8000/api/v1/search",
            json=data,
            headers=headers,
        )

        results = response.json()["results"]
        for result in results:
            print(f"Score: {result['score']}")
            print(f"Text: {result['text'][:100]}...")
        ```
    """
    try:
        # Build metadata filter
        metadata_filter = {}

        if request.authors:
            metadata_filter["authors"] = {"$in": request.authors}

        if request.topics:
            metadata_filter["topics"] = {"$in": request.topics}

        if request.categories:
            metadata_filter["categories"] = {"$in": request.categories}

        if request.entities:
            metadata_filter["entities"] = {"$in": request.entities}

        if request.sentiment:
            metadata_filter["sentiment"] = request.sentiment

        if request.language:
            metadata_filter["language"] = request.language

        # Perform search
        if request.query:
            # Hybrid search with query
            search_results = vector_store.hybrid_search(
                query=request.query,
                limit=request.limit,
                metadata_filter=metadata_filter if metadata_filter else None,
            )
        else:
            # Metadata-only search
            search_results = vector_store.search_by_metadata(
                metadata_filter=metadata_filter,
                limit=request.limit,
            )

        # Convert to response format
        results = []
        for result in search_results:
            results.append(SearchResult(
                doc_id=result.id,
                score=result.score,
                text=result.payload.get("text", "")[:500],  # Limit text length
                metadata=result.payload,
            ))

        # Build filters dict for response
        filters = {}
        if request.authors:
            filters["authors"] = request.authors
        if request.topics:
            filters["topics"] = request.topics
        if request.categories:
            filters["categories"] = request.categories
        if request.entities:
            filters["entities"] = request.entities
        if request.sentiment:
            filters["sentiment"] = request.sentiment
        if request.language:
            filters["language"] = request.language
        filters["limit"] = request.limit

        return SearchResponse(
            results=results,
            total=len(results),
            query=request.query,
            filters=filters,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get(
    "/search/suggest",
    response_model=List[str],
    summary="Get search suggestions",
    description="Get search suggestions based on query prefix",
)
@rate_limit(cost=1)
async def get_suggestions(
    query: str,
    limit: int = 5,
    api_key: str = Depends(get_api_key),
):
    """
    Get search suggestions based on query prefix.

    Returns:
        List of suggested queries

    Example:
        ```python
        import requests

        headers = {"X-API-Key": "your-api-key"}
        params = {"query": "machine", "limit": 5}

        response = requests.get(
            "http://localhost:8000/api/v1/search/suggest",
            params=params,
            headers=headers,
        )

        suggestions = response.json()
        # ["machine learning", "machine vision", ...]
        ```
    """
    # TODO: Implement suggestion logic
    # For now, return empty list
    return []
