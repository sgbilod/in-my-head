"""Check database tables"""
import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect(
        'postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev'
    )
    
    # Check tables
    tables = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
    )
    print("Tables:", [r['tablename'] for r in tables])
    
    # Check if collections table exists
    collections_exists = await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'collections')"
    )
    print(f"Collections table exists: {collections_exists}")
    
    # Check if collection_id column exists in documents
    column_exists = await conn.fetchval("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'documents' AND column_name = 'collection_id'
        )
    """)
    print(f"documents.collection_id exists: {column_exists}")
    
    await conn.close()

asyncio.run(check())
