"""
Comprehensive test suite for embedding generation.

Tests:
- EmbeddingGenerator: Single and batch embedding generation
- EmbeddingCache: Redis-based caching operations
- BatchEmbeddingProcessor: Batch processing with caching
- Integration tests: End-to-end workflows
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, AsyncMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import after path setup
# pylint: disable=wrong-import-position
from embeddings import (
    EmbeddingGenerator,
    Embedding,
    EmbeddingCache,
    BatchEmbeddingProcessor,
)
# pylint: enable=wrong-import-position


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_texts():
    """Sample texts for testing."""
    return [
        "The quick brown fox jumps over the lazy dog.",
        "Python is a high-level programming language.",
        "Machine learning is a subset of artificial intelligence.",
        "Redis is an in-memory data structure store.",
        "Natural language processing enables computers to understand text.",
    ]


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response (v1.x format)."""

    class MockEmbedding:
        def __init__(self):
            self.embedding = [0.1] * 1536
            self.index = 0

    class MockUsage:
        def __init__(self):
            self.prompt_tokens = 10
            self.total_tokens = 10

    class MockResponse:
        def __init__(self):
            self.data = [MockEmbedding()]
            self.usage = MockUsage()
            self.model = "text-embedding-3-small"

    return MockResponse()


@pytest.fixture
def mock_openai_batch_response():
    """Mock OpenAI API batch response (v1.x format)."""

    class MockEmbedding:
        def __init__(self, value):
            self.embedding = [value] * 1536
            self.index = 0

    class MockUsage:
        def __init__(self):
            self.prompt_tokens = 30
            self.total_tokens = 30

    class MockResponse:
        def __init__(self):
            self.data = [
                MockEmbedding(0.1),
                MockEmbedding(0.2),
                MockEmbedding(0.3),
            ]
            self.usage = MockUsage()
            self.model = "text-embedding-3-small"

    return MockResponse()


# ============================================================================
# EMBEDDING GENERATOR TESTS
# ============================================================================


class TestEmbeddingGenerator:
    """Test EmbeddingGenerator class."""

    def test_initialization(self):
        """Test generator initialization."""
        # Mock API key
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = EmbeddingGenerator(model="text-embedding-3-small")

            assert generator.model == "text-embedding-3-small"
            assert generator.dimensions == 1536
            assert generator.api_key == "test-key"

    def test_initialization_invalid_model(self):
        """Test initialization with invalid model."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with pytest.raises(ValueError, match="Unknown model"):
                EmbeddingGenerator(model="invalid-model")

    def test_initialization_no_api_key(self):
        """Test initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                EmbeddingGenerator()

    def test_generate_single_embedding(self, mock_openai_response):
        """Test generating single embedding."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as MockOpenAI:
                mock_client = Mock()
                mock_client.embeddings.create.return_value = mock_openai_response
                MockOpenAI.return_value = mock_client

                generator = EmbeddingGenerator()
                embedding = generator.generate("Test text")

                assert isinstance(embedding, Embedding)
                assert len(embedding.vector) == 1536
                assert embedding.text == "Test text"
                assert embedding.model == "text-embedding-3-small"
                assert embedding.token_count == 10
                assert embedding.embedding_id is not None

    def test_generate_with_metadata(self, mock_openai_response):
        """Test generating embedding with metadata."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as MockOpenAI:
                mock_client = Mock()
                mock_client.embeddings.create.return_value = mock_openai_response
                MockOpenAI.return_value = mock_client

                generator = EmbeddingGenerator()
                metadata = {"source": "test", "chunk_id": 1}
                embedding = generator.generate("Test text", metadata=metadata)

                assert embedding.metadata == metadata

    def test_generate_empty_text(self):
        """Test generating embedding for empty text."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = EmbeddingGenerator()

            with pytest.raises(ValueError, match="Text cannot be empty"):
                generator.generate("")

    def test_generate_batch(
        self, sample_texts, mock_openai_batch_response
    ):
        """Test generating batch of embeddings."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as MockOpenAI:
                mock_client = Mock()
                mock_client.embeddings.create.return_value = mock_openai_batch_response
                MockOpenAI.return_value = mock_client

                generator = EmbeddingGenerator()
                embeddings = generator.generate_batch(sample_texts[:3])

                assert len(embeddings) == 3
                assert all(isinstance(e, Embedding) for e in embeddings)
                assert all(len(e.vector) == 1536 for e in embeddings)

    def test_generate_batch_with_metadata(
        self, sample_texts, mock_openai_batch_response
    ):
        """Test generating batch with metadata."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as MockOpenAI:
                mock_client = Mock()
                mock_client.embeddings.create.return_value = mock_openai_batch_response
                MockOpenAI.return_value = mock_client

                generator = EmbeddingGenerator()
                metadata_list = [
                    {"id": 1},
                    {"id": 2},
                    {"id": 3},
                ]
                embeddings = generator.generate_batch(
                    sample_texts[:3], metadata_list
                )

                assert all(
                    e.metadata["id"] == i + 1
                    for i, e in enumerate(embeddings)
                )

    def test_statistics_tracking(self, mock_openai_response):
        """Test usage statistics tracking."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as MockOpenAI:
                mock_client = Mock()
                mock_client.embeddings.create.return_value = mock_openai_response
                MockOpenAI.return_value = mock_client

                generator = EmbeddingGenerator()

                # Generate some embeddings
                generator.generate("Test 1")
                generator.generate("Test 2")

                stats = generator.get_stats()

                assert stats["total_embeddings"] == 2
                assert stats["total_tokens"] == 20
                assert stats["total_cost"] > 0
                assert stats["failed_requests"] == 0


