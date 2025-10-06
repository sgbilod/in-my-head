"""
Quick verification script for AI Engine + Qdrant setup.

Tests:
1. Qdrant connection
2. Collection creation
3. Vector insertion
4. Similarity search
5. Collection info
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "ai-engine"))

from src.services.qdrant_service import get_qdrant_service
from src.config import settings


async def verify_setup():
    """Run verification checks."""
    print("\n" + "="*70)
    print("AI ENGINE + QDRANT VERIFICATION")
    print("="*70 + "\n")
    
    # Initialize service
    print("1. Initializing Qdrant service...")
    qdrant = get_qdrant_service()
    
    try:
        await qdrant.initialize()
        print("   ✓ Service initialized\n")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}\n")
        return False
    
    # Check collections
    print("2. Checking collections...")
    for collection_name in [
        settings.qdrant_collection_documents,
        settings.qdrant_collection_chunks,
        settings.qdrant_collection_queries
    ]:
        try:
            info = await qdrant.get_collection_info(collection_name)
            print(f"   ✓ {collection_name}:")
            print(f"      - Vectors: {info['vectors_count']}")
            print(f"      - Points: {info['points_count']}")
            print(f"      - Status: {info['status']}")
        except Exception as e:
            print(f"   ✗ {collection_name}: {e}")
    
    print()
    
    # Test vector operations
    print("3. Testing vector operations...")
    
    # Create test vector
    test_vector = [0.1] * settings.embedding_dimension
    test_point = {
        "id": "test-001",
        "vector": test_vector,
        "payload": {
            "title": "Test Document",
            "content": "This is a test",
            "test": True
        }
    }
    
    try:
        # Insert test vector
        await qdrant.upsert_vectors(
            settings.qdrant_collection_documents,
            [test_point]
        )
        print("   ✓ Inserted test vector")
        
        # Search for similar vectors
        results = await qdrant.search_similar(
            settings.qdrant_collection_documents,
            test_vector,
            limit=5
        )
        print(f"   ✓ Search returned {len(results)} results")
        
        if results:
            print(f"      - Top result: {results[0]['id']}")
            print(f"      - Score: {results[0]['score']:.4f}")
        
        # Clean up test vector
        await qdrant.delete_vectors(
            settings.qdrant_collection_documents,
            ["test-001"]
        )
        print("   ✓ Deleted test vector")
        
    except Exception as e:
        print(f"   ✗ Vector operations failed: {e}")
        return False
    
    print()
    
    # Summary
    print("="*70)
    print("VERIFICATION COMPLETE ✓")
    print("="*70)
    print()
    print("Next Steps:")
    print("1. Start AI Engine: cd services\\ai-engine && .\\start-ai-engine.ps1")
    print("2. Visit API docs: http://localhost:8002/docs")
    print("3. Run migration: python scripts\\migrate_embeddings_to_qdrant.py")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(verify_setup())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Verification failed: {e}")
        sys.exit(1)
