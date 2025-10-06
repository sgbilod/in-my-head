"""Quick check of embedding generation status."""

import asyncio
import asyncpg


async def check_status():
    """Check current database state."""
    
    conn = await asyncpg.connect(
        "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    )
    
    try:
        # Check documents
        docs = await conn.fetch("""
            SELECT id, title, extracted_text IS NOT NULL as has_text,
                   LENGTH(extracted_text) as text_len
            FROM documents
            WHERE extracted_text IS NOT NULL
        """)
        
        print(f"\n📄 Documents with text: {len(docs)}")
        for doc in docs:
            print(f"  - {doc['title']}: {doc['text_len']} chars")
        
        # Check chunks
        chunk_count = await conn.fetchval(
            "SELECT COUNT(*) FROM document_chunks"
        )
        print(f"\n🧩 Chunks created: {chunk_count}")
        
        if chunk_count > 0:
            chunks_with_embeddings = await conn.fetchval("""
                SELECT COUNT(*) FROM document_chunks
                WHERE has_embedding = TRUE
            """)
            print(f"✅ Chunks with embeddings: {chunks_with_embeddings}")
    
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_status())
