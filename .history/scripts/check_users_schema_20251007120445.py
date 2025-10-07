"""Check users table schema"""
import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect(
        'postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev'
    )
    
    # Get table schema
    columns = await conn.fetch("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)
    
    print("Users table columns:")
    for col in columns:
        print(f"  {col['column_name']:20} {col['data_type']}")
    
    await conn.close()

asyncio.run(check())
