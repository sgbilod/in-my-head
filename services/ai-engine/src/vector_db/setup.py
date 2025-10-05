"""
Qdrant vector database setup and initialization.
"""

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List
import uuid
import logging

logger = logging.getLogger(__name__)

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


class QdrantSetup:
    """
    Manages Qdrant vector database setup and initialization.
    
    Creates three collections:
    1. document_embeddings: Full document embeddings (1536 dimensions)
    2. chunk_embeddings: Document chunk embeddings (1536 dimensions)
    3. kg_node_embeddings: Knowledge graph node embeddings (768 dimensions)
    """
    
    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT):
        """
        Initialize Qdrant client.
        
        Args:
            host: Qdrant server host
            port: Qdrant server port
        """
        self.client = QdrantClient(
            host=host,
            port=port,
            api_key=QDRANT_API_KEY,
            timeout=30.0
        )
        logger.info(f"Initialized Qdrant client at {host}:{port}")
    
    def create_collections(self) -> None:
        """Create all required Qdrant collections."""
        print("=" * 60)
        print("Setting up Qdrant Vector Database Collections")
        print("=" * 60)
        
        # Collection configurations
        collections = [
            {
                "name": "document_embeddings",
                "vector_size": 1536,
                "distance": Distance.COSINE,
                "description": "Full document embeddings (OpenAI ada-002)"
            },
            {
                "name": "chunk_embeddings",
                "vector_size": 1536,
                "distance": Distance.COSINE,
                "description": "Document chunk embeddings for granular search"
            },
            {
                "name": "kg_node_embeddings",
                "vector_size": 768,
                "distance": Distance.COSINE,
                "description": (
                    "Knowledge graph node embeddings (sentence-transformers)"
                )
            }
        ]
        
        for config in collections:
            self._create_collection(
                name=config["name"],
                vector_size=config["vector_size"],
                distance=config["distance"],
                description=config["description"]
            )
        
        print("=" * 60)
        print("✅ Qdrant collections created successfully!")
        print("=" * 60)
    
    def _create_collection(
        self,
        name: str,
        vector_size: int,
        distance: Distance,
        description: str
    ) -> None:
        """
        Create a single Qdrant collection.
        
        Args:
            name: Collection name
            vector_size: Vector dimension size
            distance: Distance metric (COSINE, DOT, EUCLIDEAN)
            description: Collection description
        """
        try:
            # Check if collection already exists
            collections = self.client.get_collections().collections
            exists = any(col.name == name for col in collections)
            
            if exists:
                print(f"⚠️  Collection '{name}' already exists, skipping...")
                return
            
            # Create collection
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            
            print(f"✅ Created collection: {name}")
            print(f"   - Vector size: {vector_size}")
            print(f"   - Distance metric: {distance.value}")
            print(f"   - Description: {description}")
            
        except Exception as e:
            logger.error(f"Failed to create collection '{name}': {e}")
            print(f"❌ Failed to create collection '{name}': {e}")
            raise
    
    def add_test_vectors(self) -> None:
        """
        Add test vectors to verify collections are working.
        """
        print("\n" + "=" * 60)
        print("Adding test vectors for validation")
        print("=" * 60)
        
        # Test data for document_embeddings
        self._add_test_vector(
            collection_name="document_embeddings",
            vector_size=1536,
            payload={
                "document_id": str(uuid.uuid4()),
                "title": "Test Document",
                "type": "test"
            }
        )
        
        # Test data for chunk_embeddings
        self._add_test_vector(
            collection_name="chunk_embeddings",
            vector_size=1536,
            payload={
                "document_id": str(uuid.uuid4()),
                "chunk_index": 0,
                "content": "This is a test chunk",
                "type": "test"
            }
        )
        
        # Test data for kg_node_embeddings
        self._add_test_vector(
            collection_name="kg_node_embeddings",
            vector_size=768,
            payload={
                "node_id": str(uuid.uuid4()),
                "entity_name": "Test Entity",
                "entity_type": "test",
                "type": "test"
            }
        )
        
        print("=" * 60)
        print("✅ Test vectors added successfully!")
        print("=" * 60)
    
    def _add_test_vector(
        self,
        collection_name: str,
        vector_size: int,
        payload: dict
    ) -> None:
        """
        Add a single test vector to a collection.
        
        Args:
            collection_name: Name of the collection
            vector_size: Size of the vector
            payload: Metadata to attach to the vector
        """
        try:
            # Generate random test vector (all zeros for simplicity)
            test_vector = [0.0] * vector_size
            
            # Add vector to collection
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=test_vector,
                        payload=payload
                    )
                ]
            )
            
            print(f"✅ Added test vector to {collection_name}")
            
        except Exception as e:
            logger.error(
                f"Failed to add test vector to '{collection_name}': {e}"
            )
            print(f"❌ Failed to add test vector to '{collection_name}': {e}")
            raise
    
    def get_collection_info(self, collection_name: str) -> dict:
        """
        Get information about a collection.
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            Dictionary with collection info
        """
        try:
            collection_info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status.value
            }
        except Exception as e:
            logger.error(
                f"Failed to get info for collection '{collection_name}': {e}"
            )
            return {}
    
    def list_collections(self) -> List[str]:
        """
        List all collections in Qdrant.
        
        Returns:
            List of collection names
        """
        collections = self.client.get_collections().collections
        return [col.name for col in collections]
    
    def health_check(self) -> bool:
        """
        Check if Qdrant is healthy and responsive.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to get collections list
            self.client.get_collections()
            logger.info("Qdrant health check passed")
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


def main():
    """Main setup function."""
    try:
        # Initialize setup
        setup = QdrantSetup()
        
        # Check health
        print("\nChecking Qdrant connection...")
        if not setup.health_check():
            print("❌ Failed to connect to Qdrant")
            print(f"   Please ensure Qdrant is running at {QDRANT_HOST}:{QDRANT_PORT}")
            return
        print("✅ Successfully connected to Qdrant\n")
        
        # Create collections
        setup.create_collections()
        
        # Add test vectors
        setup.add_test_vectors()
        
        # Display collection info
        print("\n" + "=" * 60)
        print("Collection Information")
        print("=" * 60)
        for collection_name in setup.list_collections():
            info = setup.get_collection_info(collection_name)
            print(f"\n📊 {info['name']}:")
            print(f"   - Status: {info['status']}")
            print(f"   - Vectors: {info['vectors_count']}")
            print(f"   - Points: {info['points_count']}")
        
        print("\n" + "=" * 60)
        print("🎉 Qdrant setup completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"\n❌ Setup failed: {e}")
        raise


if __name__ == "__main__":
    main()
