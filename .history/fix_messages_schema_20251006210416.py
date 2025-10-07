"""Check messages table structure and add missing columns."""
import asyncio
import asyncpg


async def fix_messages_table():
    """Add missing RAG columns to messages table."""
    conn = await asyncpg.connect(
        "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    )
    
    print("Checking messages table...")
    
    # Get current columns
    columns = await conn.fetch("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'messages'
    """)
    column_names = [col['column_name'] for col in columns]
    print(f"Current columns: {', '.join(column_names)}")
    
    # Add missing columns
    if 'rag_context' not in column_names:
        await conn.execute("""
            ALTER TABLE messages 
            ADD COLUMN rag_context JSONB;
        """)
        print("✅ Added rag_context column")
    
    if 'citations' not in column_names:
        await conn.execute("""
            ALTER TABLE messages 
            ADD COLUMN citations JSONB;
        """)
        print("✅ Added citations column")
    
    if 'model' not in column_names:
        await conn.execute("""
            ALTER TABLE messages 
            ADD COLUMN model VARCHAR(100);
        """)
        print("✅ Added model column")
    
    if 'tokens_used' not in column_names:
        await conn.execute("""
            ALTER TABLE messages 
            ADD COLUMN tokens_used INTEGER;
        """)
        print("✅ Added tokens_used column")
    
    await conn.close()
    print("\n✅ Messages table fixed!")


if __name__ == "__main__":
    asyncio.run(fix_messages_table())