# ============================================================================
# EMBEDDING CACHE TESTS
# ============================================================================


class TestEmbeddingCache:
    """Test EmbeddingCache class."""

    @pytest.mark.asyncio
    async def test_cache_initialization(self):
        """Test cache initialization."""
        cache = EmbeddingCache(
            redis_url="redis://localhost:6379",
            ttl=3600,
            prefix="test:",
        )

        assert cache.ttl == 3600
        assert cache.prefix == "test:"

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation."""
        cache = EmbeddingCache(prefix="test:")

        key = cache._generate_cache_key("test text", "model-name")

        assert key.startswith("test:")
        assert len(key) > len("test:")  # Has hash

    @pytest.mark.asyncio
    async def test_cache_get_set(self, mock_openai_response):
        """Test cache get/set operations."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as MockOpenAI:
                mock_client = Mock()
                mock_client.embeddings.create.return_value = mock_openai_response
                MockOpenAI.return_value = mock_client

                # Create embedding
                generator = EmbeddingGenerator()
                embedding = generator.generate("Test text")

                # Mock Redis client
                mock_redis = AsyncMock()
                mock_redis.get.return_value = None
                mock_redis.setex.return_value = True

                cache = EmbeddingCache()
                cache.redis_client = mock_redis

                # Set in cache
                result = await cache.set(embedding)
                assert result is True

                # Mock get returning serialized data
                import json

                mock_redis.get.return_value = json.dumps(
                    embedding.to_dict()
                ).encode()

                # Get from cache
                cached = await cache.get("Test text", embedding.model)
                assert cached is not None
                assert cached.text == embedding.text
                assert len(cached.vector) == len(embedding.vector)

    @pytest.mark.asyncio
    async def test_cache_statistics(self):
        """Test cache statistics tracking."""
        cache = EmbeddingCache()

        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        cache.redis_client = mock_redis

        # Cause cache misses
        await cache.get("text1", "model")
        await cache.get("text2", "model")

        stats = await cache.get_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.0


# ============================================================================
# BATCH PROCESSOR TESTS
# ============================================================================


class TestBatchEmbeddingProcessor:
    """Test BatchEmbeddingProcessor class."""

    def test_processor_initialization(self):
        """Test processor initialization."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = EmbeddingGenerator()
            cache = EmbeddingCache()

            processor = BatchEmbeddingProcessor(
                generator=generator,
                cache=cache,
                batch_size=50,
                max_parallel=3,
            )

            assert processor.batch_size == 50
            assert processor.max_parallel == 3
            assert processor.use_cache is True

    def test_batch_splitting(self):
        """Test batch splitting logic."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            generator = EmbeddingGenerator()
            processor = BatchEmbeddingProcessor(
                generator=generator,
                batch_size=2,
            )

            texts = ["text1", "text2", "text3", "text4", "text5"]
            metadata = [{}] * 5

            batches = processor._split_batches(texts, metadata)

            assert len(batches) == 3  # 5 texts / 2 per batch = 3 batches
            assert len(batches[0][0]) == 2
            assert len(batches[1][0]) == 2
            assert len(batches[2][0]) == 1

    @pytest.mark.asyncio
    async def test_process_batch_with_cache(
        self, sample_texts, mock_openai_response
    ):
        """Test batch processing with cache hits."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as MockOpenAI:
                mock_client = Mock()
                mock_client.embeddings.create.return_value = mock_openai_response
                MockOpenAI.return_value = mock_client

                generator = EmbeddingGenerator()

                # Mock cache with some hits
                cache = Mock(spec=EmbeddingCache)
                cache.get_batch = AsyncMock(return_value={})
                cache.set_batch = AsyncMock(return_value=3)

                processor = BatchEmbeddingProcessor(
                    generator=generator,
                    cache=cache,
                    batch_size=10,
                )

                embeddings = await processor.process_batch(
                    sample_texts[:3], show_progress=False
                )

                assert len(embeddings) == 3
                cache.set_batch.assert_called_once()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(
        self, sample_texts, mock_openai_batch_response
    ):
        """Test complete embedding generation workflow."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as MockOpenAI:
                mock_client = Mock()
                mock_client.embeddings.create.return_value = mock_openai_batch_response
                MockOpenAI.return_value = mock_client

                # Initialize components
                generator = EmbeddingGenerator()

                # Mock cache
                cache = Mock(spec=EmbeddingCache)
                cache.get_batch = AsyncMock(return_value={})
                cache.set_batch = AsyncMock(return_value=3)

                # Create processor
                processor = BatchEmbeddingProcessor(
                    generator=generator,
                    cache=cache,
                )

                # Process batch
                embeddings = await processor.process_batch(
                    sample_texts[:3], show_progress=False
                )

                # Verify results
                assert len(embeddings) == 3
                assert all(isinstance(e, Embedding) for e in embeddings)
                assert all(len(e.vector) == 1536 for e in embeddings)

                # Verify cache was used
                cache.get_batch.assert_called_once()
                cache.set_batch.assert_called_once()


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v", "--tb=short"])
