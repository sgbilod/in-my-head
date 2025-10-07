import asyncio
import asyncpg

async def check_documents_schema():
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='inmyhead',
        password='inmyhead_dev_pass',
        database='inmyhead_dev'
    )
    
    # Get columns from documents table
    rows = await conn.fetch("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'documents'
        ORDER BY ordinal_position
    """)
    
    print("Documents table schema:")
    print("-" * 80)
    for row in rows:
        print(f"{row['column_name']:20} {row['data_type']:20} Nullable: {row['is_nullable']:5} Default: {row['column_default']}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_documents_schema())
