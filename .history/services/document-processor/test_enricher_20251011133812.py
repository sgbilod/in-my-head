"""
Tests for metadata enricher.

Tests the MetadataEnricher class that orchestrates the complete
document enrichment pipeline.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import List

# Add src to path for imports
import sys
import os

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "src"),
)

# pylint: disable=wrong-import-position
from metadata.metadata_enricher import (
    MetadataEnricher,
    EnrichedDocument,
    EnrichmentStats,
)
from metadata.metadata_extractor import ExtractedMetadata
from metadata.metadata_types import (
    Author,
    Topic,
    Entity,
    Category,
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
    """Sample document text."""
    return """
    Artificial Intelligence in Healthcare

    By Dr. Jane Smith and Prof. Michael Chen

    Machine learning and deep learning are transforming medical diagnosis.
    Companies like DeepMind and IBM Watson Health are pioneering AI
    applications in healthcare, enabling early disease detection and
    personalized treatment plans.
    """


@pytest.fixture
def mock_metadata():
    """Mock extracted metadata."""
    return ExtractedMetadata(
        text="Sample text preview...",
        authors=[
            Author(name="Dr. Jane Smith", role="author", confidence=0.95),
            Author(name="Prof. Michael Chen", role="author", confidence=0.93),
        ],
        topics=[
            Topic(
                name="Artificial Intelligence",
                relevance=0.98,
                subtopics=["Machine Learning", "Deep Learning"],
            ),
            Topic(name="Healthcare", relevance=0.95, subtopics=["Diagnosis"]),
        ],
        entities=[
            Entity(
                name="DeepMind",
                type=EntityType.ORGANIZATION,
                mentions=1,
                confidence=0.92,
            ),
            Entity(
                name="IBM Watson Health",
                type=EntityType.ORGANIZATION,
                mentions=1,
                confidence=0.90,
            ),
        ],
        dates=[],
        categories=[
            Category(
                name=CategoryType.TECHNOLOGY,
                subcategory="AI",
                confidence=0.95,
            ),
            Category(
                name=CategoryType.HEALTH, subcategory="Medicine", confidence=0.90
            ),
        ],
        summary="AI is transforming healthcare through ML and deep learning.",
        keywords=["AI", "healthcare", "machine learning", "diagnosis"],
        title="Artificial Intelligence in Healthcare",
        language="en",
        sentiment=None,
        extracted_at=datetime.utcnow(),
        confidence=0.93,
    )


@pytest.fixture
def mock_embedding():
    """Mock embedding vector."""
    return [0.1] * 3072  # 3072-dimensional vector


@pytest.fixture
def mock_metadata_extractor(mock_metadata):
    """Mock MetadataExtractor."""
    extractor = AsyncMock()
    extractor.extract = AsyncMock(return_value=mock_metadata)
    extractor.extract_batch = AsyncMock(return_value=[mock_metadata])
    extractor.close = AsyncMock()
    return extractor


@pytest.fixture
def mock_embedding_generator(mock_embedding):
    """Mock EmbeddingGenerator."""

    class MockEmbedding:
        def __init__(self, vector):
            self.vector = vector

    generator = AsyncMock()
    generator.generate = AsyncMock(
        return_value=MockEmbedding(mock_embedding)
    )
    return generator


@pytest.fixture
def mock_vector_store():
    """Mock VectorStore."""
    store = AsyncMock()
    store.insert = AsyncMock(return_value="vec_123")
    store.search = AsyncMock(return_value=[])
    store.filter_search = AsyncMock(return_value=[])
    store.update_payload = AsyncMock(return_value=True)
    store.delete = AsyncMock(return_value=True)
    return store


@pytest.fixture
def enricher(
    mock_metadata_extractor, mock_embedding_generator, mock_vector_store
):
    """MetadataEnricher instance with mocked dependencies."""
    return MetadataEnricher(
        metadata_extractor=mock_metadata_extractor,
        embedding_generator=mock_embedding_generator,
        vector_store=mock_vector_store,
    )


# ============================================================================
# TEST ENRICHED DOCUMENT
# ============================================================================


class TestEnrichedDocument:
    """Test EnrichedDocument class."""

    def test_creation(self, mock_metadata, mock_embedding):
        """Test EnrichedDocument creation."""
        doc = EnrichedDocument(
            id="doc123",
            text="Sample text",
            embedding=mock_embedding,
            metadata=mock_metadata,
            source="test.pdf",
            confidence=0.95,
        )

        assert doc.id == "doc123"
        assert doc.text == "Sample text"
        assert len(doc.embedding) == 3072
        assert doc.metadata == mock_metadata
        assert doc.source == "test.pdf"
        assert doc.confidence == 0.95
        assert doc.enriched_at is not None

    def test_to_vector_payload(self, mock_metadata, mock_embedding):
        """Test conversion to vector payload."""
        doc = EnrichedDocument(
            id="doc123",
            text="Sample text",
            embedding=mock_embedding,
            metadata=mock_metadata,
        )

        payload = doc.to_vector_payload()

        assert payload["id"] == "doc123"
        assert payload["text"] == "Sample text"
        assert len(payload["authors"]) == 2
        assert payload["authors"][0]["name"] == "Dr. Jane Smith"
        assert len(payload["topics"]) == 2
        assert payload["topics"][0]["name"] == "Artificial Intelligence"
        assert len(payload["entities"]) == 2
        assert len(payload["categories"]) == 2
        assert payload["summary"] is not None
        assert len(payload["keywords"]) == 4


# ============================================================================
# TEST ENRICHMENT STATS
# ============================================================================


class TestEnrichmentStats:
    """Test EnrichmentStats class."""

    def test_initial_stats(self):
        """Test initial statistics."""
        stats = EnrichmentStats()

        assert stats.total_processed == 0
        assert stats.successful == 0
        assert stats.failed == 0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = EnrichmentStats(
            total_processed=10,
            successful=8,
            failed=2,
            cache_hits=5,
            cache_misses=5,
        )

        stats_dict = stats.to_dict()

        assert stats_dict["total_processed"] == 10
        assert stats_dict["successful"] == 8
        assert stats_dict["failed"] == 2
        assert stats_dict["success_rate"] == 0.8
        assert stats_dict["cache_hit_rate"] == 0.5


# ============================================================================
# TEST METADATA ENRICHER
# ============================================================================


class TestMetadataEnricher:
    """Test MetadataEnricher class."""

    def test_initialization(self, enricher):
        """Test enricher initialization."""
        assert enricher.chunk_size == 1000
        assert enricher.chunk_overlap == 200
        assert enricher.metadata_fields is None

    @pytest.mark.asyncio
    async def test_enrich_document(
        self, enricher, sample_text, mock_metadata, mock_embedding
    ):
        """Test single document enrichment."""
        result = await enricher.enrich_document(
            text=sample_text, doc_id="doc123", source="test.pdf"
        )

        assert isinstance(result, EnrichedDocument)
        assert result.id == "doc123"
        assert result.text == sample_text
        assert len(result.embedding) == 3072
        assert result.metadata == mock_metadata
        assert result.source == "test.pdf"
        assert result.vector_id == "vec_123"

        # Verify calls
        enricher.metadata_extractor.extract.assert_called_once()
        enricher.embedding_generator.generate.assert_called_once()
        enricher.vector_store.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_enrich_document_auto_id(
        self, enricher, sample_text
    ):
        """Test document enrichment with auto-generated ID."""
        result = await enricher.enrich_document(text=sample_text)

        assert result.id is not None
        assert len(result.id) == 16  # SHA256 hash truncated to 16 chars

    @pytest.mark.asyncio
    async def test_enrich_document_no_store(
        self, enricher, sample_text
    ):
        """Test document enrichment without vector storage."""
        result = await enricher.enrich_document(
            text=sample_text, doc_id="doc123", store_in_vector_db=False
        )

        assert result.vector_id is None
        enricher.vector_store.insert.assert_not_called()

    @pytest.mark.asyncio
    async def test_enrich_document_empty_text(self, enricher):
        """Test enrichment with empty text."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await enricher.enrich_document(text="")

    @pytest.mark.asyncio
    async def test_enrich_document_with_specific_fields(
        self, enricher, sample_text
    ):
        """Test enrichment with specific metadata fields."""
        fields = {MetadataField.AUTHORS, MetadataField.TOPICS}

        await enricher.enrich_document(
            text=sample_text, metadata_fields=fields
        )

        # Verify fields were passed to extractor
        call_args = enricher.metadata_extractor.extract.call_args
        assert call_args[1]["fields"] == fields

    @pytest.mark.asyncio
    async def test_enrich_batch(self, enricher):
        """Test batch document enrichment."""
        documents = [
            {"text": "Document 1", "id": "doc1", "source": "file1.pdf"},
            {"text": "Document 2", "id": "doc2"},
            {"text": "Document 3"},
        ]

        results = await enricher.enrich_batch(documents)

        assert len(results) == 3
        assert all(isinstance(doc, EnrichedDocument) for doc in results)
        assert results[0].id == "doc1"
        assert results[1].id == "doc2"
        assert results[0].source == "file1.pdf"

    @pytest.mark.asyncio
    async def test_enrich_batch_with_failures(
        self, enricher, mock_metadata_extractor
    ):
        """Test batch enrichment with some failures."""
        # Make second document fail
        mock_metadata_extractor.extract.side_effect = [
            mock_metadata_extractor.extract.return_value,
            Exception("Extraction failed"),
            mock_metadata_extractor.extract.return_value,
        ]

        documents = [
            {"text": "Document 1"},
            {"text": "Document 2"},
            {"text": "Document 3"},
        ]

        results = await enricher.enrich_batch(documents)

        # Should have 2 successful (doc1 and doc3)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_metadata_with_query(
        self, enricher, mock_embedding
    ):
        """Test metadata search with text query."""
        await enricher.search_by_metadata(
            query_text="machine learning",
            authors=["Dr. Smith"],
            categories=["technology"],
            limit=5,
        )

        # Verify embedding generation for query
        enricher.embedding_generator.generate.assert_called_once_with(
            "machine learning"
        )

        # Verify vector search was called
        enricher.vector_store.search.assert_called_once()
        call_args = enricher.vector_store.search.call_args
        assert call_args[1]["limit"] == 5

    @pytest.mark.asyncio
    async def test_search_by_metadata_filter_only(self, enricher):
        """Test metadata search without text query."""
        await enricher.search_by_metadata(
            authors=["Dr. Smith"], categories=["technology"]
        )

        # Should use filter search (no embedding)
        enricher.embedding_generator.generate.assert_not_called()
        enricher.vector_store.filter_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_metadata(self, enricher):
        """Test updating document metadata."""
        updates = {"summary": "New summary", "keywords": ["new", "keywords"]}

        result = await enricher.update_document_metadata("doc123", updates)

        assert result is True
        enricher.vector_store.update_payload.assert_called_once_with(
            doc_id="doc123", payload_updates=updates
        )

    @pytest.mark.asyncio
    async def test_delete_document(self, enricher):
        """Test deleting document."""
        result = await enricher.delete_document("doc123")

        assert result is True
        enricher.vector_store.delete.assert_called_once_with("doc123")

    def test_get_stats(self, enricher):
        """Test getting enrichment statistics."""
        # Manually update stats
        enricher._stats.total_processed = 10
        enricher._stats.successful = 8
        enricher._stats.failed = 2

        stats = enricher.get_stats()

        assert stats["total_processed"] == 10
        assert stats["successful"] == 8
        assert stats["failed"] == 2
        assert stats["success_rate"] == 0.8

    @pytest.mark.asyncio
    async def test_close(self, enricher):
        """Test closing enricher."""
        await enricher.close()

        enricher.metadata_extractor.close.assert_called_once()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for the enrichment pipeline."""

    @pytest.mark.asyncio
    async def test_complete_pipeline(
        self,
        enricher,
        sample_text,
        mock_metadata,
        mock_embedding,
    ):
        """Test complete enrichment pipeline."""
        # Enrich document
        doc = await enricher.enrich_document(
            text=sample_text, doc_id="doc123", source="test.pdf"
        )

        # Verify document structure
        assert doc.id == "doc123"
        assert doc.text == sample_text
        assert len(doc.embedding) == 3072
        assert doc.vector_id == "vec_123"

        # Verify metadata
        assert len(doc.metadata.authors) == 2
        assert len(doc.metadata.topics) == 2
        assert len(doc.metadata.entities) == 2
        assert len(doc.metadata.categories) == 2
        assert doc.metadata.summary is not None

        # Verify payload
        payload = doc.to_vector_payload()
        assert payload["id"] == "doc123"
        assert len(payload["authors"]) == 2
        assert payload["authors"][0]["name"] == "Dr. Jane Smith"

        # Get statistics
        stats = enricher.get_stats()
        assert stats["total_processed"] == 1
        assert stats["successful"] == 1
        assert stats["success_rate"] == 1.0
