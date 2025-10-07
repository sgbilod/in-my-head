"""Check collections table schema"""
import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect(
        'postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev'
    )
    
    # Get table schema
    columns = await conn.fetch("""
        SELECT column_name, data_type, column_default, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'collections'
        ORDER BY ordinal_position
    """)
    
    print("Collections table schema:")
    for col in columns:
        print(f"  {col['column_name']:20} {col['data_type']:15} "
              f"default={col['column_default']} nullable={col['is_nullable']}")
    
    await conn.close()

asyncio.run(check())
