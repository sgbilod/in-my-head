import asyncio
import asyncpg


async def fix_documents_id():
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='inmyhead',
        password='inmyhead_dev_pass',
        database='inmyhead_dev'
    )
    
    print("Adding DEFAULT gen_random_uuid() to documents.id...")
    
    await conn.execute("""
        ALTER TABLE documents 
        ALTER COLUMN id SET DEFAULT gen_random_uuid()
    """)
    
    print("✅ Successfully added default UUID generation to documents.id")
    
    # Verify the change
    result = await conn.fetchrow("""
        SELECT column_default
        FROM information_schema.columns
        WHERE table_name = 'documents' AND column_name = 'id'
    """)
    
    print(f"New default value: {result['column_default']}")
    
    await conn.close()


if __name__ == "__main__":
    asyncio.run(fix_documents_id())
