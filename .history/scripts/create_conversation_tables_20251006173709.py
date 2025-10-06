"""
Database migration: Add conversations and messages tables.

This creates the conversation management schema for multi-turn chat with RAG.

Tables:
- conversations: Conversation sessions
- messages: Individual messages with RAG context and citations
"""

import asyncio
import asyncpg


MIGRATION_SQL = """
-- =====================================================================
-- CONVERSATIONS TABLE
-- =====================================================================

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for conversations
CREATE INDEX IF NOT EXISTS idx_conversations_user 
    ON conversations(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_updated 
    ON conversations(updated_at DESC);


-- =====================================================================
-- MESSAGES TABLE
-- =====================================================================

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    
    -- RAG-specific fields
    rag_context JSONB,  -- Retrieved context chunks
    citations JSONB,    -- Source citations used in answer
    
    -- LLM metadata
    model VARCHAR(100),
    temperature FLOAT,
    tokens_used INTEGER,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for messages
CREATE INDEX IF NOT EXISTS idx_messages_conversation 
    ON messages(conversation_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_messages_role 
    ON messages(conversation_id, role);


-- =====================================================================
-- UPDATE TRIGGER FOR CONVERSATIONS
-- =====================================================================

CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_conversation_timestamp ON messages;
CREATE TRIGGER trigger_update_conversation_timestamp
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();
"""


async def run_migration():
    """Run the conversation management migration."""
    
    print("=" * 70)
    print("CONVERSATION MANAGEMENT SCHEMA MIGRATION")
    print("=" * 70)
    
    db_url = (
        "postgresql://inmyhead:inmyhead_dev_pass@"
        "localhost:5434/inmyhead_dev"
    )
    
    try:
        print("\n[1/3] Connecting to database...")
        conn = await asyncpg.connect(db_url)
        print("     ✅ Connected")
        
        print("\n[2/3] Running migration...")
        await conn.execute(MIGRATION_SQL)
        print("     ✅ Tables created")
        
        print("\n[3/3] Verifying schema...")
        
        # Check conversations table
        conv_cols = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'conversations'
            ORDER BY ordinal_position
        """)
        
        print(f"\n     📋 Conversations table ({len(conv_cols)} columns):")
        for col in conv_cols:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"        - {col['column_name']:<20} {col['data_type']:<15} {nullable}")
        
        # Check messages table
        msg_cols = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'messages'
            ORDER BY ordinal_position
        """)
        
        print(f"\n     📋 Messages table ({len(msg_cols)} columns):")
        for col in msg_cols:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"        - {col['column_name']:<20} {col['data_type']:<15} {nullable}")
        
        # Check indexes
        indexes = await conn.fetch("""
            SELECT tablename, indexname
            FROM pg_indexes
            WHERE tablename IN ('conversations', 'messages')
            AND schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        
        print(f"\n     🔍 Indexes ({len(indexes)}):")
        for idx in indexes:
            print(f"        - {idx['tablename']}.{idx['indexname']}")
        
        # Check triggers
        triggers = await conn.fetch("""
            SELECT trigger_name, event_object_table
            FROM information_schema.triggers
            WHERE event_object_table IN ('conversations', 'messages')
            AND trigger_schema = 'public'
        """)
        
        print(f"\n     ⚡ Triggers ({len(triggers)}):")
        for trg in triggers:
            print(f"        - {trg['event_object_table']}.{trg['trigger_name']}")
        
        print(f"\n{'=' * 70}")
        print("✅ MIGRATION COMPLETE!")
        print(f"{'=' * 70}")
        print("\nSchema ready for conversation management:")
        print("  - conversations: Track chat sessions")
        print("  - messages: Store user/assistant messages with RAG context")
        print("  - Auto-update conversation timestamps on new messages")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if conn:
            await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
