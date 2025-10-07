"""Fix conversations table schema - remove foreign key constraint."""
import asyncio
import asyncpg


async def fix_table():
    """Remove users foreign key constraint."""
    conn = await asyncpg.connect(
        "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    )
    
    print("Fixing conversations table...")
    
    # Drop the foreign key constraint
    await conn.execute("""
        ALTER TABLE conversations 
        DROP CONSTRAINT IF EXISTS conversations_user_id_fkey;
    """)
    print("✅ Dropped foreign key constraint")
    
    # Make ai_model and ai_provider nullable
    await conn.execute("""
        ALTER TABLE conversations 
        ALTER COLUMN ai_model DROP NOT NULL;
    """)
    print("✅ Made ai_model nullable")
    
    await conn.execute("""
        ALTER TABLE conversations 
        ALTER COLUMN ai_provider DROP NOT NULL;
    """)
    print("✅ Made ai_provider nullable")
    
    await conn.close()
    print("\n✅ Table fixed successfully!")


if __name__ == "__main__":
    asyncio.run(fix_table())
