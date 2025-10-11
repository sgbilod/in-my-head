"""
Search engine for Qdrant vector database.

Features:
- Semantic search (vector similarity)
- Keyword search (payload filtering)
- Hybrid search (vector + keyword)
- Advanced filtering
- Pagination and scoring
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    ScoredPoint,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchFilter:
    """Filter for search queries."""

    field: str
    value: Any
    operator: str = "match"  # match, range, exists

    def to_qdrant_condition(self) -> FieldCondition:
        """Convert to Qdrant field condition."""
        if self.operator == "match":
            return FieldCondition(
                key=self.field,
                match=MatchValue(value=self.value),
            )
        elif self.operator == "range":
            # Expect value to be dict with 'gte' and/or 'lte'
            return FieldCondition(
                key=self.field,
                range=Range(**self.value),
            )
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")


@dataclass
class SearchQuery:
    """Search query configuration."""

    query_vector: Optional[List[float]] = None
    query_text: Optional[str] = None  # For keyword search
    limit: int = 10
    score_threshold: Optional[float] = None
    filters: List[SearchFilter] = field(default_factory=list)
    offset: int = 0
    with_payload: bool = True
    with_vectors: bool = False


@dataclass
class SearchResult:
    """Search result with score and payload."""

    id: str
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None

    @classmethod
    def from_scored_point(
        cls, point: ScoredPoint, include_vector: bool = False
    ) -> "SearchResult":
        """Create SearchResult from Qdrant ScoredPoint."""
        return cls(
            id=str(point.id),
            score=point.score,
            payload=dict(point.payload) if point.payload else {},
            vector=point.vector if include_vector else None,
        )


class SearchEngine:
    """
    Search engine for semantic and hybrid search.

    Features:
    - Vector similarity search
    - Keyword filtering
    - Hybrid search (combines both)
    - Advanced filtering and pagination
    """

    def __init__(
        self,
        client: QdrantClient,
        default_collection: str = "documents",
    ):
        """
        Initialize search engine.

        Args:
            client: Qdrant client instance
            default_collection: Default collection name
        """
        self.client = client
        self.default_collection = default_collection

        logger.info(
            f"Initialized SearchEngine with collection={default_collection}"
        )

    def search(
        self,
        query: SearchQuery,
        collection_name: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Execute search query.

        Args:
            query: Search query configuration
            collection_name: Collection to search
                (default: self.default_collection)

        Returns:
            List of search results
        """
        collection = collection_name or self.default_collection

        try:
            # Build filter if specified
            query_filter = None
            if query.filters:
                query_filter = Filter(
                    must=[f.to_qdrant_condition() for f in query.filters]
                )

            # Execute search
            if query.query_vector:
                # Vector search
                results = self.client.search(
                    collection_name=collection,
                    query_vector=query.query_vector,
                    limit=query.limit,
                    offset=query.offset,
                    query_filter=query_filter,
                    score_threshold=query.score_threshold,
                    with_payload=query.with_payload,
                    with_vectors=query.with_vectors,
                )
            else:
                # Scroll through results (no vector search)
                results = self._scroll_search(
                    collection=collection,
                    query=query,
                    query_filter=query_filter,
                )

            # Convert to SearchResult
            search_results = [
                SearchResult.from_scored_point(
                    point, include_vector=query.with_vectors
                )
                for point in results
            ]

            logger.debug(
                f"Search returned {len(search_results)} results "
                f"from {collection}"
            )

            return search_results

        except Exception as e:
            logger.error(f"Search failed in {collection}: {e}")
            return []

    def semantic_search(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        collection_name: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Perform semantic search using vector similarity.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            collection_name: Collection to search

        Returns:
            List of search results
        """
        query = SearchQuery(
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
        )

        return self.search(query, collection_name)

    def keyword_search(
        self,
        filters: List[SearchFilter],
        limit: int = 10,
        collection_name: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Perform keyword search using payload filtering.

        Args:
            filters: List of search filters
            limit: Maximum number of results
            collection_name: Collection to search

        Returns:
            List of search results
        """
        query = SearchQuery(
            filters=filters,
            limit=limit,
        )

        return self.search(query, collection_name)

    def hybrid_search(
        self,
        query_vector: List[float],
        filters: List[SearchFilter],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        collection_name: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Perform hybrid search (vector + keyword).

        Args:
            query_vector: Query embedding vector
            filters: List of search filters
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            collection_name: Collection to search

        Returns:
            List of search results
        """
        query = SearchQuery(
            query_vector=query_vector,
            filters=filters,
            limit=limit,
            score_threshold=score_threshold,
        )

        return self.search(query, collection_name)

    def search_by_id(
        self,
        point_id: str,
        collection_name: Optional[str] = None,
    ) -> Optional[SearchResult]:
        """
        Retrieve a point by ID.

        Args:
            point_id: Point ID
            collection_name: Collection to search

        Returns:
            SearchResult or None if not found
        """
        collection = collection_name or self.default_collection

        try:
            points = self.client.retrieve(
                collection_name=collection,
                ids=[point_id],
                with_payload=True,
                with_vectors=False,
            )

            if points:
                point = points[0]
                return SearchResult(
                    id=str(point.id),
                    score=1.0,  # No score for direct retrieval
                    payload=dict(point.payload) if point.payload else {},
                )

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve point {point_id}: {e}")
            return None

    def search_similar(
        self,
        point_id: str,
        limit: int = 10,
        collection_name: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Find similar points to a given point.

        Args:
            point_id: Reference point ID
            limit: Maximum number of results
            collection_name: Collection to search

        Returns:
            List of similar points
        """
        collection = collection_name or self.default_collection

        try:
            # First, get the point's vector
            points = self.client.retrieve(
                collection_name=collection,
                ids=[point_id],
                with_vectors=True,
            )

            if not points:
                logger.warning(f"Point {point_id} not found")
                return []

            query_vector = points[0].vector

            # Search for similar points
            return self.semantic_search(
                query_vector=query_vector,
                limit=limit + 1,  # +1 to exclude the query point
                collection_name=collection,
            )[
                1:
            ]  # Skip first result (the query point itself)

        except Exception as e:
            logger.error(f"Failed to search similar to {point_id}: {e}")
            return []

    def _scroll_search(
        self,
        collection: str,
        query: SearchQuery,
        query_filter: Optional[Filter],
    ) -> List[ScoredPoint]:
        """
        Scroll through points (for non-vector searches).

        Args:
            collection: Collection name
            query: Search query
            query_filter: Qdrant filter

        Returns:
            List of scored points
        """
        try:
            # Use scroll to get points
            scroll_result = self.client.scroll(
                collection_name=collection,
                scroll_filter=query_filter,
                limit=query.limit,
                offset=query.offset,
                with_payload=query.with_payload,
                with_vectors=query.with_vectors,
            )

            points = scroll_result[0]

            # Convert to ScoredPoint (with score=1.0)
            scored_points = []
            for point in points:
                scored_point = ScoredPoint(
                    id=point.id,
                    version=point.version,
                    score=1.0,  # No similarity score for scroll
                    payload=point.payload,
                    vector=point.vector if query.with_vectors else None,
                )
                scored_points.append(scored_point)

            return scored_points

        except Exception as e:
            logger.error(f"Scroll search failed: {e}")
            return []

    def count_points(
        self,
        filters: Optional[List[SearchFilter]] = None,
        collection_name: Optional[str] = None,
    ) -> int:
        """
        Count points matching filters.

        Args:
            filters: Optional filters
            collection_name: Collection to search

        Returns:
            Number of matching points
        """
        collection = collection_name or self.default_collection

        try:
            query_filter = None
            if filters:
                query_filter = Filter(
                    must=[f.to_qdrant_condition() for f in filters]
                )

            result = self.client.count(
                collection_name=collection,
                count_filter=query_filter,
                exact=True,
            )

            return result.count

        except Exception as e:
            logger.error(f"Failed to count points: {e}")
            return 0
