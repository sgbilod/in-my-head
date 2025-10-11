"""
Comprehensive test suite for metadata extraction.

Tests:
- MetadataExtractor: Extraction, caching, batch processing
- Metadata types: Author, Topic, Entity, etc.
- Integration: End-to-end workflows
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import after path setup
# pylint: disable=wrong-import-position
from metadata import (
    MetadataExtractor,
    ExtractedMetadata,
    Author,
    Topic,
    Entity,
    DateReference,
    Category,
    Sentiment,
    EntityType,
    CategoryType,
    MetadataField,
)
# pylint: enable=wrong-import-position


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_text():
    """Sample text for extraction."""
    return """
    Artificial Intelligence and Machine Learning in 2025
    
    By Dr. Jane Smith and Prof. John Doe
    Published: October 11, 2025
    
    Artificial intelligence (AI) has made tremendous progress in recent years.
    Major tech companies like Google, Microsoft, and OpenAI are leading
    the development of large language models. These models, such as GPT-4
    and Claude, are revolutionizing how we interact with technology.
    
    The field of machine learning continues to evolve rapidly, with new
    breakthroughs in areas like computer vision, natural language processing,
    and robotics. Researchers at Stanford University and MIT are pushing
    the boundaries of what's possible.
    
    This technology has applications in healthcare, education, finance,
    and many other sectors. The future looks promising for AI development.
    """


@pytest.fixture
def mock_anthropic_response():
    """Mock Claude API response."""
    return {
        "authors": [
            {"name": "Dr. Jane Smith", "role": "author", "confidence": 0.95},
            {"name": "Prof. John Doe", "role": "author", "confidence": 0.95},
        ],
        "topics": [
            {
                "name": "Artificial Intelligence",
                "relevance": 1.0,
                "subtopics": ["Machine Learning", "Deep Learning"],
            },
            {
                "name": "Technology",
                "relevance": 0.9,
                "subtopics": ["Large Language Models"],
            },
        ],
        "entities": [
            {
                "name": "Google",
                "type": "organization",
                "mentions": 1,
                "confidence": 1.0,
            },
            {
                "name": "Microsoft",
                "type": "organization",
                "mentions": 1,
                "confidence": 1.0,
            },
            {
                "name": "OpenAI",
                "type": "organization",
                "mentions": 1,
                "confidence": 1.0,
            },
            {
                "name": "Stanford University",
                "type": "organization",
                "mentions": 1,
                "confidence": 1.0,
            },
            {
                "name": "MIT",
                "type": "organization",
                "mentions": 1,
                "confidence": 1.0,
            },
        ],
        "dates": [
            {
                "date": "2025-10-11",
                "context": "publication date",
                "type": "published",
            }
        ],
        "categories": [
            {
                "name": "technology",
                "subcategory": "Artificial Intelligence",
                "confidence": 0.98,
            },
            {
                "name": "science",
                "subcategory": "Computer Science",
                "confidence": 0.95,
            },
        ],
        "summary": (
            "An overview of artificial intelligence and machine learning "
            "progress in 2025, highlighting contributions from major tech "
            "companies and research institutions."
        ),
        "keywords": [
            "artificial intelligence",
            "machine learning",
            "large language models",
            "GPT-4",
            "Claude",
            "deep learning",
        ],
        "title": "Artificial Intelligence and Machine Learning in 2025",
        "language": "en",
        "sentiment": {"score": 0.7, "label": "positive", "confidence": 0.9},
    }


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.info.return_value = {"db0": {"keys": 0}}
    redis_mock.close = AsyncMock()
    return redis_mock


@pytest.fixture
def mock_anthropic_client(mock_anthropic_response):
    """Mock Anthropic client."""
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = str(mock_anthropic_response).replace("'", '"')
    mock_response.content = [mock_content]

    mock_client = Mock()
    mock_client.messages.create.return_value = mock_response

    return mock_client


# ============================================================================
# METADATA TYPES TESTS
# ============================================================================


class TestMetadataTypes:
    """Test metadata type dataclasses."""

    def test_author_creation(self):
        """Test Author creation."""
        author = Author(
            name="John Doe",
            role="author",
            affiliation="MIT",
            confidence=0.95,
        )

        assert author.name == "John Doe"
        assert author.role == "author"
        assert author.affiliation == "MIT"
        assert author.confidence == 0.95

    def test_author_to_dict(self):
        """Test Author to_dict method."""
        author = Author(name="John Doe", role="author")
        author_dict = author.to_dict()

        assert author_dict["name"] == "John Doe"
        assert author_dict["role"] == "author"
        assert "confidence" in author_dict

    def test_topic_creation(self):
        """Test Topic creation."""
        topic = Topic(
            name="AI",
            relevance=0.95,
            subtopics=["ML", "DL"],
        )

        assert topic.name == "AI"
        assert topic.relevance == 0.95
        assert len(topic.subtopics) == 2

    def test_entity_creation(self):
        """Test Entity creation."""
        entity = Entity(
            name="Google",
            type=EntityType.ORGANIZATION,
            mentions=5,
            confidence=0.98,
        )

        assert entity.name == "Google"
        assert entity.type == EntityType.ORGANIZATION
        assert entity.mentions == 5

    def test_date_reference_creation(self):
        """Test DateReference creation."""
        date_ref = DateReference(
            date="2025-10-11",
            context="publication",
            type="published",
        )

        assert date_ref.date == "2025-10-11"
        assert date_ref.context == "publication"

    def test_category_creation(self):
        """Test Category creation."""
        category = Category(
            name=CategoryType.TECHNOLOGY,
            subcategory="AI",
            confidence=0.95,
        )

        assert category.name == CategoryType.TECHNOLOGY
        assert category.subcategory == "AI"

    def test_sentiment_creation(self):
        """Test Sentiment creation."""
        sentiment = Sentiment(
            score=0.7,
            label="positive",
            confidence=0.9,
        )

        assert sentiment.score == 0.7
        assert sentiment.label == "positive"


# ============================================================================
# METADATA EXTRACTOR TESTS
# ============================================================================


class TestMetadataExtractor:
    """Test MetadataExtractor class."""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_redis):
        """Test extractor initialization."""
        with patch("metadata.metadata_extractor.redis.Redis") as MockRedis:
            MockRedis.return_value = mock_redis

            extractor = MetadataExtractor(
                anthropic_api_key="test-key",
                redis_host="localhost",
            )

            assert extractor.model == "claude-sonnet-4-20250514"
            assert extractor.cache_ttl == 604800

    @pytest.mark.asyncio
    async def test_extract_with_cache_miss(
        self, sample_text, mock_redis, mock_anthropic_client,
        mock_anthropic_response
    ):
        """Test extraction with cache miss."""
        with patch("metadata.metadata_extractor.redis.Redis") as MockRedis:
            with patch(
                "metadata.metadata_extractor.Anthropic"
            ) as MockAnthropic:
                MockRedis.return_value = mock_redis
                MockAnthropic.return_value = mock_anthropic_client

                extractor = MetadataExtractor(anthropic_api_key="test-key")
                metadata = await extractor.extract(sample_text)

                assert isinstance(metadata, ExtractedMetadata)
                assert extractor.stats["cache_misses"] == 1
                assert extractor.stats["total_extracted"] == 1

    @pytest.mark.asyncio
    async def test_extract_with_cache_hit(
        self, sample_text, mock_redis, mock_anthropic_client
    ):
        """Test extraction with cache hit."""
        # Setup cached response
        import json

        cached_data = {
            "authors": [],
            "topics": [],
            "entities": [],
            "dates": [],
            "categories": [],
            "summary": "Test summary",
            "keywords": ["test"],
            "title": "Test Title",
            "language": "en",
            "sentiment": None,
            "extracted_at": datetime.now().isoformat(),
            "confidence": 1.0,
        }
        mock_redis.get.return_value = json.dumps(cached_data)

        with patch("metadata.metadata_extractor.redis.Redis") as MockRedis:
            with patch("metadata.metadata_extractor.Anthropic") as MockAnthropic:
                MockRedis.return_value = mock_redis
                MockAnthropic.return_value = mock_anthropic_client

                extractor = MetadataExtractor(anthropic_api_key="test-key")
                metadata = await extractor.extract(sample_text, use_cache=True)

                assert isinstance(metadata, ExtractedMetadata)
                assert extractor.stats["cache_hits"] == 1
                # Should not call Claude
                mock_anthropic_client.messages.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_batch(
        self, sample_text, mock_redis, mock_anthropic_client
    ):
        """Test batch extraction."""
        texts = [sample_text, sample_text[:100], sample_text[:200]]

        with patch("metadata.metadata_extractor.redis.Redis") as MockRedis:
            with patch("metadata.metadata_extractor.Anthropic") as MockAnthropic:
                MockRedis.return_value = mock_redis
                MockAnthropic.return_value = mock_anthropic_client

                extractor = MetadataExtractor(anthropic_api_key="test-key")
                results = await extractor.extract_batch(texts)

                assert len(results) == 3
                assert all(isinstance(r, ExtractedMetadata) for r in results)

    @pytest.mark.asyncio
    async def test_extract_specific_fields(
        self, sample_text, mock_redis, mock_anthropic_client
    ):
        """Test extraction with specific fields."""
        fields = {MetadataField.AUTHORS, MetadataField.TOPICS}

        with patch("metadata.metadata_extractor.redis.Redis") as MockRedis:
            with patch("metadata.metadata_extractor.Anthropic") as MockAnthropic:
                MockRedis.return_value = mock_redis
                MockAnthropic.return_value = mock_anthropic_client

                extractor = MetadataExtractor(anthropic_api_key="test-key")
                metadata = await extractor.extract(
                    sample_text, fields=fields
                )

                assert isinstance(metadata, ExtractedMetadata)

    @pytest.mark.asyncio
    async def test_get_stats(self, mock_redis, mock_anthropic_client):
        """Test statistics retrieval."""
        with patch("metadata.metadata_extractor.redis.Redis") as MockRedis:
            with patch("metadata.metadata_extractor.Anthropic") as MockAnthropic:
                MockRedis.return_value = mock_redis
                MockAnthropic.return_value = mock_anthropic_client

                extractor = MetadataExtractor(anthropic_api_key="test-key")
                stats = await extractor.get_stats()

                assert "total_extracted" in stats
                assert "cache_hits" in stats
                assert "cache_hit_rate" in stats


# ============================================================================
# EXTRACTED METADATA TESTS
# ============================================================================


class TestExtractedMetadata:
    """Test ExtractedMetadata class."""

    def test_creation(self, sample_text):
        """Test ExtractedMetadata creation."""
        metadata = ExtractedMetadata(
            text=sample_text,
            authors=[Author(name="John Doe")],
            topics=[Topic(name="AI")],
        )

        assert len(metadata.authors) == 1
        assert len(metadata.topics) == 1

    def test_to_dict(self, sample_text):
        """Test to_dict conversion."""
        metadata = ExtractedMetadata(
            text=sample_text,
            authors=[Author(name="John Doe")],
            summary="Test summary",
            keywords=["ai", "ml"],
        )

        metadata_dict = metadata.to_dict()

        assert "authors" in metadata_dict
        assert "summary" in metadata_dict
        assert "keywords" in metadata_dict
        assert len(metadata_dict["authors"]) == 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for metadata extraction."""

    @pytest.mark.asyncio
    async def test_end_to_end_extraction(
        self, sample_text, mock_redis, mock_anthropic_client
    ):
        """Test complete extraction workflow."""
        with patch("metadata.metadata_extractor.redis.Redis") as MockRedis:
            with patch("metadata.metadata_extractor.Anthropic") as MockAnthropic:
                MockRedis.return_value = mock_redis
                MockAnthropic.return_value = mock_anthropic_client

                # Initialize extractor
                extractor = MetadataExtractor(anthropic_api_key="test-key")

                # Extract metadata
                metadata = await extractor.extract(sample_text)

                # Verify results
                assert isinstance(metadata, ExtractedMetadata)
                assert metadata.text is not None

                # Get statistics
                stats = await extractor.get_stats()
                assert stats["total_extracted"] == 1

                # Close
                await extractor.close()


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v", "--tb=short"])
