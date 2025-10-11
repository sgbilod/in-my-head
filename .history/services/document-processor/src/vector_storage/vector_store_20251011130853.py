"""
Vector store for managing embeddings in Qdrant.

Features:
- Store and retrieve embeddings
- Batch operations
- Search capabilities
- Collection management
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from .collection_manager import CollectionManager, CollectionConfig
from .search_engine import (
    SearchEngine,
    SearchQuery,
    SearchFilter,
    SearchResult,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """Document with vector embedding."""

    vector: List[float]
    payload: Dict[str, Any]
    id: Optional[str] = None

    def __post_init__(self):
        """Generate ID if not provided."""
        if self.id is None:
            self.id = str(uuid.uuid4())


class VectorStore:
    """
    Vector store for Qdrant database.

    Features:
    - Store embeddings with metadata
    - Batch upload operations
    - Semantic search
    - Hybrid search (vector + keyword)
    - Collection management
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
        default_collection: str = "documents",
        vector_size: int = 1536,
    ):
        """
        Initialize vector store.

        Args:
            host: Qdrant server host
            port: Qdrant server port
            api_key: Optional API key for authentication
            default_collection: Default collection name
            vector_size: Vector dimension
        """
        # Initialize Qdrant client
        self.client = QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
            timeout=30,
        )

        self.default_collection = default_collection
        self.vector_size = vector_size

        # Initialize managers
        self.collection_manager = CollectionManager(
            client=self.client,
            default_vector_size=vector_size,
        )

        self.search_engine = SearchEngine(
            client=self.client,
            default_collection=default_collection,
        )

        # Statistics
        self.stats = {
            "total_uploaded": 0,
            "total_searched": 0,
            "failed_uploads": 0,
        }

        logger.info(
            f"Initialized VectorStore at {host}:{port} "
            f"(collection={default_collection}, size={vector_size})"
        )

    def setup(self, recreate: bool = False) -> bool:
        """
        Setup default collections.

        Args:
            recreate: If True, recreate existing collections

        Returns:
            True if setup successful
        """
        try:
            # Create default collection
            config = CollectionConfig(
                name=self.default_collection,
                vector_size=self.vector_size,
                distance="Cosine",
            )

            result = self.collection_manager.create_collection(
                config, recreate=recreate
            )

            if result:
                logger.info("Vector store setup complete")
            else:
                logger.warning("Vector store setup had issues")

            return result

        except Exception as e:
            logger.error(f"Vector store setup failed: {e}")
            return False

    def insert(
        self,
        document: VectorDocument,
        collection_name: Optional[str] = None,
    ) -> bool:
        """
        Insert a single document.

        Args:
            document: Vector document to insert
            collection_name: Collection name (default: self.default_collection)

        Returns:
            True if inserted successfully
        """
        return self.insert_batch([document], collection_name)

    def insert_batch(
        self,
        documents: List[VectorDocument],
        collection_name: Optional[str] = None,
        batch_size: int = 100,
    ) -> bool:
        """
        Insert multiple documents in batches.

        Args:
            documents: List of vector documents
            collection_name: Collection name
            batch_size: Batch size for upload

        Returns:
            True if all inserted successfully
        """
        collection = collection_name or self.default_collection

        if not documents:
            logger.warning("No documents to insert")
            return True

        try:
            # Process in batches
            total_batches = (len(documents) + batch_size - 1) // batch_size

            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min((batch_idx + 1) * batch_size, len(documents))
                batch = documents[start_idx:end_idx]

                # Convert to PointStruct
                points = [
                    PointStruct(
                        id=doc.id,
                        vector=doc.vector,
                        payload=doc.payload,
                    )
                    for doc in batch
                ]

                # Upload batch
                self.client.upsert(
                    collection_name=collection,
                    points=points,
                )

                logger.debug(
                    f"Uploaded batch {batch_idx + 1}/{total_batches} "
                    f"({len(batch)} documents)"
                )

            # Update statistics
            self.stats["total_uploaded"] += len(documents)

            logger.info(
                f"Successfully inserted {len(documents)} documents "
                f"into {collection}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to insert batch: {e}")
            self.stats["failed_uploads"] += 1
            return False

    def search(
        self,
        query: SearchQuery,
        collection_name: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Execute search query.

        Args:
            query: Search query configuration
            collection_name: Collection name

        Returns:
            List of search results
        """
        self.stats["total_searched"] += 1
        return self.search_engine.search(query, collection_name)

    def semantic_search(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        collection_name: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Perform semantic search.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            collection_name: Collection name

        Returns:
            List of search results
        """
        return self.search_engine.semantic_search(
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            collection_name=collection_name,
        )

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
            filters: Search filters
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            collection_name: Collection name

        Returns:
            List of search results
        """
        return self.search_engine.hybrid_search(
            query_vector=query_vector,
            filters=filters,
            limit=limit,
            score_threshold=score_threshold,
            collection_name=collection_name,
        )

    def get_by_id(
        self,
        document_id: str,
        collection_name: Optional[str] = None,
    ) -> Optional[SearchResult]:
        """
        Retrieve document by ID.

        Args:
            document_id: Document ID
            collection_name: Collection name

        Returns:
            SearchResult or None
        """
        return self.search_engine.search_by_id(document_id, collection_name)

    def delete(
        self,
        document_id: str,
        collection_name: Optional[str] = None,
    ) -> bool:
        """
        Delete document by ID.

        Args:
            document_id: Document ID
            collection_name: Collection name

        Returns:
            True if deleted successfully
        """
        collection = collection_name or self.default_collection

        try:
            self.client.delete(
                collection_name=collection,
                points_selector=[document_id],
            )

            logger.info(f"Deleted document {document_id} from {collection}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False

    def delete_batch(
        self,
        document_ids: List[str],
        collection_name: Optional[str] = None,
    ) -> bool:
        """
        Delete multiple documents.

        Args:
            document_ids: List of document IDs
            collection_name: Collection name

        Returns:
            True if all deleted successfully
        """
        collection = collection_name or self.default_collection

        try:
            self.client.delete(
                collection_name=collection,
                points_selector=document_ids,
            )

            logger.info(
                f"Deleted {len(document_ids)} documents from {collection}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to delete batch: {e}")
            return False

    def count(
        self,
        filters: Optional[List[SearchFilter]] = None,
        collection_name: Optional[str] = None,
    ) -> int:
        """
        Count documents matching filters.

        Args:
            filters: Optional search filters
            collection_name: Collection name

        Returns:
            Number of matching documents
        """
        return self.search_engine.count_points(filters, collection_name)

    def get_collection_info(
        self,
        collection_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get collection information.

        Args:
            collection_name: Collection name

        Returns:
            Collection info dictionary
        """
        collection = collection_name or self.default_collection
        return self.collection_manager.get_collection_info(collection)

    def list_collections(self) -> List[str]:
        """
        List all collections.

        Returns:
            List of collection names
        """
        return self.collection_manager.list_collections()

    def create_collection(
        self,
        name: str,
        vector_size: Optional[int] = None,
        distance: str = "Cosine",
        recreate: bool = False,
    ) -> bool:
        """
        Create a new collection.

        Args:
            name: Collection name
            vector_size: Vector dimension (default: self.vector_size)
            distance: Distance metric (Cosine, Euclid, Dot)
            recreate: Recreate if exists

        Returns:
            True if created successfully
        """
        config = CollectionConfig(
            name=name,
            vector_size=vector_size or self.vector_size,
            distance=distance,
        )

        return self.collection_manager.create_collection(config, recreate)

    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection.

        Args:
            name: Collection name

        Returns:
            True if deleted successfully
        """
        return self.collection_manager.delete_collection(name)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.

        Returns:
            Statistics dictionary
        """
        collection_stats = self.collection_manager.get_statistics()

        return {
            **self.stats,
            "collections": collection_stats,
        }

    def close(self):
        """Close connections."""
        try:
            self.client.close()
            logger.info("Vector store connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
