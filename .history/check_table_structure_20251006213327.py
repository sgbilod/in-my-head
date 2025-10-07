"""Check table structure."""
import asyncio
import asyncpg


async def check_table():
    """Check conversations table structure."""
    conn = await asyncpg.connect(
        "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    )
    
    # Get table columns
    columns = await conn.fetch("""
        SELECT column_name, data_type, column_default, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'conversations'
        ORDER BY ordinal_position;
    """)
    
    print("Conversations table structure:")
    print("-" * 80)
    for col in columns:
        default = col['column_default'] or 'NONE'
        print(f"{col['column_name']:<20} {col['data_type']:<15} "
              f"DEFAULT: {default:<30} "
              f"NULL: {col['is_nullable']}")
    
    await conn.close()


if __name__ == "__main__":
    asyncio.run(check_table())
