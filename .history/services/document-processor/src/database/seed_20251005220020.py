"""
Seed data script for development and testing.
Creates test user, collections, and tags.
"""

from src.database.connection import get_db, init_db
from src.models.database import User, Collection, Tag
import uuid
import hashlib
import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Simple password hashing for development (use proper hashing in production)"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_seed_data():
    """Create initial seed data for development."""
    print("=" * 50)
    print("Creating seed data for In My Head...")
    print("=" * 50)
    
    # Initialize database first
    init_db()
    
    with get_db() as db:
        # Check if test user already exists
        existing_user = db.query(User).filter_by(username="testuser").first()
        if existing_user:
            print("⚠️  Test user already exists, skipping seed data creation")
            return
        
        # Create test user
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            username="testuser",
            email="test@inmyhead.dev",
            password_hash=pwd_context.hash("testpassword123"),
            full_name="Test User",
            preferences={"theme": "dark", "language": "en"},
            is_verified=True,
            is_active=True
        )
        db.add(user)
        db.flush()
        
        print(f"✅ Created test user: testuser")
        print(f"   Email: test@inmyhead.dev")
        print(f"   Password: testpassword123")
        print(f"   User ID: {user_id}")
        
        # Create default collection
        default_collection_id = uuid.uuid4()
        default_collection = Collection(
            id=default_collection_id,
            user_id=user.id,
            name="My Documents",
            description="Default collection for all documents",
            color="#6366F1",
            icon="folder",
            is_default=True
        )
        db.add(default_collection)
        print(f"✅ Created default collection: My Documents ({default_collection_id})")
        
        # Create sample collections
        work_collection_id = uuid.uuid4()
        work_collection = Collection(
            id=work_collection_id,
            user_id=user.id,
            name="Work",
            description="Work-related documents and notes",
            color="#10B981",
            icon="briefcase"
        )
        db.add(work_collection)
        print(f"✅ Created collection: Work ({work_collection_id})")
        
        personal_collection_id = uuid.uuid4()
        personal_collection = Collection(
            id=personal_collection_id,
            user_id=user.id,
            name="Personal",
            description="Personal documents and notes",
            color="#F59E0B",
            icon="home"
        )
        db.add(personal_collection)
        print(f"✅ Created collection: Personal ({personal_collection_id})")
        
        research_collection_id = uuid.uuid4()
        research_collection = Collection(
            id=research_collection_id,
            user_id=user.id,
            name="Research",
            description="Research papers and articles",
            color="#8B5CF6",
            icon="flask"
        )
        db.add(research_collection)
        print(f"✅ Created collection: Research ({research_collection_id})")
        
        # Create sample tags
        tags_data = [
            {"name": "important", "color": "#EF4444"},
            {"name": "urgent", "color": "#F97316"},
            {"name": "research", "color": "#8B5CF6"},
            {"name": "todo", "color": "#F59E0B"},
            {"name": "reference", "color": "#06B6D4"},
            {"name": "archive", "color": "#6B7280"},
            {"name": "favorite", "color": "#EC4899"},
        ]
        
        for tag_data in tags_data:
            tag = Tag(
                id=uuid.uuid4(),
                user_id=user.id,
                name=tag_data["name"],
                color=tag_data["color"]
            )
            db.add(tag)
            print(f"✅ Created tag: {tag_data['name']}")
        
        db.commit()
        
        print("=" * 50)
        print("✅ Seed data created successfully!")
        print("=" * 50)
        print("\n📝 Login Credentials:")
        print(f"   Username: testuser")
        print(f"   Email: test@inmyhead.dev")
        print(f"   Password: testpassword123")
        print(f"\n🆔 User ID: {user_id}")
        print("\n📂 Collections created:")
        print(f"   - My Documents (default)")
        print(f"   - Work")
        print(f"   - Personal")
        print(f"   - Research")
        print("\n🏷️  Tags created:")
        for tag_data in tags_data:
            print(f"   - {tag_data['name']}")
        print()


if __name__ == "__main__":
    try:
        create_seed_data()
    except Exception as e:
        logger.error(f"❌ Failed to create seed data: {e}")
        print(f"❌ Failed to create seed data: {e}")
        raise
