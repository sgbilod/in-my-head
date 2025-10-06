"""
Get documents table schema.
"""

import asyncio
import asyncpg


async def get_schema():
    """Get documents table schema."""
    
    db_url = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    
    conn = await asyncpg.connect(db_url)
    
    # Get columns
    columns = await conn.fetch("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'documents'
        ORDER BY ordinal_position
    """)
    
    print("\n📋 Documents table schema:")
    for col in columns:
        print(f"  - {col['column_name']:30} {col['data_type']}")
    
    # Get sample document
    doc = await conn.fetchrow("SELECT * FROM documents LIMIT 1")
    
    if doc:
        print("\n📄 Sample document fields:")
        for key in dict(doc).keys():
            value = doc[key]
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"  - {key:30} {value}")
    
    await conn.close()


if __name__ == "__main__":
    asyncio.run(get_schema())
