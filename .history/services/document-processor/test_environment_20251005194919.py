"""
Quick development environment verification script.
Tests database connection, imports, and basic functionality.
"""
import sys
from sqlalchemy import create_engine, text

def test_database_connection():
    """Test PostgreSQL connection."""
    print("🔍 Testing database connection...")
    
    db_url = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text('SELECT COUNT(*) FROM users'))
            user_count = result.scalar()
            
            # Count all tables
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """))
            table_count = result.scalar()
            
        engine.dispose()
        
        print(f"✅ Database connection successful!")
        print(f"   • Tables: {table_count}")
        print(f"   • Users: {user_count}")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_imports():
    """Test that all critical imports work."""
    print("\n🔍 Testing Python imports...")
    
    imports_to_test = [
        ("sqlalchemy", "SQLAlchemy ORM"),
        ("alembic", "Database migrations"),
        ("fastapi", "FastAPI framework"),
        ("pydantic", "Data validation"),
        ("passlib", "Password hashing"),
        ("python-multipart", "File uploads"),
    ]
    
    failed = []
    
    for module_name, description in imports_to_test:
        try:
            __import__(module_name.replace("-", "_"))
            print(f"✅ {description}: OK")
        except ImportError as e:
            print(f"❌ {description}: MISSING")
            failed.append(module_name)
    
    if failed:
        print(f"\n⚠️  Missing packages: {', '.join(failed)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def test_models():
    """Test that database models can be imported."""
    print("\n🔍 Testing database models...")
    
    try:
        from src.models.database import User, Document, Collection, Tag
        print("✅ Database models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import models: {e}")
        return False

def main():
    """Run all verification tests."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     IN MY HEAD - Development Environment Verification       ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    results = []
    
    # Test database
    results.append(("Database Connection", test_database_connection()))
    
    # Test imports
    results.append(("Python Packages", test_imports()))
    
    # Test models
    results.append(("Database Models", test_models()))
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All checks passed! Your environment is ready for development!")
        print("\n🚀 Next steps:")
        print("   1. Start FastAPI server: uvicorn src.main:app --reload")
        print("   2. Open http://localhost:8000/docs for API documentation")
        print("   3. Start developing features!")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
