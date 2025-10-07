"""Fix collections table id column to have default UUID"""
import asyncio
import asyncpg

async def fix():
    conn = await asyncpg.connect(
        'postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev'
    )
    
    print("Fixing collections table id column...")
    
    try:
        # Add default to id column
        await conn.execute("""
            ALTER TABLE collections 
            ALTER COLUMN id SET DEFAULT gen_random_uuid()
        """)
        print("✅ Added default gen_random_uuid() to collections.id")
        
        # Verify
        result = await conn.fetchrow("""
            SELECT column_default
            FROM information_schema.columns
            WHERE table_name = 'collections' AND column_name = 'id'
        """)
        print(f"✅ Verified: collections.id default = {result['column_default']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

asyncio.run(fix())
