"""
Qdrant Vector Database Service.

This service provides a high-level interface for interacting with Qdrant,
including collection management, vector operations, and similarity search.
"""

import logging
from typing import List, Dict, Optional, Any
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
)
from qdrant_client.http.exceptions import UnexpectedResponse

from ..config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for managing Qdrant vector database operations."""
    
    def __init__(self):
        """Initialize Qdrant client."""
        self.client = QdrantClient(**settings.qdrant_config)
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize Qdrant collections if they don't exist.
        
        Creates three collections:
        - document_embeddings: Full document vectors
        - chunk_embeddings: Document chunk vectors
        - query_embeddings: Search query history
        """
        if self._initialized:
            return
        
        try:
            # Check Qdrant connection
            collections = self.client.get_collections()
            logger.info(f"Connected to Qdrant. Existing collections: {len(collections.collections)}")
            
            # Create collections if they don't exist
            await self._ensure_collection(
                settings.qdrant_collection_documents,
                settings.embedding_dimension,
                Distance.COSINE
            )
            await self._ensure_collection(
                settings.qdrant_collection_chunks,
                settings.embedding_dimension,
                Distance.COSINE
            )
            await self._ensure_collection(
                settings.qdrant_collection_queries,
                settings.embedding_dimension,
                Distance.COSINE
            )
            
            self._initialized = True
            logger.info("Qdrant service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant service: {e}")
            raise
    
    async def _ensure_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance
    ) -> None:
        """
        Ensure a collection exists, create if it doesn't.
        
        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            distance: Distance metric (COSINE, EUCLID, DOT)
        """
        try:
            # Check if collection exists
            self.client.get_collection(collection_name)
            logger.info(f"Collection '{collection_name}' already exists")
        except (UnexpectedResponse, Exception):
            # Collection doesn't exist, create it
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            logger.info(f"Created collection '{collection_name}' (size={vector_size}, distance={distance.name})")
    
    async def upsert_vectors(
        self,
        collection_name: str,
        points: List[Dict[str, Any]]
    ) -> None:
        """
        Insert or update vectors in a collection.
        
        Args:
            collection_name: Name of the collection
            points: List of point dictionaries with 'id', 'vector', and 'payload'
        
        Example:
            points = [
                {
                    "id": "doc-123",
                    "vector": [0.1, 0.2, ...],
                    "payload": {"document_id": "123", "title": "Example"}
                }
            ]
        """
        try:
            point_structs = [
                PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point.get("payload", {})
                )
                for point in points
            ]
            
            self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )
            
            logger.info(f"Upserted {len(points)} vectors to '{collection_name}'")
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            raise
    
    async def search_similar(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in a collection.
        
        Args:
            collection_name: Name of the collection to search
            query_vector: Query vector for similarity search
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            filters: Optional filters for metadata
        
        Returns:
            List of search results with id, score, and payload
        """
        try:
            # Build filter if provided
            query_filter = None
            if filters:
                query_filter = self._build_filter(filters)
            
            # Execute search
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # Format results
            formatted_results = [
                {
                    "id": str(result.id),
                    "score": result.score,
                    "payload": result.payload
                }
                for result in results
            ]
            
            logger.info(f"Found {len(formatted_results)} similar vectors in '{collection_name}'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            raise
    
    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """
        Build Qdrant filter from dictionary.
        
        Args:
            filters: Dictionary of field: value pairs
        
        Returns:
            Qdrant Filter object
        """
        conditions = [
            FieldCondition(
                key=key,
                match=MatchValue(value=value)
            )
            for key, value in filters.items()
        ]
        return Filter(must=conditions)
    
    async def delete_vectors(
        self,
        collection_name: str,
        point_ids: List[str]
    ) -> None:
        """
        Delete vectors from a collection.
        
        Args:
            collection_name: Name of the collection
            point_ids: List of point IDs to delete
        """
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=point_ids
            )
            logger.info(f"Deleted {len(point_ids)} vectors from '{collection_name}'")
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            raise
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a collection.
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            Dictionary with collection metadata
        """
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "status": info.status.name,
                "optimizer_status": info.optimizer_status.name,
                "indexed_vectors_count": info.indexed_vectors_count
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise
    
    async def count_vectors(
        self,
        collection_name: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count vectors in a collection with optional filters.
        
        Args:
            collection_name: Name of the collection
            filters: Optional filters for counting
        
        Returns:
            Number of vectors matching criteria
        """
        try:
            query_filter = None
            if filters:
                query_filter = self._build_filter(filters)
            
            result = self.client.count(
                collection_name=collection_name,
                count_filter=query_filter
            )
            return result.count
        except Exception as e:
            logger.error(f"Failed to count vectors: {e}")
            raise
    
    async def close(self) -> None:
        """Close Qdrant client connection."""
        try:
            self.client.close()
            logger.info("Qdrant client closed")
        except Exception as e:
            logger.error(f"Failed to close Qdrant client: {e}")


# Global Qdrant service instance (singleton)
_qdrant_service: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    """
    Get or create the global Qdrant service instance.
    
    Returns:
        QdrantService instance
    """
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
    return _qdrant_service
