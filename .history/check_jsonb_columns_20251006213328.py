"""Check if citations column is actually JSONB."""
import asyncio
import asyncpg


async def check_column_types():
    """Check messages table column types."""
    conn = await asyncpg.connect(
        "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    )
    
    columns = await conn.fetch("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'messages'
        AND column_name IN ('rag_context', 'citations')
    """)
    
    for col in columns:
        print(f"{col['column_name']}: {col['data_type']}")
    
    # Fix if they're not JSONB
    for col in columns:
        if col['data_type'] != 'jsonb':
            print(f"\nFixing {col['column_name']} to be JSONB...")
            await conn.execute(f"""
                ALTER TABLE messages
                ALTER COLUMN {col['column_name']} TYPE JSONB
                USING {col['column_name']}::jsonb
            """)
            print(f"✅ Fixed {col['column_name']}")
    
    await conn.close()


if __name__ == "__main__":
    asyncio.run(check_column_types())
