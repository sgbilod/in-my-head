"""
Simple script to create all database tables directly.
Bypasses Alembic for initial setup. Imports only database models, not Pydantic schemas.
"""
import os
import sys
import importlib.util

# Set DATABASE_URL if not already set
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql://inmyhead_user:inmyhead_dev_password_CHANGE_ME_IN_PRODUCTION@localhost:5432/inmyhead"

from sqlalchemy import create_engine

# Import database.py directly, bypassing __init__.py
spec = importlib.util.spec_from_file_location("database_models", "src/models/database.py")
database_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_models)
Base = database_models.Base

def create_tables():
    """Create all tables in the database."""
    database_url = os.environ["DATABASE_URL"]
    print(f"Connecting to database...")

    engine = create_engine(database_url)

    print("Creating tables...")
    Base.metadata.create_all(engine)

    print("✅ All tables created successfully!")

    # List created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\nCreated {len(tables)} tables:")
    for table in sorted(tables):
        print(f"  - {table}")

    return len(tables)

if __name__ == "__main__":
    count = create_tables()
    sys.exit(0 if count > 0 else 1)
