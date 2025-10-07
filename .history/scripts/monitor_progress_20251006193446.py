"""Monitor embedding generation progress."""

import asyncio
import asyncpg
import time
from qdrant_client import QdrantClient


async def check_status():
    """Check current status."""
    # Check PostgreSQL
    try:
        conn = await asyncpg.connect(
            "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
        )
        chunk_count = await conn.fetchval("SELECT COUNT(*) FROM document_chunks")
        embedded_count = await conn.fetchval(
            "SELECT COUNT(*) FROM document_chunks WHERE has_embedding = TRUE"
        )
        await conn.close()
        
        print(f"📊 PostgreSQL:")
        print(f"   Chunks: {chunk_count}")
        print(f"   With embeddings: {embedded_count}")
    except Exception as e:
        print(f"❌ PostgreSQL error: {e}")
    
    # Check Qdrant
    try:
        qdrant = QdrantClient(url="http://localhost:6333")
        collections = qdrant.get_collections().collections
        
        print(f"\n📊 Qdrant:")
        if collections:
            for col in collections:
                info = qdrant.get_collection(col.name)
                print(f"   {col.name}: {info.points_count} vectors")
        else:
            print("   No collections yet")
    except Exception as e:
        print(f"❌ Qdrant error: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print(f"Progress Check - {time.strftime('%H:%M:%S')}")
    print("=" * 50)
    asyncio.run(check_status())
