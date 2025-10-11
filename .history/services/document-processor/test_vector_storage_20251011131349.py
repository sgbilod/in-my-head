"""
Comprehensive test suite for vector storage.

Tests:
- VectorStore: Insert, search, delete operations
- CollectionManager: Collection lifecycle
- SearchEngine: Semantic, keyword, and hybrid search
- Integration: End-to-end workflows
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import after path setup
# pylint: disable=wrong-import-position
from vector_storage import (
    VectorStore,
    VectorDocument,
    CollectionManager,
    CollectionConfig,
    SearchEngine,
    SearchFilter,
    SearchResult,
)
# pylint: enable=wrong-import-position


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_vectors():
    """Sample embedding vectors."""
    return [
        [0.1] * 1536,
        [0.2] * 1536,
        [0.3] * 1536,
    ]


@pytest.fixture
def sample_documents(sample_vectors):
    """Sample vector documents."""
    return [
        VectorDocument(
            vector=sample_vectors[0],
            payload={
                "text": "The quick brown fox",
                "title": "Document 1",
                "category": "animals",
            },
            id="doc1",
        ),
        VectorDocument(
            vector=sample_vectors[1],
            payload={
                "text": "Python programming language",
                "title": "Document 2",
                "category": "tech",
            },
            id="doc2",
        ),
        VectorDocument(
            vector=sample_vectors[2],
            payload={
                "text": "Machine learning models",
                "title": "Document 3",
                "category": "tech",
            },
            id="doc3",
        ),
    ]


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client."""
    client = Mock()

    # Mock collections
    mock_collections = Mock()
    mock_collections.collections = []
    client.get_collections.return_value = mock_collections

    # Mock collection info
    mock_info = Mock()
    mock_info.status = "green"
    mock_info.vectors_count = 100
    mock_info.points_count = 100
    mock_info.segments_count = 1
    mock_info.config = Mock()
    mock_info.config.params = Mock()
    mock_info.config.params.vectors = Mock()
    mock_info.config.params.vectors.size = 1536
    mock_info.config.params.vectors.distance = Mock()
    mock_info.config.params.vectors.distance.name = "Cosine"
    mock_info.config.hnsw_config = Mock()
    mock_info.config.hnsw_config.m = 16
    mock_info.config.hnsw_config.ef_construct = 100
    mock_info.config.optimizer_config = Mock()
    mock_info.config.optimizer_config.indexing_threshold = 10000
    client.get_collection.return_value = mock_info

    # Mock operations
    client.create_collection.return_value = True
    client.delete_collection.return_value = True
    client.upsert.return_value = True
    client.delete.return_value = True

    # Mock search
    mock_point = Mock()
    mock_point.id = "doc1"
    mock_point.score = 0.95
    mock_point.payload = {"text": "Test", "title": "Test Doc"}
    mock_point.vector = None
    client.search.return_value = [mock_point]

    # Mock retrieve
    client.retrieve.return_value = [mock_point]

    # Mock scroll
    client.scroll.return_value = ([mock_point], None)

    # Mock count
    mock_count = Mock()
    mock_count.count = 1
    client.count.return_value = mock_count

    return client


# ============================================================================
# COLLECTION MANAGER TESTS
# ============================================================================


