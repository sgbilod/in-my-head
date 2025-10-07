"""Fix document_count column default"""
import asyncio
import asyncpg

async def fix():
    conn = await asyncpg.connect(
        'postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev'
    )
    
    print("Fixing document_count default...")
    
    try:
        await conn.execute("""
            ALTER TABLE collections 
            ALTER COLUMN document_count SET DEFAULT 0
        """)
        print("✅ Set document_count default to 0")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

asyncio.run(fix())
