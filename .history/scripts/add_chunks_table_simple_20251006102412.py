"""
Create document_chunks table using raw SQL.

Simpler migration that doesn't rely on SQLAlchemy table resolution.
"""

import asyncio
import asyncpg
from datetime import datetime


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Chunk content
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    
    -- Position tracking
    start_position INTEGER NOT NULL,
    end_position INTEGER NOT NULL,
    
    -- Statistics
    char_count INTEGER NOT NULL,
    word_count INTEGER NOT NULL,
    sentence_count INTEGER NOT NULL,
    
    -- Chunking metadata
    chunking_strategy VARCHAR(50) NOT NULL,
    chunk_metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Vector search
    embedding_id UUID UNIQUE,
    embedding_model VARCHAR(100),
    has_embedding BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_chunking_strategy CHECK (
        chunking_strategy IN ('sentence', 'paragraph', 'fixed', 'semantic')
    ),
    CONSTRAINT check_chunk_index_positive CHECK (chunk_index >= 0),
    CONSTRAINT check_start_position_positive CHECK (start_position >= 0),
    CONSTRAINT check_end_position CHECK (end_position > start_position)
);
"""

CREATE_INDEXES_SQL = [
    """
    CREATE INDEX IF NOT EXISTS idx_chunks_document_index 
    ON document_chunks(document_id, chunk_index);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
    ON document_chunks(document_id, has_embedding);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_chunks_created_at 
    ON document_chunks(created_at);
    """
]


async def run_migration():
    """Run the document_chunks table migration."""
    
    print("\n" + "=" * 70)
    print("=== DOCUMENT CHUNKS TABLE MIGRATION (SQL) ===")
    print("=" * 70)
    
    db_url = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    
    try:
        # Connect to database
        conn = await asyncpg.connect(db_url)
        
        print(f"\n📊 Database: localhost:5434/inmyhead_dev")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check if table already exists
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'document_chunks'
            );
        """)
        
        if exists:
            print("\n⚠️  Table 'document_chunks' already exists!")
            response = input("Drop and recreate? (yes/no): ")
            
            if response.lower() == 'yes':
                print("\n🗑️  Dropping existing table...")
                await conn.execute("DROP TABLE document_chunks CASCADE;")
                print("✅ Table dropped")
            else:
                print("\n❌ Migration cancelled")
                await conn.close()
                return
        
        # Create table
        print("\n📝 Creating document_chunks table...")
        await conn.execute(CREATE_TABLE_SQL)
        print("✅ Table created")
        
        # Create indexes
        print("\n🔍 Creating indexes...")
        for i, index_sql in enumerate(CREATE_INDEXES_SQL, 1):
            await conn.execute(index_sql)
            print(f"  ✅ Index {i}/3 created")
        
        # Verify creation
        print("\n🔎 Verifying table structure...")
        
        # Get column count
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'document_chunks'
            ORDER BY ordinal_position;
        """)
        
        print(f"\n📋 Columns ({len(columns)}):")
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  - {col['column_name']:20} {col['data_type']:20} {nullable}")
        
        # Get index count
        indexes = await conn.fetch("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'document_chunks';
        """)
        
        print(f"\n🔍 Indexes ({len(indexes)}):")
        for idx in indexes:
            print(f"  - {idx['indexname']}")
        
        # Get constraints
        constraints = await conn.fetch("""
            SELECT conname, contype
            FROM pg_constraint
            WHERE conrelid = 'document_chunks'::regclass;
        """)
        
        print(f"\n🔒 Constraints ({len(constraints)}):")
        for const in constraints:
            ctype = {
                'p': 'PRIMARY KEY',
                'f': 'FOREIGN KEY',
                'c': 'CHECK',
                'u': 'UNIQUE'
            }.get(const['contype'], 'UNKNOWN')
            print(f"  - {const['conname']:40} ({ctype})")
        
        await conn.close()
        
        print("\n" + "=" * 70)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 70)
        
        print("\n📋 Next Steps:")
        print("  1. Update document-processor to store chunks after parsing")
        print("  2. Use chunking service to split existing documents")
        print("  3. Generate embeddings for all chunks")
        print("  4. Store embeddings in Qdrant collection 'chunk_embeddings'")
        print("  5. Test RAG retrieval with /rag/retrieve endpoint")
        print()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Entry point."""
    asyncio.run(run_migration())


if __name__ == "__main__":
    main()
