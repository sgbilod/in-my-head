"""
Run Collections Migration

Execute the 002_add_collections.sql migration on the database.
"""

import asyncio
import asyncpg
import os
from pathlib import Path


async def run_migration():
    """Execute the collections migration."""
    # Database connection
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev",
    )

    print("🔄 Connecting to database...")
    conn = await asyncpg.connect(db_url)

    try:
        # Read migration file
        migration_file = Path("services/ai-engine/migrations/002_add_collections.sql")
        print(f"📄 Reading migration: {migration_file}")

        migration_sql = migration_file.read_text()

        # Execute migration
        print("⚡ Executing migration...")
        await conn.execute(migration_sql)

        print("✅ Migration completed successfully!")

        # Verify tables
        print("\n📊 Verifying collections table...")
        result = await conn.fetch(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'collections'
            ORDER BY ordinal_position;
            """
        )

        if result:
            print("✅ Collections table created:")
            for row in result:
                print(f"   - {row['column_name']}: {row['data_type']}")
        else:
            print("❌ Collections table not found!")

        # Verify collection_id column in documents
        print("\n📊 Verifying documents.collection_id...")
        result = await conn.fetchrow(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'documents' AND column_name = 'collection_id';
            """
        )

        if result:
            print(f"✅ documents.collection_id added: {result['data_type']}")
        else:
            print("❌ documents.collection_id not found!")

        # Verify triggers
        print("\n📊 Verifying triggers...")
        triggers = await conn.fetch(
            """
            SELECT trigger_name, event_object_table
            FROM information_schema.triggers
            WHERE trigger_name LIKE '%collection%';
            """
        )

        if triggers:
            print("✅ Triggers created:")
            for trigger in triggers:
                print(
                    f"   - {trigger['trigger_name']} on {trigger['event_object_table']}"
                )
        else:
            print("⚠️  No collection triggers found")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()
        print("\n🔒 Database connection closed")


if __name__ == "__main__":
    asyncio.run(run_migration())
