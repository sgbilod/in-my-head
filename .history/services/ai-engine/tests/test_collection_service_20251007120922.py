"""
Tests for CollectionService

Test suite for collection management functionality.
"""

import pytest
import pytest_asyncio
import asyncpg
from uuid import uuid4
from datetime import datetime

from src.services.collection_service import CollectionService


@pytest_asyncio.fixture
async def db_pool():
    """Create a test database connection pool."""
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5434,
        user="inmyhead",
        password="inmyhead_dev_pass",
        database="inmyhead_dev",
        min_size=1,
        max_size=5,
    )
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def collection_service(db_pool):
    """Create a CollectionService instance."""
    return CollectionService(db_pool)


@pytest_asyncio.fixture
async def test_user_id(db_pool):
    """Generate a test user ID and ensure user exists in database."""
    user_id = uuid4()
    
    # Create test user in database
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (id, email, username, full_name, 
                             password_hash, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """, user_id, f"test_{user_id}@example.com", 
             f"testuser_{user_id}", "Test User", "hashed_password")
    
    yield user_id
    
    # Cleanup test user after test
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)


@pytest_asyncio.fixture
async def cleanup_collections(db_pool, test_user_id):
    """Clean up test collections after each test."""
    yield
    async with db_pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM collections WHERE user_id = $1", test_user_id
        )


class TestCollectionCreation:
    """Tests for creating collections."""

    @pytest.mark.asyncio
    async def test_create_collection_success(
        self, collection_service, test_user_id, cleanup_collections
    ):
        """Test successful collection creation."""
        result = await collection_service.create_collection(
            user_id=test_user_id, name="Test Collection", description="A test"
        )

        assert result["name"] == "Test Collection"
        assert result["description"] == "A test"
        assert result["user_id"] == test_user_id
        assert result["document_count"] == 0
        assert "id" in result
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_create_collection_without_description(
        self, collection_service, test_user_id, cleanup_collections
    ):
        """Test creating collection without description."""
        result = await collection_service.create_collection(
            user_id=test_user_id, name="Minimal Collection"
        )

        assert result["name"] == "Minimal Collection"
        assert result["description"] is None
        assert result["document_count"] == 0

    @pytest.mark.asyncio
    async def test_create_duplicate_collection_name(
        self, collection_service, test_user_id, cleanup_collections
    ):
        """Test that duplicate collection names are rejected."""
        # Create first collection
        await collection_service.create_collection(
            user_id=test_user_id, name="Duplicate Test"
        )

        # Attempt to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            await collection_service.create_collection(
                user_id=test_user_id, name="Duplicate Test"
            )

    @pytest.mark.asyncio
    async def test_different_users_same_collection_name(
        self, collection_service, db_pool, cleanup_collections
    ):
        """Test that different users can have collections with same name."""
        user1_id = uuid4()
        user2_id = uuid4()
        
        # Create test users
        async with db_pool.acquire() as conn:
            for user_id in [user1_id, user2_id]:
                await conn.execute("""
                    INSERT INTO users (id, email, username, full_name,
                                     password_hash, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                """, user_id, f"test_{user_id}@example.com",
                     f"testuser_{user_id}", "Test User", "hashed_password")

        # Create collections for both users
        result1 = await collection_service.create_collection(
            user_id=user1_id, name="Shared Name"
        )
        result2 = await collection_service.create_collection(
            user_id=user2_id, name="Shared Name"
        )

        assert result1["name"] == result2["name"]
        assert result1["user_id"] != result2["user_id"]
        
        # Cleanup
        async with db_pool.acquire() as conn:
            for user_id in [user1_id, user2_id]:
                await conn.execute("DELETE FROM collections WHERE user_id = $1", user_id)
                await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        assert result1["id"] != result2["id"]

        # Cleanup
        await collection_service.delete_collection(result1["id"], user1_id)
        await collection_service.delete_collection(result2["id"], user2_id)


class TestCollectionRetrieval:
    """Tests for retrieving collections."""

    @pytest.mark.asyncio
    async def test_get_collection_by_id(
        self, collection_service, test_user_id, cleanup_collections
    ):
        """Test retrieving a collection by ID."""
        # Create collection
        created = await collection_service.create_collection(
            user_id=test_user_id, name="Get Test"
        )

        # Retrieve collection
        result = await collection_service.get_collection(
            created["id"], test_user_id
        )

        assert result is not None
        assert result["id"] == created["id"]
        assert result["name"] == "Get Test"

    @pytest.mark.asyncio
    async def test_get_nonexistent_collection(
        self, collection_service, test_user_id
    ):
        """Test retrieving non-existent collection returns None."""
        result = await collection_service.get_collection(uuid4(), test_user_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_collection_wrong_user(
        self, collection_service, db_pool
    ):
        """Test that users can't access other users' collections."""
        user1_id = uuid4()
        user2_id = uuid4()
        
        # Create test users
        async with db_pool.acquire() as conn:
            for user_id in [user1_id, user2_id]:
                await conn.execute(
                    """
                    INSERT INTO users (id, email, username, full_name,
                                     password_hash, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                """,
                    user_id,
                    f"test_{user_id}@example.com",
                    f"testuser_{user_id}",
                    "Test User",
                    "hashed_password"
                )

        # Create collection for user1
        created = await collection_service.create_collection(
            user_id=user1_id, name="Private Collection"
        )

        # Try to access with user2
        result = await collection_service.get_collection(
            created["id"], user2_id
        )
        assert result is None

        # Cleanup
        await collection_service.delete_collection(created["id"], user1_id)
        async with db_pool.acquire() as conn:
            for user_id in [user1_id, user2_id]:
                await conn.execute("DELETE FROM users WHERE id = $1", user_id)

    @pytest.mark.asyncio
    async def test_list_collections_empty(
        self, collection_service, test_user_id
    ):
        """Test listing collections for user with no collections."""
        result = await collection_service.list_collections(test_user_id)
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_collections_multiple(
        self, collection_service, test_user_id, cleanup_collections
    ):
        """Test listing multiple collections."""
        # Create multiple collections
        await collection_service.create_collection(
            user_id=test_user_id, name="Collection 1"
        )
        await collection_service.create_collection(
            user_id=test_user_id, name="Collection 2"
        )
        await collection_service.create_collection(
            user_id=test_user_id, name="Collection 3"
        )

        # List collections
        result = await collection_service.list_collections(test_user_id)

        assert len(result) == 3
        names = [c["name"] for c in result]
        assert "Collection 1" in names
        assert "Collection 2" in names
        assert "Collection 3" in names

    @pytest.mark.asyncio
    async def test_list_collections_pagination(
        self, collection_service, test_user_id, cleanup_collections
    ):
        """Test collection listing with pagination."""
        # Create 5 collections
        for i in range(5):
            await collection_service.create_collection(
                user_id=test_user_id, name=f"Collection {i}"
            )

        # Get first page
        page1 = await collection_service.list_collections(
            test_user_id, limit=2, offset=0
        )
        assert len(page1) == 2

        # Get second page
        page2 = await collection_service.list_collections(
            test_user_id, limit=2, offset=2
        )
        assert len(page2) == 2

        # Ensure different results
        page1_ids = {c["id"] for c in page1}
        page2_ids = {c["id"] for c in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_list_collections_sorting(
        self, collection_service, test_user_id, cleanup_collections
    ):
        """Test collection listing with different sort orders."""
        # Create collections with delays to ensure different timestamps
        import asyncio

        await collection_service.create_collection(
            user_id=test_user_id, name="AAA"
        )
        await asyncio.sleep(0.1)
        await collection_service.create_collection(
            user_id=test_user_id, name="ZZZ"
        )

        # Sort by name ascending
        result_name_asc = await collection_service.list_collections(
            test_user_id, sort_by="name", sort_order="asc"
        )
        assert result_name_asc[0]["name"] == "AAA"
        assert result_name_asc[1]["name"] == "ZZZ"

        # Sort by name descending
        result_name_desc = await collection_service.list_collections(
            test_user_id, sort_by="name", sort_order="desc"
        )
        assert result_name_desc[0]["name"] == "ZZZ"
        assert result_name_desc[1]["name"] == "AAA"


class TestCollectionUpdate:
    """Tests for updating collections."""

    @pytest.mark.asyncio
    async def test_update_collection_name(
        self, collection_service, test_user_id, cleanup_collections
    ):
        """Test updating collection name."""
        # Create collection
        created = await collection_service.create_collection(
            user_id=test_user_id, name="Original Name"
        )

        # Update name
        updated = await collection_service.update_collection(
            collection_id=created["id"],
            user_id=test_user_id,
            name="Updated Name",
        )

        assert updated["name"] == "Updated Name"
        assert updated["id"] == created["id"]

    @pytest.mark.asyncio
    async def test_update_collection_description(
        self, collection_service, test_user_id, cleanup_collections
    ):
        """Test updating collection description."""
        created = await collection_service.create_collection(
            user_id=test_user_id, name="Test", description="Old description"
        )

        updated = await collection_service.update_collection(
            collection_id=created["id"],
            user_id=test_user_id,
            description="New description",
        )

        assert updated["description"] == "New description"
        assert updated["name"] == "Test"  # Name unchanged

    @pytest.mark.asyncio
    async def test_update_nonexistent_collection(
        self, collection_service, test_user_id
    ):
        """Test updating non-existent collection returns None."""
        result = await collection_service.update_collection(
            collection_id=uuid4(), user_id=test_user_id, name="New Name"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_update_collection_wrong_user(
        self, collection_service, db_pool
    ):
        """Test that users can't update other users' collections."""
        user1_id = uuid4()
        user2_id = uuid4()
        
        # Create test users
        async with db_pool.acquire() as conn:
            for user_id in [user1_id, user2_id]:
                await conn.execute(
                    """
                    INSERT INTO users (id, email, username, full_name,
                                     password_hash, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                """,
                    user_id,
                    f"test_{user_id}@example.com",
                    f"testuser_{user_id}",
                    "Test User",
                    "hashed_password"
                )

        # Create collection for user1
        created = await collection_service.create_collection(
            user_id=user1_id, name="User1 Collection"
        )

        # Try to update with user2
        result = await collection_service.update_collection(
            collection_id=created["id"], user_id=user2_id, name="Hacked"
        )
        assert result is None

        # Cleanup
        await collection_service.delete_collection(created["id"], user1_id)
        async with db_pool.acquire() as conn:
            for user_id in [user1_id, user2_id]:
                await conn.execute("DELETE FROM users WHERE id = $1", user_id)


class TestCollectionDeletion:
    """Tests for deleting collections."""

    @pytest.mark.asyncio
    async def test_delete_collection_success(
        self, collection_service, test_user_id, cleanup_collections
    ):
        """Test successful collection deletion."""
        created = await collection_service.create_collection(
            user_id=test_user_id, name="To Delete"
        )

        # Delete collection
        deleted = await collection_service.delete_collection(
            created["id"], test_user_id
        )
        assert deleted is True

        # Verify deletion
        result = await collection_service.get_collection(
            created["id"], test_user_id
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_collection(
        self, collection_service, test_user_id
    ):
        """Test deleting non-existent collection returns False."""
        deleted = await collection_service.delete_collection(
            uuid4(), test_user_id
        )
        assert deleted is False

    @pytest.mark.asyncio
    async def test_delete_collection_wrong_user(
        self, collection_service, db_pool
    ):
        """Test that users can't delete other users' collections."""
        user1_id = uuid4()
        user2_id = uuid4()
        
        # Create test users
        async with db_pool.acquire() as conn:
            for user_id in [user1_id, user2_id]:
                await conn.execute(
                    """
                    INSERT INTO users (id, email, username, full_name,
                                     password_hash, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                """,
                    user_id,
                    f"test_{user_id}@example.com",
                    f"testuser_{user_id}",
                    "Test User",
                    "hashed_password"
                )

        # Create collection for user1
        created = await collection_service.create_collection(
            user_id=user1_id, name="Protected Collection"
        )

        # Try to delete with user2
        deleted = await collection_service.delete_collection(
            created["id"], user2_id
        )
        assert deleted is False

        # Cleanup
        await collection_service.delete_collection(created["id"], user1_id)
        async with db_pool.acquire() as conn:
            for user_id in [user1_id, user2_id]:
                await conn.execute("DELETE FROM users WHERE id = $1", user_id)


class TestDocumentCollectionOperations:
    """Tests for adding/removing documents to/from collections."""

    @pytest.mark.asyncio
    async def test_add_document_to_collection(
        self, collection_service, test_user_id, db_pool, cleanup_collections
    ):
        """Test adding a document to a collection."""
        # Create collection
        collection = await collection_service.create_collection(
            user_id=test_user_id, name="Doc Collection"
        )

        # Create a test document
        async with db_pool.acquire() as conn:
            doc = await conn.fetchrow(
                """
                INSERT INTO documents (user_id, file_name, file_type, status)
                VALUES ($1, 'test.pdf', 'pdf', 'completed')
                RETURNING id
                """,
                test_user_id,
            )
            doc_id = doc["id"]

        # Add document to collection
        result = await collection_service.add_document_to_collection(
            collection["id"], doc_id, test_user_id
        )
        assert result is True

        # Verify document has collection_id
        async with db_pool.acquire() as conn:
            doc_check = await conn.fetchrow(
                "SELECT collection_id FROM documents WHERE id = $1", doc_id
            )
            assert doc_check["collection_id"] == collection["id"]

        # Cleanup
        async with db_pool.acquire() as conn:
            await conn.execute("DELETE FROM documents WHERE id = $1", doc_id)

    @pytest.mark.asyncio
    async def test_remove_document_from_collection(
        self, collection_service, test_user_id, db_pool, cleanup_collections
    ):
        """Test removing a document from a collection."""
        # Create collection
        collection = await collection_service.create_collection(
            user_id=test_user_id, name="Doc Collection"
        )

        # Create and add document
        async with db_pool.acquire() as conn:
            doc = await conn.fetchrow(
                """
                INSERT INTO documents 
                (user_id, file_name, file_type, status, collection_id)
                VALUES ($1, 'test.pdf', 'pdf', 'completed', $2)
                RETURNING id
                """,
                test_user_id,
                collection["id"],
            )
            doc_id = doc["id"]

        # Remove document from collection
        result = await collection_service.remove_document_from_collection(
            doc_id, test_user_id
        )
        assert result is True

        # Verify collection_id is NULL
        async with db_pool.acquire() as conn:
            doc_check = await conn.fetchrow(
                "SELECT collection_id FROM documents WHERE id = $1", doc_id
            )
            assert doc_check["collection_id"] is None

        # Cleanup
        async with db_pool.acquire() as conn:
            await conn.execute("DELETE FROM documents WHERE id = $1", doc_id)

    @pytest.mark.asyncio
    async def test_get_collection_documents(
        self, collection_service, test_user_id, db_pool, cleanup_collections
    ):
        """Test retrieving all documents in a collection."""
        # Create collection
        collection = await collection_service.create_collection(
            user_id=test_user_id, name="Doc Collection"
        )

        # Create multiple documents in collection
        doc_ids = []
        async with db_pool.acquire() as conn:
            for i in range(3):
                doc = await conn.fetchrow(
                    """
                    INSERT INTO documents 
                    (user_id, file_name, file_type, status, collection_id)
                    VALUES ($1, $2, 'pdf', 'completed', $3)
                    RETURNING id
                    """,
                    test_user_id,
                    f"test{i}.pdf",
                    collection["id"],
                )
                doc_ids.append(doc["id"])

        # Get collection documents
        docs = await collection_service.get_collection_documents(
            collection["id"], test_user_id
        )

        assert len(docs) == 3
        retrieved_ids = {doc["id"] for doc in docs}
        assert retrieved_ids == set(doc_ids)

        # Cleanup
        async with db_pool.acquire() as conn:
            for doc_id in doc_ids:
                await conn.execute("DELETE FROM documents WHERE id = $1", doc_id)
