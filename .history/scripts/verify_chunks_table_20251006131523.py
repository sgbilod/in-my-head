"""
Verify document_chunks table exists and has correct structure.
"""

import asyncio
import asyncpg
from sqlalchemy import create_engine, inspect


async def verify_chunks_table():
    """Verify the document_chunks table."""
    
    print("\n" + "=" * 70)
    print("DOCUMENT CHUNKS TABLE VERIFICATION")
    print("=" * 70)
    
    # Database connection
    db_url = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    
    try:
        # Create engine
        engine = create_engine(db_url)
        inspector = inspect(engine)
        
        # Check if table exists
        tables = inspector.get_table_names()
        
        if "document_chunks" not in tables:
            print("\n❌ ERROR: document_chunks table does NOT exist!")
            print("\nAvailable tables:")
            for table in sorted(tables):
                print(f"  - {table}")
            print("\n⚠️  Run migration: python scripts/add_chunks_table_migration.py")
            return False
        
        print("\n✅ document_chunks table EXISTS\n")
        
        # Get columns
        columns = inspector.get_columns("document_chunks")
        print(f"📋 Columns ({len(columns)}):")
        for col in columns:
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            print(f"  - {col['name']:20} {str(col['type']):20} {nullable}")
        
        # Get indexes
        indexes = inspector.get_indexes("document_chunks")
        print(f"\n🔍 Indexes ({len(indexes)}):")
        for idx in indexes:
            cols = ", ".join(idx["column_names"])
            unique = "UNIQUE" if idx.get("unique") else ""
            print(f"  - {idx['name']:40} ON ({cols}) {unique}")
        
        # Get foreign keys
        foreign_keys = inspector.get_foreign_keys("document_chunks")
        print(f"\n🔗 Foreign Keys ({len(foreign_keys)}):")
        for fk in foreign_keys:
            print(f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        
        # Count rows
        conn = await asyncpg.connect(db_url)
        count = await conn.fetchval("SELECT COUNT(*) FROM document_chunks")
        await conn.close()
        
        print(f"\n📊 Row Count: {count}")
        
        print("\n✅ TABLE VERIFICATION COMPLETE")
        print("=" * 70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(verify_chunks_table())
