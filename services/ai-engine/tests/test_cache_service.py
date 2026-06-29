"""
Tests for Redis caching service.

Tests the actual RedisCacheService API:
- cache_query_result / get_query_result
- cache_embedding / get_embedding
- invalidate_document_cache
- get_cache_stats
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json
import numpy as np


@pytest.fixture
def mock_redis():
    """Mock Redis client with all methods used by RedisCacheService."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.ping = AsyncMock(return_value=True)
    mock.info = AsyncMock(return_value={"keyspace_hits": 10, "keyspace_misses": 5})
    mock.scan_iter = MagicMock(return_value=AsyncIteratorMock([]))
    return mock


class AsyncIteratorMock:
    """Helper to mock async iterators like scan_iter."""
    def __init__(self, items):
        self.items = list(items)
    def __aiter__(self):
        return self
    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


@pytest.fixture
def cache_service(mock_redis):
    """Create cache service with mocked Redis client."""
    from src.services.cache_service import RedisCacheService
    service = RedisCacheService()
    service._client = mock_redis
    return service


@pytest.mark.asyncio
async def test_cache_query_result(cache_service, mock_redis):
    """Test caching query results calls setex with correct TTL."""
    result = {"doc_id": "1", "score": 0.9}
    await cache_service.cache_query_result("test query", result)
    mock_redis.setex.assert_called_once()
    args = mock_redis.setex.call_args[0]
    assert args[0].startswith("rag:query:")
    assert args[1] == 1800


@pytest.mark.asyncio
async def test_get_query_result_hit(cache_service, mock_redis):
    """Test cache hit returns deserialized result."""
    expected = {"doc_id": "1", "score": 0.9}
    mock_redis.get.return_value = json.dumps(expected).encode()
    result = await cache_service.get_query_result("test query")
    assert result == expected


@pytest.mark.asyncio
async def test_get_query_result_miss(cache_service, mock_redis):
    """Test cache miss returns None."""
    mock_redis.get.return_value = None
    result = await cache_service.get_query_result("test query")
    assert result is None


@pytest.mark.asyncio
async def test_cache_embedding(cache_service, mock_redis):
    """Test embedding caching uses numpy serialization and 24h TTL."""
    embedding = [0.1] * 384
    await cache_service.cache_embedding("test text", embedding)
    mock_redis.setex.assert_called_once()
    args = mock_redis.setex.call_args[0]
    assert args[0].startswith("rag:embedding:")
    assert args[1] == 86400


@pytest.mark.asyncio
async def test_get_embedding_hit(cache_service, mock_redis):
    """Test embedding cache hit deserializes numpy bytes."""
    embedding = [0.1, 0.2, 0.3]
    mock_redis.get.return_value = np.array(embedding, dtype=np.float32).tobytes()
    result = await cache_service.get_embedding("test text")
    assert result is not None
    assert len(result) == 3
    assert abs(result[0] - 0.1) < 0.001


@pytest.mark.asyncio
async def test_get_embedding_miss(cache_service, mock_redis):
    """Test embedding cache miss returns None."""
    mock_redis.get.return_value = None
    result = await cache_service.get_embedding("test text")
    assert result is None


@pytest.mark.asyncio
async def test_invalidate_document_cache(cache_service, mock_redis):
    """Test document cache invalidation scans and deletes matching keys."""
    mock_redis.scan_iter = MagicMock(
        return_value=AsyncIteratorMock([b"rag:query:abc123", b"rag:query:def456"])
    )
    deleted = await cache_service.invalidate_document_cache("doc123")
    assert deleted == 2
    assert mock_redis.delete.call_count == 2


@pytest.mark.asyncio
async def test_invalidate_document_cache_no_keys(cache_service, mock_redis):
    """Test invalidation with no matching keys returns 0."""
    mock_redis.scan_iter = MagicMock(return_value=AsyncIteratorMock([]))
    deleted = await cache_service.invalidate_document_cache("doc123")
    assert deleted == 0


@pytest.mark.asyncio
async def test_cache_query_with_collection_id(cache_service, mock_redis):
    """Test that collection_id changes the cache key."""
    result = {"score": 0.9}
    await cache_service.cache_query_result("query", result, collection_id="col1")
    call1_key = mock_redis.setex.call_args[0][0]
    mock_redis.setex.reset_mock()
    await cache_service.cache_query_result("query", result, collection_id="col2")
    call2_key = mock_redis.setex.call_args[0][0]
    assert call1_key != call2_key


@pytest.mark.asyncio
async def test_cache_query_custom_ttl(cache_service, mock_redis):
    """Test custom TTL overrides default."""
    await cache_service.cache_query_result("query", {"x": 1}, ttl=60)
    args = mock_redis.setex.call_args[0]
    assert args[1] == 60


@pytest.mark.asyncio
async def test_hash_text_deterministic(cache_service):
    """Test that hash_text produces consistent results."""
    from src.services.cache_service import RedisCacheService
    h1 = RedisCacheService.hash_text("hello")
    h2 = RedisCacheService.hash_text("hello")
    h3 = RedisCacheService.hash_text("world")
    assert h1 == h2
    assert h1 != h3


@pytest.mark.asyncio
async def test_hash_query_with_collection(cache_service):
    """Test hash_query includes collection_id when provided."""
    from src.services.cache_service import RedisCacheService
    h1 = RedisCacheService.hash_query("query")
    h2 = RedisCacheService.hash_query("query", "col1")
    assert h1 != h2


@pytest.mark.asyncio
async def test_cache_query_result_handles_error(cache_service, mock_redis):
    """Test graceful error handling on cache write failure."""
    mock_redis.setex.side_effect = Exception("connection refused")
    result = await cache_service.cache_query_result("query", {"x": 1})
    assert result is False


@pytest.mark.asyncio
async def test_get_query_result_handles_error(cache_service, mock_redis):
    """Test graceful error handling on cache read failure."""
    mock_redis.get.side_effect = Exception("connection refused")
    result = await cache_service.get_query_result("query")
    assert result is None


@pytest.mark.asyncio
async def test_concurrent_cache_operations(cache_service, mock_redis):
    """Test concurrent cache operations complete without errors."""
    tasks = [
        cache_service.get_query_result(f"query_{i}")
        for i in range(10)
    ]
    results = await asyncio.gather(*tasks)
    assert len(results) == 10
    assert all(r is None for r in results)


@pytest.mark.asyncio
async def test_calculate_hit_rate():
    """Test hit rate calculation."""
    from src.services.cache_service import RedisCacheService
    assert RedisCacheService._calculate_hit_rate(0, 0) == 0.0
    assert RedisCacheService._calculate_hit_rate(10, 0) == 100.0
    assert RedisCacheService._calculate_hit_rate(1, 1) == 50.0
    assert abs(RedisCacheService._calculate_hit_rate(2, 1) - 66.666) < 1
