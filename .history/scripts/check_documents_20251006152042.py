"""
Check existing documents in database.
"""

import asyncio
import asyncpg


async def check_documents():
    """Check documents in database."""
    
    db_url = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    
    conn = await asyncpg.connect(db_url)
    
    # Get document count
    count = await conn.fetchval("SELECT COUNT(*) FROM documents")
    print(f"\n📊 Total documents: {count}")
    
    # Get sample documents
    docs = await conn.fetch("""
        SELECT id, title, content_type, char_count, created_at
        FROM documents
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    print("\n📄 Recent documents:")
    for doc in docs:
        print(f"  - {doc['title'][:50]:50} | {doc['content_type']:15} | {doc['char_count']:8} chars")
    
    # Check if any have embeddings
    with_embeddings = await conn.fetchval("""
        SELECT COUNT(*) FROM documents WHERE embedding IS NOT NULL
    """)
    
    print(f"\n🔢 Documents with embeddings: {with_embeddings}")
    
    await conn.close()


if __name__ == "__main__":
    asyncio.run(check_documents())
