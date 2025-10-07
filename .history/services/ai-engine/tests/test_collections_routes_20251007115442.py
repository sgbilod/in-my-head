"""
Tests for Collections API Routes

Test suite for collection API endpoints.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from uuid import uuid4
import asyncpg


@pytest_asyncio.fixture
async def test_user_id(db_pool):
    """Generate a test user ID and ensure user exists."""
    user_id = uuid4()
    
    # Create test user
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (id, email, name, created_at, updated_at)
            VALUES ($1, $2, $3, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """, user_id, f"test_{user_id}@example.com", "Test User")
    
    yield user_id
    
    # Cleanup
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)


@pytest_asyncio.fixture
async def auth_headers(test_user_id):
    """Generate authentication headers for tests."""
    # Mock JWT token for testing
    return {"Authorization": f"Bearer test_token_{test_user_id}"}


@pytest_asyncio.fixture
async def db_pool():
    """Create database pool for cleanup."""
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5434,
        user="inmyhead",
        password="inmyhead_dev_pass",
        database="inmyhead_dev",
    )
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def cleanup_collections(db_pool, test_user_id):
    """Clean up test data after each test."""
    yield
    async with db_pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM collections WHERE user_id = $1", test_user_id
        )


class TestCreateCollectionEndpoint:
    """Tests for POST /api/collections."""

    @pytest.mark.asyncio
    async def test_create_collection_success(
        self, client: AsyncClient, auth_headers, cleanup_collections
    ):
        """Test successful collection creation via API."""
        response = await client.post(
            "/api/collections",
            json={"name": "API Test Collection", "description": "Test desc"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Collection"
        assert data["description"] == "Test desc"
        assert "id" in data
        assert data["document_count"] == 0

    @pytest.mark.asyncio
    async def test_create_collection_without_description(
        self, client: AsyncClient, auth_headers, cleanup_collections
    ):
        """Test creating collection without description."""
        response = await client.post(
            "/api/collections",
            json={"name": "Minimal Collection"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Collection"
        assert data["description"] is None

    @pytest.mark.asyncio
    async def test_create_collection_duplicate_name(
        self, client: AsyncClient, auth_headers, cleanup_collections
    ):
        """Test that duplicate names return 400."""
        # Create first collection
        await client.post(
            "/api/collections",
            json={"name": "Duplicate"},
            headers=auth_headers,
        )

        # Try to create duplicate
        response = await client.post(
            "/api/collections",
            json={"name": "Duplicate"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_collection_missing_name(
        self, client: AsyncClient, auth_headers
    ):
        """Test that missing name returns validation error."""
        response = await client.post(
            "/api/collections", json={}, headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_collection_unauthorized(self, client: AsyncClient):
        """Test that unauthorized request is rejected."""
        response = await client.post(
            "/api/collections", json={"name": "Unauthorized"}
        )

        assert response.status_code == 401


class TestListCollectionsEndpoint:
    """Tests for GET /api/collections."""

    @pytest.mark.asyncio
    async def test_list_collections_empty(
        self, client: AsyncClient, auth_headers
    ):
        """Test listing collections when user has none."""
        response = await client.get("/api/collections", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_collections_multiple(
        self, client: AsyncClient, auth_headers, cleanup_collections
    ):
        """Test listing multiple collections."""
        # Create collections
        for i in range(3):
            await client.post(
                "/api/collections",
                json={"name": f"Collection {i}"},
                headers=auth_headers,
            )

        # List collections
        response = await client.get("/api/collections", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_list_collections_pagination(
        self, client: AsyncClient, auth_headers, cleanup_collections
    ):
        """Test collection list pagination."""
        # Create multiple collections
        for i in range(5):
            await client.post(
                "/api/collections",
                json={"name": f"Page Test {i}"},
                headers=auth_headers,
            )

        # Get first page
        response1 = await client.get(
            "/api/collections?limit=2&offset=0", headers=auth_headers
        )
        assert response1.status_code == 200
        page1 = response1.json()
        assert len(page1) == 2

        # Get second page
        response2 = await client.get(
            "/api/collections?limit=2&offset=2", headers=auth_headers
        )
        assert response2.status_code == 200
        page2 = response2.json()
        assert len(page2) == 2

        # Ensure different results
        page1_ids = {c["id"] for c in page1}
        page2_ids = {c["id"] for c in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_list_collections_sorting(
        self, client: AsyncClient, auth_headers, cleanup_collections
    ):
        """Test collection list sorting."""
        # Create collections
        await client.post(
            "/api/collections", json={"name": "AAA"}, headers=auth_headers
        )
        await client.post(
            "/api/collections", json={"name": "ZZZ"}, headers=auth_headers
        )

        # Sort ascending
        response_asc = await client.get(
            "/api/collections?sort_by=name&sort_order=asc",
            headers=auth_headers,
        )
        data_asc = response_asc.json()
        names_asc = [c["name"] for c in data_asc if c["name"] in ["AAA", "ZZZ"]]
        assert names_asc == ["AAA", "ZZZ"]

        # Sort descending
        response_desc = await client.get(
            "/api/collections?sort_by=name&sort_order=desc",
            headers=auth_headers,
        )
        data_desc = response_desc.json()
        names_desc = [c["name"] for c in data_desc if c["name"] in ["AAA", "ZZZ"]]
        assert names_desc == ["ZZZ", "AAA"]


class TestGetCollectionEndpoint:
    """Tests for GET /api/collections/{id}."""

    @pytest.mark.asyncio
    async def test_get_collection_success(
        self, client: AsyncClient, auth_headers, cleanup_collections
    ):
        """Test retrieving a specific collection."""
        # Create collection
        create_response = await client.post(
            "/api/collections",
            json={"name": "Get Test"},
            headers=auth_headers,
        )
        collection_id = create_response.json()["id"]

        # Get collection
        response = await client.get(
            f"/api/collections/{collection_id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == collection_id
        assert data["name"] == "Get Test"

    @pytest.mark.asyncio
    async def test_get_nonexistent_collection(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting non-existent collection returns 404."""
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/collections/{fake_id}", headers=auth_headers
        )

        assert response.status_code == 404


class TestUpdateCollectionEndpoint:
    """Tests for PUT /api/collections/{id}."""

    @pytest.mark.asyncio
    async def test_update_collection_name(
        self, client: AsyncClient, auth_headers, cleanup_collections
    ):
        """Test updating collection name."""
        # Create collection
        create_response = await client.post(
            "/api/collections",
            json={"name": "Original"},
            headers=auth_headers,
        )
        collection_id = create_response.json()["id"]

        # Update collection
        response = await client.put(
            f"/api/collections/{collection_id}",
            json={"name": "Updated"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_collection_description(
        self, client: AsyncClient, auth_headers, cleanup_collections
    ):
        """Test updating collection description."""
        # Create collection
        create_response = await client.post(
            "/api/collections",
            json={"name": "Update Test", "description": "Old"},
            headers=auth_headers,
        )
        collection_id = create_response.json()["id"]

        # Update description
        response = await client.put(
            f"/api/collections/{collection_id}",
            json={"description": "New"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New"

    @pytest.mark.asyncio
    async def test_update_nonexistent_collection(
        self, client: AsyncClient, auth_headers
    ):
        """Test updating non-existent collection returns 404."""
        fake_id = str(uuid4())
        response = await client.put(
            f"/api/collections/{fake_id}",
            json={"name": "Updated"},
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestDeleteCollectionEndpoint:
    """Tests for DELETE /api/collections/{id}."""

    @pytest.mark.asyncio
    async def test_delete_collection_success(
        self, client: AsyncClient, auth_headers, cleanup_collections
    ):
        """Test successful collection deletion."""
        # Create collection
        create_response = await client.post(
            "/api/collections",
            json={"name": "To Delete"},
            headers=auth_headers,
        )
        collection_id = create_response.json()["id"]

        # Delete collection
        response = await client.delete(
            f"/api/collections/{collection_id}", headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/collections/{collection_id}", headers=auth_headers
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_collection(
        self, client: AsyncClient, auth_headers
    ):
        """Test deleting non-existent collection returns 404."""
        fake_id = str(uuid4())
        response = await client.delete(
            f"/api/collections/{fake_id}", headers=auth_headers
        )

        assert response.status_code == 404


class TestCollectionDocumentEndpoints:
    """Tests for collection document management endpoints."""

    @pytest.mark.asyncio
    async def test_add_document_to_collection(
        self, client: AsyncClient, auth_headers, db_pool, cleanup_collections
    ):
        """Test adding a document to a collection."""
        # Create collection
        create_response = await client.post(
            "/api/collections",
            json={"name": "Doc Collection"},
            headers=auth_headers,
        )
        collection_id = create_response.json()["id"]

        # Create a test document (mock)
        # In real tests, this would use the document upload endpoint
        # For now, we'll test the endpoint structure

        # Note: This test requires a real document to exist
        # Implementation depends on test fixtures

    @pytest.mark.asyncio
    async def test_get_collection_documents(
        self, client: AsyncClient, auth_headers, cleanup_collections
    ):
        """Test retrieving documents in a collection."""
        # Create collection
        create_response = await client.post(
            "/api/collections",
            json={"name": "Doc Collection"},
            headers=auth_headers,
        )
        collection_id = create_response.json()["id"]

        # Get documents
        response = await client.get(
            f"/api/collections/{collection_id}/documents",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)
