"""
Pytest Configuration and Fixtures

Shared fixtures for all tests
"""

import asyncio
import os
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import asyncpg

# Import the FastAPI app
from src.main import app


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the entire test session.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """
    Create a database connection pool for tests.
    Uses test database credentials.
    """
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    )
    
    pool = await asyncpg.create_pool(
        db_url,
        min_size=2,
        max_size=10
    )
    
    try:
        yield pool
    finally:
        await pool.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an AsyncClient for making HTTP requests to the API.
    Uses ASGITransport for proper async handling with httpx.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_id() -> str:
    """
    Provide a test user ID.
    """
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def auth_headers(test_user_id: str) -> dict:
    """
    Provide authentication headers for API requests.
    """
    return {
        "Authorization": f"Bearer test_token_{test_user_id}"
    }


@pytest_asyncio.fixture
async def cleanup_collections(db_pool: asyncpg.Pool):
    """
    Fixture to cleanup test collections after each test.
    """
    yield
    
    # Cleanup after test
    async with db_pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM collections 
            WHERE name LIKE 'test_%' OR name LIKE 'Test%'
        """)


@pytest_asyncio.fixture
async def cleanup_documents(db_pool: asyncpg.Pool):
    """
    Fixture to cleanup test documents after each test.
    """
    yield
    
    # Cleanup after test
    async with db_pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM documents 
            WHERE title LIKE 'test_%' OR title LIKE 'Test%'
        """)


@pytest_asyncio.fixture
async def cleanup_conversations(db_pool: asyncpg.Pool):
    """
    Fixture to cleanup test conversations after each test.
    """
    yield
    
    # Cleanup after test
    async with db_pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM conversations 
            WHERE title LIKE 'test_%' OR title LIKE 'Test%'
        """)


@pytest_asyncio.fixture
async def sample_collection(
    db_pool: asyncpg.Pool,
    test_user_id: str
) -> dict:
    """
    Create a sample collection for testing.
    """
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO collections (user_id, name, description)
            VALUES ($1, $2, $3)
            RETURNING id, user_id, name, description, 
                      document_count, created_at, updated_at
        """, test_user_id, "Test Collection", "A test collection")
        
        return dict(row)


@pytest_asyncio.fixture
async def sample_document(
    db_pool: asyncpg.Pool,
    test_user_id: str
) -> dict:
    """
    Create a sample document for testing.
    """
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO documents (
                user_id, title, file_name, file_type, 
                file_size, file_path, status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, user_id, title, file_name, file_type,
                      file_size, file_path, status, created_at, updated_at
        """,
        test_user_id,
        "Test Document",
        "test.pdf",
        "pdf",
        1024,
        "/uploads/test.pdf",
        "completed"
        )
        
        return dict(row)


@pytest.fixture
def mock_openai_response():
    """
    Provide a mock OpenAI API response.
    """
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response from the AI."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }


@pytest.fixture
def mock_embedding():
    """
    Provide a mock embedding vector.
    """
    return [0.1] * 1536  # Standard OpenAI embedding dimension


# Configure pytest markers
def pytest_configure(config):
    """
    Configure custom pytest markers.
    """
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests"
    )
