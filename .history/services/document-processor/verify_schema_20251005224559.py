"""
Verify database schema - check all tables exist.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import inspect
from src.database.connection import engine

def verify_tables():
    """Verify all 15 tables exist in the database."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = [
        'users',
        'collections',
        'documents',
        'tags',
        'document_tags',
        'annotations',
        'conversations',
        'messages',
        'queries',
        'resources',
        'knowledge_graph_nodes',
        'knowledge_graph_edges',
        'processing_jobs',
        'api_keys',
        'system_settings',
        'alembic_version'
    ]
    
    print("=" * 60)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 60)
    print(f"\nTotal tables found: {len(tables)}\n")
    
    print("Tables in database:")
    for table in sorted(tables):
        status = "✅" if table in expected_tables or table == 'alembic_version' else "⚠️"
        print(f"  {status} {table}")
    
    print("\nExpected tables check:")
    for expected in expected_tables:
        if expected in tables:
            print(f"  ✅ {expected}")
        else:
            print(f"  ❌ {expected} - MISSING")
    
    # Get detailed info for documents table
    print("\n" + "=" * 60)
    print("DOCUMENTS TABLE SCHEMA")
    print("=" * 60)
    
    if 'documents' in tables:
        columns = inspector.get_columns('documents')
        print(f"\nTotal columns: {len(columns)}\n")
        for col in columns:
            print(f"  • {col['name']:30s} {str(col['type']):20s} {'NOT NULL' if not col['nullable'] else ''}")
        
        # Get indexes
        indexes = inspector.get_indexes('documents')
        print(f"\nIndexes on documents table: {len(indexes)}")
        for idx in indexes:
            print(f"  • {idx['name']}: {', '.join(idx['column_names'])}")
        
        # Get foreign keys
        fks = inspector.get_foreign_keys('documents')
        print(f"\nForeign keys on documents table: {len(fks)}")
        for fk in fks:
            print(f"  • {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    
    # Check for test user from seed
    from src.database.connection import get_db
    from src.models.database import User, Collection, Tag
    
    print("\n" + "=" * 60)
    print("SEED DATA VERIFICATION")
    print("=" * 60)
    
    with get_db() as db:
        user_count = db.query(User).count()
        collection_count = db.query(Collection).count()
        tag_count = db.query(Tag).count()
        
        print(f"\n  Users: {user_count}")
        print(f"  Collections: {collection_count}")
        print(f"  Tags: {tag_count}")
        
        if user_count > 0:
            test_user = db.query(User).filter(User.username == 'testuser').first()
            if test_user:
                print(f"\n  ✅ Test user exists: {test_user.username} ({test_user.email})")
                print(f"     ID: {test_user.id}")
                print(f"     Created: {test_user.created_at}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    verify_tables()
