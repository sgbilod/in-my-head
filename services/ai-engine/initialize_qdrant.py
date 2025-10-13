"""
Initialize Qdrant vector database collections.
Creates 3 collections: document_embeddings, chunk_embeddings, kg_node_embeddings.
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

QDRANT_URL = "http://localhost:6333"

def initialize_qdrant():
    """Create all required Qdrant collections."""
    client = QdrantClient(url=QDRANT_URL)

    print(f"Connected to Qdrant at {QDRANT_URL}\n")

    collections = [
        {
            "name": "document_embeddings",
            "vector_size": 1536,  # OpenAI ada-002 dimension
            "distance": Distance.COSINE,
            "description": "Document-level embeddings for semantic search"
        },
        {
            "name": "chunk_embeddings",
            "vector_size": 1536,  # OpenAI ada-002 dimension
            "distance": Distance.COSINE,
            "description": "Chunk-level embeddings for fine-grained search"
        },
        {
            "name": "kg_node_embeddings",
            "vector_size": 768,  # sentence-transformers dimension
            "distance": Distance.COSINE,
            "description": "Knowledge graph node embeddings"
        }
    ]

    created_count = 0
    existing_count = 0

    for collection_config in collections:
        collection_name = collection_config["name"]

        # Check if collection exists
        existing_collections = client.get_collections().collections
        if any(c.name == collection_name for c in existing_collections):
            print(f"⚠️  Collection '{collection_name}' already exists - skipping")
            existing_count += 1
            continue

        # Create collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=collection_config["vector_size"],
                distance=collection_config["distance"]
            )
        )

        print(f"✅ Created collection '{collection_name}'")
        print(f"   - Vector size: {collection_config['vector_size']}")
        print(f"   - Distance: {collection_config['distance']}")
        print(f"   - Description: {collection_config['description']}\n")
        created_count += 1

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Created: {created_count} collections")
    print(f"  Existing: {existing_count} collections")
    print(f"  Total: {created_count + existing_count} collections")
    print(f"{'='*60}")

    # Verify all collections
    print("\nVerifying collections:")
    all_collections = client.get_collections().collections
    for collection in all_collections:
        info = client.get_collection(collection.name)
        print(f"  ✅ {collection.name}")
        print(f"     Points: {info.points_count}")
        print(f"     Vectors: {info.vectors_count if hasattr(info, 'vectors_count') else 'N/A'}")

    return created_count + existing_count

if __name__ == "__main__":
    try:
        count = initialize_qdrant()
        print(f"\n✅ Qdrant initialization complete! {count} collections ready.")
        exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)