class TestCollectionManager:
    """Test CollectionManager class."""

    def test_initialization(self, mock_qdrant_client):
        """Test manager initialization."""
        manager = CollectionManager(
            client=mock_qdrant_client,
            default_vector_size=1536,
        )

        assert manager.client == mock_qdrant_client
        assert manager.default_vector_size == 1536

    def test_create_collection(self, mock_qdrant_client):
        """Test collection creation."""
        manager = CollectionManager(client=mock_qdrant_client)

        config = CollectionConfig(
            name="test_collection",
            vector_size=1536,
            distance="Cosine",
        )

        result = manager.create_collection(config)

        assert result is True
        mock_qdrant_client.create_collection.assert_called_once()

    def test_delete_collection(self, mock_qdrant_client):
        """Test collection deletion."""
        # Make collection exist
        mock_collection = Mock()
        mock_collection.name = "test_collection"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections

        manager = CollectionManager(client=mock_qdrant_client)
        result = manager.delete_collection("test_collection")

        assert result is True
        mock_qdrant_client.delete_collection.assert_called_once()

    def test_list_collections(self, mock_qdrant_client):
        """Test listing collections."""
        # Setup mock collections
        mock_col1 = Mock()
        mock_col1.name = "collection1"
        mock_col2 = Mock()
        mock_col2.name = "collection2"

        mock_collections = Mock()
        mock_collections.collections = [mock_col1, mock_col2]
        mock_qdrant_client.get_collections.return_value = mock_collections

        manager = CollectionManager(client=mock_qdrant_client)
        collections = manager.list_collections()

        assert len(collections) == 2
        assert "collection1" in collections
        assert "collection2" in collections

    def test_get_collection_info(self, mock_qdrant_client):
        """Test getting collection info."""
        # Make collection exist
        mock_collection = Mock()
        mock_collection.name = "test_collection"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections

        manager = CollectionManager(client=mock_qdrant_client)
        info = manager.get_collection_info("test_collection")

        assert info is not None
        assert info["name"] == "test_collection"
        assert info["vectors_count"] == 100
        assert info["config"]["vector_size"] == 1536


# ============================================================================
# SEARCH ENGINE TESTS
# ============================================================================


class TestSearchEngine:
    """Test SearchEngine class."""

    def test_initialization(self, mock_qdrant_client):
        """Test search engine initialization."""
        engine = SearchEngine(
            client=mock_qdrant_client,
            default_collection="documents",
        )

        assert engine.client == mock_qdrant_client
        assert engine.default_collection == "documents"

    def test_semantic_search(self, mock_qdrant_client, sample_vectors):
        """Test semantic search."""
        engine = SearchEngine(client=mock_qdrant_client)

        results = engine.semantic_search(
            query_vector=sample_vectors[0],
            limit=10,
        )

        assert len(results) > 0
        assert isinstance(results[0], SearchResult)
        mock_qdrant_client.search.assert_called_once()

    def test_search_with_filters(self, mock_qdrant_client, sample_vectors):
        """Test search with filters."""
        engine = SearchEngine(client=mock_qdrant_client)

        filters = [
            SearchFilter(field="category", value="tech", operator="match")
        ]

        results = engine.hybrid_search(
            query_vector=sample_vectors[0],
            filters=filters,
            limit=10,
        )

        assert isinstance(results, list)
        mock_qdrant_client.search.assert_called_once()

    def test_search_by_id(self, mock_qdrant_client):
        """Test search by ID."""
        engine = SearchEngine(client=mock_qdrant_client)

        result = engine.search_by_id("doc1")

        assert result is not None
        assert result.id == "doc1"
        mock_qdrant_client.retrieve.assert_called_once()

    def test_count_points(self, mock_qdrant_client):
        """Test counting points."""
        engine = SearchEngine(client=mock_qdrant_client)

        count = engine.count_points()

        assert count == 1
        mock_qdrant_client.count.assert_called_once()


# ============================================================================
# VECTOR STORE TESTS
# ============================================================================


