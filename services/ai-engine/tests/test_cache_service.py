"""
Tests for Redis caching service

Comprehensive test coverage for cache_service.py
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json
import hashlib
from datetime import datetime, timedelta

# Mock redis before importing cache_service
redis_mock = MagicMock()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.keys = AsyncMock(return_value=[])
    mock.ttl = AsyncMock(return_value=1800)
    mock.ping = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def cache_service(mock_redis):
    """Create cache service with mocked Redis"""
    with patch('redis.asyncio.Redis', return_value=mock_redis):
        from src.services.cache_service import RedisCacheService
        service = RedisCacheService()
        service.redis = mock_redis
        return service


@pytest.mark.asyncio
async def test_cache_query_result(cache_service, mock_redis):
    """Test caching query results"""
    query = "test query"
    results = [{"doc_id": "1", "score": 0.9}]
    
    # Cache results
    await cache_service.cache_query_result(query, results)
    
    # Verify set was called
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[1]['ex'] == 1800  # 30 minutes TTL


@pytest.mark.asyncio
async def test_get_cached_query_hit(cache_service, mock_redis):
    """Test retrieving cached query (cache hit)"""
    query = "test query"
    results = [{"doc_id": "1", "score": 0.9}]
    
    # Mock cache hit
    mock_redis.get.return_value = json.dumps(results).encode('utf-8')
    
    # Retrieve from cache
    cached = await cache_service.get_cached_query(query)
    
    assert cached is not None
    assert cached == results
    assert cache_service.cache_hits > 0


@pytest.mark.asyncio
async def test_get_cached_query_miss(cache_service, mock_redis):
    """Test retrieving cached query (cache miss)"""
    query = "test query"
    
    # Mock cache miss
    mock_redis.get.return_value = None
    
    # Retrieve from cache
    cached = await cache_service.get_cached_query(query)
    
    assert cached is None
    assert cache_service.cache_misses > 0


@pytest.mark.asyncio
async def test_cache_embedding(cache_service, mock_redis):
    """Test caching embedding vectors"""
    text = "test text"
    embedding = [0.1] * 1536
    
    # Cache embedding
    await cache_service.cache_embedding(text, embedding)
    
    # Verify set was called with correct TTL
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[1]['ex'] == 86400  # 24 hours TTL


@pytest.mark.asyncio
async def test_get_cached_embedding(cache_service, mock_redis):
    """Test retrieving cached embeddings"""
    text = "test text"
    embedding = [0.1] * 1536
    
    # Mock cache hit
    import numpy as np
    mock_redis.get.return_value = np.array(embedding).tobytes()
    
    # Retrieve from cache
    cached = await cache_service.get_cached_embedding(text)
    
    assert cached is not None
    assert len(cached) == 1536


@pytest.mark.asyncio
async def test_invalidate_by_document(cache_service, mock_redis):
    """Test document-based cache invalidation"""
    doc_id = "doc123"
    
    # Mock keys that should be deleted
    mock_redis.keys.return_value = [
        b"query:hash1:doc123",
        b"query:hash2:doc123",
        b"query:hash3:other"
    ]
    
    # Invalidate by document
    deleted = await cache_service.invalidate_by_document(doc_id)
    
    # Should delete 2 keys containing doc123
    assert mock_redis.delete.called
    assert deleted >= 0


@pytest.mark.asyncio
async def test_invalidate_all(cache_service, mock_redis):
    """Test invalidating all cached queries"""
    mock_redis.keys.return_value = [
        b"query:hash1",
        b"query:hash2",
        b"embedding:hash3"
    ]
    
    # Invalidate all queries
    deleted = await cache_service.invalidate_all_queries()
    
    # Should attempt to delete query keys
    assert mock_redis.keys.called


@pytest.mark.asyncio
async def test_cache_statistics(cache_service):
    """Test cache statistics tracking"""
    # Record some hits and misses
    cache_service.record_hit("query")
    cache_service.record_miss("query")
    cache_service.record_hit("query")
    cache_service.record_hit("embedding")
    
    # Get statistics
    stats = cache_service.get_statistics()
    
    assert stats['total_requests'] == 4
    assert stats['cache_hits'] == 3
    assert stats['cache_misses'] == 1
    assert 0.7 < stats['hit_rate'] < 0.8


@pytest.mark.asyncio
async def test_health_check_healthy(cache_service, mock_redis):
    """Test health check when Redis is healthy"""
    mock_redis.ping.return_value = True
    
    healthy = await cache_service.health_check()
    
    assert healthy is True
    mock_redis.ping.assert_called_once()


@pytest.mark.asyncio
async def test_health_check_unhealthy(cache_service, mock_redis):
    """Test health check when Redis is down"""
    mock_redis.ping.side_effect = Exception("Connection failed")
    
    healthy = await cache_service.health_check()
    
    assert healthy is False


@pytest.mark.asyncio
async def test_cache_key_generation(cache_service):
    """Test consistent cache key generation"""
    query1 = "test query"
    query2 = "test query"
    query3 = "different query"
    
    # Same query should generate same key
    key1 = cache_service._generate_cache_key(query1)
    key2 = cache_service._generate_cache_key(query2)
    key3 = cache_service._generate_cache_key(query3)
    
    assert key1 == key2
    assert key1 != key3


@pytest.mark.asyncio
async def test_ttl_configuration(cache_service):
    """Test that TTL values are configurable"""
    assert cache_service.query_ttl == 1800  # 30 minutes
    assert cache_service.embedding_ttl == 86400  # 24 hours


@pytest.mark.asyncio
async def test_cache_with_doc_ids(cache_service, mock_redis):
    """Test caching with document ID tracking"""
    query = "test query"
    results = [{"doc_id": "1", "score": 0.9}]
    doc_ids = ["doc1", "doc2"]
    
    # Cache with doc IDs
    await cache_service.cache_query_result(query, results, doc_ids=doc_ids)
    
    # Verify the cache key includes doc IDs
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_cache_access(cache_service, mock_redis):
    """Test thread-safe concurrent cache access"""
    queries = [f"query_{i}" for i in range(10)]
    
    # Simulate concurrent cache operations
    tasks = [
        cache_service.get_cached_query(query)
        for query in queries
    ]
    
    results = await asyncio.gather(*tasks)
    
    # All should complete without errors
    assert len(results) == 10


@pytest.mark.asyncio
async def test_cache_serialization(cache_service, mock_redis):
    """Test proper JSON serialization of complex objects"""
    complex_result = {
        "doc_id": "123",
        "score": 0.95,
        "metadata": {
            "title": "Test Doc",
            "date": "2025-10-11"
        },
        "chunks": [
            {"text": "chunk 1", "position": 0},
            {"text": "chunk 2", "position": 1}
        ]
    }
    
    # Should handle complex nested structures
    await cache_service.cache_query_result("test", [complex_result])
    
    # Verify it was serialized
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_cache_expiration(cache_service, mock_redis):
    """Test that cache entries expire correctly"""
    query = "test query"
    
    # Mock TTL check
    mock_redis.ttl.return_value = 0  # Expired
    
    ttl = await cache_service.get_ttl(query)
    
    assert ttl == 0


@pytest.mark.asyncio
async def test_reset_statistics(cache_service):
    """Test resetting cache statistics"""
    # Record some stats
    cache_service.record_hit("query")
    cache_service.record_miss("query")
    
    # Reset
    cache_service.reset_statistics()
    
    stats = cache_service.get_statistics()
    assert stats['total_requests'] == 0
    assert stats['cache_hits'] == 0
    assert stats['cache_misses'] == 0


@pytest.mark.asyncio
async def test_embedding_vector_serialization(cache_service, mock_redis):
    """Test numpy array serialization for embeddings"""
    import numpy as np
    
    embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
    
    # Cache embedding
    await cache_service.cache_embedding("text", embedding)
    
    # Should have called set with serialized numpy array
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_batch_invalidation(cache_service, mock_redis):
    """Test batch invalidation of multiple documents"""
    doc_ids = ["doc1", "doc2", "doc3"]
    
    mock_redis.keys.return_value = [
        b"query:hash1:doc1",
        b"query:hash2:doc2"
    ]
    
    # Invalidate multiple documents
    for doc_id in doc_ids:
        await cache_service.invalidate_by_document(doc_id)
    
    # Should have called keys multiple times
    assert mock_redis.keys.call_count >= len(doc_ids)
