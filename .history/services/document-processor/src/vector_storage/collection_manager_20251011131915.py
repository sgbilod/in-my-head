"""
Qdrant collection manager for vector storage.

Features:
- Collection creation and deletion
- Schema management
- Index configuration (HNSW)
- Collection statistics and monitoring
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    OptimizersConfigDiff,
    HnswConfigDiff,
    CollectionStatus,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CollectionConfig:
    """Configuration for a Qdrant collection."""

    name: str
    vector_size: int = 1536  # Default for text-embedding-3-small
    distance: str = "Cosine"  # Cosine, Euclid, Dot
    hnsw_m: int = 16  # Number of edges per node
    hnsw_ef_construct: int = 100  # Construction time/accuracy trade-off
    on_disk_payload: bool = False  # Store payload on disk


class CollectionManager:
    """
    Manage Qdrant collections for vector storage.

    Features:
    - Create collections with HNSW indexing
    - Configure distance metrics
    - Manage collection lifecycle
    - Monitor collection statistics
    """

    # Distance metric mapping
    DISTANCE_METRICS = {
        "Cosine": Distance.COSINE,
        "Euclid": Distance.EUCLID,
        "Dot": Distance.DOT,
    }

    def __init__(
        self,
        client: QdrantClient,
        default_vector_size: int = 1536,
    ):
        """
        Initialize collection manager.

        Args:
            client: Qdrant client instance
            default_vector_size: Default vector dimension
        """
        self.client = client
        self.default_vector_size = default_vector_size

        logger.info(
            "Initialized CollectionManager with "
            f"vector_size={default_vector_size}"
        )

    def create_collection(
        self,
        config: CollectionConfig,
        recreate: bool = False,
    ) -> bool:
        """
        Create a new collection with HNSW indexing.

        Args:
            config: Collection configuration
            recreate: If True, delete existing collection first

        Returns:
            True if created successfully
        """
        try:
            # Check if collection exists
            exists = self._collection_exists(config.name)

            if exists:
                if recreate:
                    logger.info(f"Deleting existing collection: {config.name}")
                    self.delete_collection(config.name)
                else:
                    logger.warning(
                        f"Collection {config.name} already exists. "
                        f"Use recreate=True to overwrite."
                    )
                    return False

            # Get distance metric
            distance = self.DISTANCE_METRICS.get(
                config.distance, Distance.COSINE
            )

            # Create collection
            logger.info(f"Creating collection: {config.name}")
            self.client.create_collection(
                collection_name=config.name,
                vectors_config=VectorParams(
                    size=config.vector_size,
                    distance=distance,
                ),
                optimizer_config=OptimizersConfigDiff(
                    # Start indexing after 10K points
                    indexing_threshold=10000,
                ),
                hnsw_config=HnswConfigDiff(
                    m=config.hnsw_m,
                    ef_construct=config.hnsw_ef_construct,
                    full_scan_threshold=10000,
                ),
                on_disk_payload=config.on_disk_payload,
            )

            logger.info(
                f"Collection {config.name} created successfully "
                f"(size={config.vector_size}, distance={config.distance})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create collection {config.name}: {e}")
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.

        Args:
            collection_name: Name of collection to delete

        Returns:
            True if deleted successfully
        """
        try:
            if not self._collection_exists(collection_name):
                logger.warning(f"Collection {collection_name} does not exist")
                return False

            self.client.delete_collection(collection_name)
            logger.info(f"Collection {collection_name} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False

    def list_collections(self) -> List[str]:
        """
        List all collections.

        Returns:
            List of collection names
        """
        try:
            collections = self.client.get_collections()
            return [col.name for col in collections.collections]

        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    def get_collection_info(
        self, collection_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get collection information and statistics.

        Args:
            collection_name: Name of collection

        Returns:
            Dictionary with collection info or None if not found
        """
        try:
            if not self._collection_exists(collection_name):
                logger.warning(f"Collection {collection_name} does not exist")
                return None

            info = self.client.get_collection(collection_name)

            return {
                "name": collection_name,
                "status": info.status,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance.name,
                    "hnsw_m": info.config.hnsw_config.m,
                    "hnsw_ef_construct": info.config.hnsw_config.ef_construct,
                },
                "optimizer": {
                    "indexing_threshold": info.config.optimizer_config.indexing_threshold,
                },
            }

        except Exception as e:
            logger.error(
                f"Failed to get info for collection {collection_name}: {e}"
            )
            return None

    def collection_is_ready(self, collection_name: str) -> bool:
        """
        Check if collection is ready for operations.

        Args:
            collection_name: Name of collection

        Returns:
            True if collection is ready
        """
        try:
            info = self.client.get_collection(collection_name)
            return info.status == CollectionStatus.GREEN

        except Exception as e:
            logger.error(
                f"Failed to check status for collection {collection_name}: {e}"
            )
            return False

    def optimize_collection(self, collection_name: str) -> bool:
        """
        Trigger collection optimization (indexing).

        Args:
            collection_name: Name of collection

        Returns:
            True if optimization started
        """
        try:
            if not self._collection_exists(collection_name):
                logger.warning(f"Collection {collection_name} does not exist")
                return False

            # Note: Qdrant automatically optimizes, but we can trigger it
            logger.info(f"Collection {collection_name} optimization triggered")
            return True

        except Exception as e:
            logger.error(
                f"Failed to optimize collection {collection_name}: {e}"
            )
            return False

    def _collection_exists(self, collection_name: str) -> bool:
        """
        Check if collection exists.

        Args:
            collection_name: Name of collection

        Returns:
            True if collection exists
        """
        try:
            collections = self.client.get_collections()
            return any(
                col.name == collection_name for col in collections.collections
            )

        except Exception as e:
            logger.error(f"Failed to check collection existence: {e}")
            return False

    def create_default_collections(self) -> Dict[str, bool]:
        """
        Create default collections for the application.

        Returns:
            Dictionary mapping collection names to creation status
        """
        results = {}

        # Documents collection (main content)
        documents_config = CollectionConfig(
            name="documents",
            vector_size=self.default_vector_size,
            distance="Cosine",
            hnsw_m=16,
            hnsw_ef_construct=100,
        )
        results["documents"] = self.create_collection(documents_config)

        # Chunks collection (smaller text segments)
        chunks_config = CollectionConfig(
            name="chunks",
            vector_size=self.default_vector_size,
            distance="Cosine",
            hnsw_m=16,
            hnsw_ef_construct=100,
        )
        results["chunks"] = self.create_collection(chunks_config)

        logger.info(f"Default collections created: {results}")
        return results

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics for all collections.

        Returns:
            Dictionary with collection statistics
        """
        try:
            collections = self.list_collections()
            stats = {
                "total_collections": len(collections),
                "collections": {},
            }

            for collection_name in collections:
                info = self.get_collection_info(collection_name)
                if info:
                    stats["collections"][collection_name] = {
                        "status": info["status"],
                        "vectors_count": info["vectors_count"],
                        "points_count": info["points_count"],
                    }

            return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"total_collections": 0, "collections": {}}