class TestVectorStore:
    """Test VectorStore class."""

    def test_initialization(self, mock_qdrant_client):
        """Test vector store initialization."""
        with patch("vector_storage.vector_store.QdrantClient") as MockClient:
            MockClient.return_value = mock_qdrant_client

            store = VectorStore(
                host="localhost",
                port=6333,
                default_collection="documents",
            )

            assert store.default_collection == "documents"
            assert store.vector_size == 1536

    def test_insert_single_document(
        self, mock_qdrant_client, sample_documents
    ):
        """Test inserting single document."""
        with patch("vector_storage.vector_store.QdrantClient") as MockClient:
            MockClient.return_value = mock_qdrant_client

            store = VectorStore()
            result = store.insert(sample_documents[0])

            assert result is True
            mock_qdrant_client.upsert.assert_called_once()

    def test_insert_batch(self, mock_qdrant_client, sample_documents):
        """Test batch insert."""
        with patch("vector_storage.vector_store.QdrantClient") as MockClient:
            MockClient.return_value = mock_qdrant_client

            store = VectorStore()
            result = store.insert_batch(sample_documents)

            assert result is True
            assert store.stats["total_uploaded"] == 3
            mock_qdrant_client.upsert.assert_called()

    def test_semantic_search(self, mock_qdrant_client, sample_vectors):
        """Test semantic search."""
        with patch("vector_storage.vector_store.QdrantClient") as MockClient:
            MockClient.return_value = mock_qdrant_client

            store = VectorStore()
            results = store.semantic_search(
                query_vector=sample_vectors[0],
                limit=5,
            )

            assert isinstance(results, list)
            assert store.stats["total_searched"] == 1

    def test_hybrid_search(self, mock_qdrant_client, sample_vectors):
        """Test hybrid search."""
        with patch("vector_storage.vector_store.QdrantClient") as MockClient:
            MockClient.return_value = mock_qdrant_client

            store = VectorStore()
            filters = [
                SearchFilter(field="category", value="tech", operator="match")
            ]

            results = store.hybrid_search(
                query_vector=sample_vectors[0],
                filters=filters,
                limit=5,
            )

            assert isinstance(results, list)

    def test_get_by_id(self, mock_qdrant_client):
        """Test get by ID."""
        with patch("vector_storage.vector_store.QdrantClient") as MockClient:
            MockClient.return_value = mock_qdrant_client

            store = VectorStore()
            result = store.get_by_id("doc1")

            assert result is not None
            assert result.id == "doc1"

    def test_delete_document(self, mock_qdrant_client):
        """Test document deletion."""
        with patch("vector_storage.vector_store.QdrantClient") as MockClient:
            MockClient.return_value = mock_qdrant_client

            store = VectorStore()
            result = store.delete("doc1")

            assert result is True
            mock_qdrant_client.delete.assert_called_once()

    def test_delete_batch(self, mock_qdrant_client):
        """Test batch deletion."""
        with patch("vector_storage.vector_store.QdrantClient") as MockClient:
            MockClient.return_value = mock_qdrant_client

            store = VectorStore()
            result = store.delete_batch(["doc1", "doc2", "doc3"])

            assert result is True
            mock_qdrant_client.delete.assert_called_once()

    def test_count(self, mock_qdrant_client):
        """Test document count."""
        with patch("vector_storage.vector_store.QdrantClient") as MockClient:
            MockClient.return_value = mock_qdrant_client

            store = VectorStore()
            count = store.count()

            assert count == 1

    def test_get_stats(self, mock_qdrant_client):
        """Test statistics retrieval."""
        with patch("vector_storage.vector_store.QdrantClient") as MockClient:
            MockClient.return_value = mock_qdrant_client

            store = VectorStore()
            stats = store.get_stats()

            assert "total_uploaded" in stats
            assert "total_searched" in stats
            assert "collections" in stats


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_end_to_end_workflow(
        self, mock_qdrant_client, sample_documents, sample_vectors
    ):
        """Test complete workflow: insert, search, delete."""
        with patch("vector_storage.vector_store.QdrantClient") as MockClient:
            MockClient.return_value = mock_qdrant_client

            # Initialize store
            store = VectorStore()

            # Setup collection
            result = store.setup(recreate=False)
            assert result is True

            # Insert documents
            result = store.insert_batch(sample_documents)
            assert result is True

            # Semantic search
            results = store.semantic_search(
                query_vector=sample_vectors[0],
                limit=5,
            )
            assert isinstance(results, list)

            # Hybrid search
            filters = [
                SearchFilter(field="category", value="tech", operator="match")
            ]
            results = store.hybrid_search(
                query_vector=sample_vectors[0],
                filters=filters,
            )
            assert isinstance(results, list)

            # Get by ID
            result = store.get_by_id("doc1")
            assert result is not None

            # Count
            count = store.count()
            assert count >= 0

            # Delete
            result = store.delete("doc1")
            assert result is True

            # Get stats
            stats = store.get_stats()
            assert stats["total_uploaded"] == 3
            assert stats["total_searched"] >= 2


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v", "--tb=short"])
