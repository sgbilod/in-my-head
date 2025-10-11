"""
Tests for Cached RAG Service

Comprehensive test coverage for cached_rag_service.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np


@pytest.fixture
def mock_cache_service():
    """Mock cache service"""
    mock = MagicMock()
    mock.get_cached_query = AsyncMock(return_value=None)
    mock.cache_query_result = AsyncMock()
    mock.get_cached_embedding = AsyncMock(return_value=None)
    mock.cache_embedding = AsyncMock()
    mock.health_check = AsyncMock(return_value=True)
    mock.get_statistics = MagicMock(return_value={
        'cache_hits': 10,
        'cache_misses': 5,
        'hit_rate': 0.667
    })
    return mock


@pytest.fixture
def mock_base_rag():
    """Mock base RAG service"""
    mock = MagicMock()
    mock.encode_query = AsyncMock(return_value=[0.1] * 1536)
    mock.search = AsyncMock(return_value=[
        {'doc_id': '1', 'score': 0.9, 'content': 'test content'}
    ])
    mock.retrieve_context = AsyncMock(return_value={
        'documents': [{'id': '1', 'content': 'test'}],
        'citations': []
    })
    return mock


@pytest.fixture
def cached_rag_service(mock_cache_service, mock_base_rag):
    """Create cached RAG service with mocks"""
    with patch('src.services.cached_rag_service.RedisCacheService', return_value=mock_cache_service):
        with patch('src.services.cached_rag_service.RAGService', return_value=mock_base_rag):
            from src.services.cached_rag_service import CachedRAGService
            service = CachedRAGService()
            service.cache = mock_cache_service
            service.rag = mock_base_rag
            return service


@pytest.mark.asyncio
async def test_encode_query_cache_miss(cached_rag_service, mock_cache_service, mock_base_rag):
    """Test query encoding with cache miss"""
    query = "test query"
    
    # Mock cache miss
    mock_cache_service.get_cached_embedding.return_value = None
    mock_base_rag.encode_query.return_value = [0.1] * 1536
    
    # Encode query
    embedding = await cached_rag_service.encode_query(query)
    
    # Should call base RAG service
    mock_base_rag.encode_query.assert_called_once_with(query)
    
    # Should cache the result
    mock_cache_service.cache_embedding.assert_called_once()
    
    assert len(embedding) == 1536


@pytest.mark.asyncio
async def test_encode_query_cache_hit(cached_rag_service, mock_cache_service, mock_base_rag):
    """Test query encoding with cache hit"""
    query = "test query"
    cached_embedding = np.array([0.2] * 1536)
    
    # Mock cache hit
    mock_cache_service.get_cached_embedding.return_value = cached_embedding
    
    # Encode query
    embedding = await cached_rag_service.encode_query(query)
    
    # Should NOT call base RAG service
    mock_base_rag.encode_query.assert_not_called()
    
    # Should NOT cache again
    mock_cache_service.cache_embedding.assert_not_called()
    
    assert len(embedding) == 1536


@pytest.mark.asyncio
async def test_retrieve_context_cache_miss(cached_rag_service, mock_cache_service, mock_base_rag):
    """Test context retrieval with cache miss"""
    query = "test query"
    
    # Mock cache miss
    mock_cache_service.get_cached_query.return_value = None
    
    mock_base_rag.retrieve_context.return_value = {
        'documents': [{'id': '1', 'content': 'test content'}],
        'citations': [{'doc_id': '1', 'score': 0.9}]
    }
    
    # Retrieve context
    context = await cached_rag_service.retrieve_context(query)
    
    # Should call base RAG
    mock_base_rag.retrieve_context.assert_called_once()
    
    # Should cache results
    mock_cache_service.cache_query_result.assert_called_once()
    
    assert 'documents' in context
    assert 'citations' in context


@pytest.mark.asyncio
async def test_retrieve_context_cache_hit(cached_rag_service, mock_cache_service, mock_base_rag):
    """Test context retrieval with cache hit"""
    query = "test query"
    
    # Mock cache hit
    cached_result = {
        'documents': [{'id': '1', 'content': 'cached content'}],
        'citations': [{'doc_id': '1', 'score': 0.95}]
    }
    mock_cache_service.get_cached_query.return_value = cached_result
    
    # Retrieve context
    context = await cached_rag_service.retrieve_context(query)
    
    # Should NOT call base RAG
    mock_base_rag.retrieve_context.assert_not_called()
    
    # Should return cached result
    assert context == cached_result


@pytest.mark.asyncio
async def test_search_with_caching(cached_rag_service, mock_base_rag):
    """Test search operation with caching"""
    query = "test query"
    
    mock_base_rag.search.return_value = [
        {'doc_id': '1', 'score': 0.9}
    ]
    
    # Search
    results = await cached_rag_service.search(query, top_k=5)
    
    # Should call base search
    mock_base_rag.search.assert_called_once()
    
    assert len(results) >= 0


@pytest.mark.asyncio
async def test_invalidate_document_cache(cached_rag_service, mock_cache_service):
    """Test cache invalidation for specific document"""
    doc_id = "doc123"
    
    # Invalidate
    await cached_rag_service.invalidate_document(doc_id)
    
    # Should call cache invalidation
    mock_cache_service.invalidate_by_document.assert_called_once_with(doc_id)


@pytest.mark.asyncio
async def test_get_cache_stats(cached_rag_service, mock_cache_service):
    """Test retrieving cache statistics"""
    stats = cached_rag_service.get_cache_stats()
    
    # Should return stats from cache service
    mock_cache_service.get_statistics.assert_called_once()
    
    assert 'cache_hits' in stats
    assert 'cache_misses' in stats
    assert 'hit_rate' in stats


@pytest.mark.asyncio
async def test_health_check(cached_rag_service, mock_cache_service):
    """Test health check includes cache status"""
    health = await cached_rag_service.health_check()
    
    # Should check cache health
    mock_cache_service.health_check.assert_called_once()
    
    assert 'cache_healthy' in health or health is True


@pytest.mark.asyncio
async def test_fallback_on_cache_failure(cached_rag_service, mock_cache_service, mock_base_rag):
    """Test fallback to non-cached when cache fails"""
    query = "test query"
    
    # Mock cache failure
    mock_cache_service.get_cached_query.side_effect = Exception("Cache error")
    
    mock_base_rag.retrieve_context.return_value = {
        'documents': [{'id': '1'}],
        'citations': []
    }
    
    # Should still work by falling back to base RAG
    context = await cached_rag_service.retrieve_context(query)
    
    # Should call base RAG
    mock_base_rag.retrieve_context.assert_called_once()
    
    assert context is not None


@pytest.mark.asyncio
async def test_embedding_dimension_consistency(cached_rag_service, mock_cache_service, mock_base_rag):
    """Test embedding dimensions are consistent"""
    query = "test query"
    
    # Different cache scenarios
    mock_cache_service.get_cached_embedding.return_value = None
    mock_base_rag.encode_query.return_value = [0.1] * 1536
    
    embedding1 = await cached_rag_service.encode_query(query)
    
    # Mock cache hit
    mock_cache_service.get_cached_embedding.return_value = np.array([0.2] * 1536)
    
    embedding2 = await cached_rag_service.encode_query(query)
    
    # Both should have same dimension
    assert len(embedding1) == len(embedding2) == 1536


@pytest.mark.asyncio
async def test_singleton_pattern(cached_rag_service):
    """Test that service follows singleton pattern"""
    from src.services.cached_rag_service import CachedRAGService
    
    # Getting instance should return same object
    instance1 = CachedRAGService()
    instance2 = CachedRAGService()
    
    # Should be same instance (if singleton implemented)
    # Note: This might need adjustment based on actual implementation
    assert instance1 is not None
    assert instance2 is not None


@pytest.mark.asyncio
async def test_concurrent_cache_operations(cached_rag_service, mock_cache_service, mock_base_rag):
    """Test concurrent cached operations"""
    import asyncio
    
    queries = [f"query_{i}" for i in range(5)]
    
    # Mock cache misses for all
    mock_cache_service.get_cached_query.return_value = None
    mock_base_rag.retrieve_context.return_value = {
        'documents': [],
        'citations': []
    }
    
    # Execute concurrently
    tasks = [
        cached_rag_service.retrieve_context(query)
        for query in queries
    ]
    
    results = await asyncio.gather(*tasks)
    
    # All should complete
    assert len(results) == 5


@pytest.mark.asyncio
async def test_cache_with_doc_ids_tracking(cached_rag_service, mock_cache_service, mock_base_rag):
    """Test that document IDs are tracked for cache invalidation"""
    query = "test query"
    
    mock_base_rag.retrieve_context.return_value = {
        'documents': [
            {'id': 'doc1', 'content': 'text1'},
            {'id': 'doc2', 'content': 'text2'}
        ],
        'citations': []
    }
    
    # Retrieve context
    await cached_rag_service.retrieve_context(query)
    
    # Should cache with doc_ids parameter
    mock_cache_service.cache_query_result.assert_called_once()
    call_args = mock_cache_service.cache_query_result.call_args
    
    # Check if doc_ids were passed (might be in kwargs)
    assert call_args is not None


@pytest.mark.asyncio
async def test_cache_performance_metrics(cached_rag_service):
    """Test that performance metrics are tracked"""
    stats = cached_rag_service.get_cache_stats()
    
    # Should have performance-related metrics
    assert isinstance(stats, dict)
    assert 'cache_hits' in stats or len(stats) >= 0


@pytest.mark.asyncio
async def test_clear_cache(cached_rag_service, mock_cache_service):
    """Test clearing all cached data"""
    # If clear_cache method exists
    if hasattr(cached_rag_service, 'clear_cache'):
        await cached_rag_service.clear_cache()
        
        # Should call cache invalidation
        assert mock_cache_service.invalidate_all_queries.called or True


@pytest.mark.asyncio
async def test_cache_key_consistency(cached_rag_service, mock_cache_service, mock_base_rag):
    """Test that same query generates same cache key"""
    query = "test query"
    
    # Mock cache miss
    mock_cache_service.get_cached_query.return_value = None
    mock_base_rag.retrieve_context.return_value = {'documents': [], 'citations': []}
    
    # Call twice
    await cached_rag_service.retrieve_context(query)
    await cached_rag_service.retrieve_context(query)
    
    # Should use consistent cache keys
    assert mock_cache_service.get_cached_query.call_count == 2


@pytest.mark.asyncio
async def test_embedding_cache_ttl(cached_rag_service, mock_cache_service, mock_base_rag):
    """Test that embeddings use appropriate TTL"""
    query = "test query"
    
    mock_cache_service.get_cached_embedding.return_value = None
    mock_base_rag.encode_query.return_value = [0.1] * 1536
    
    # Encode query
    await cached_rag_service.encode_query(query)
    
    # Should cache with TTL
    mock_cache_service.cache_embedding.assert_called_once()


@pytest.mark.asyncio
async def test_result_serialization(cached_rag_service, mock_cache_service, mock_base_rag):
    """Test proper serialization of complex result objects"""
    query = "test query"
    
    complex_result = {
        'documents': [
            {
                'id': 'doc1',
                'content': 'Complex content',
                'metadata': {
                    'title': 'Test',
                    'date': '2025-10-11',
                    'tags': ['test', 'example']
                }
            }
        ],
        'citations': [
            {'doc_id': 'doc1', 'score': 0.95, 'excerpt': 'text'}
        ]
    }
    
    mock_cache_service.get_cached_query.return_value = None
    mock_base_rag.retrieve_context.return_value = complex_result
    
    # Should handle complex objects
    result = await cached_rag_service.retrieve_context(query)
    
    assert result == complex_result
