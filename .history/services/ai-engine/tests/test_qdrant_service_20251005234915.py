"""
Tests for Qdrant Service.

Test suite for vector database operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from qdrant_client.models import Distance

from src.services.qdrant_service import QdrantService, get_qdrant_service
from src.config import settings


@pytest.fixture
def qdrant_service():
    """Fixture for QdrantService instance."""
    return QdrantService()


@pytest.fixture
def mock_qdrant_client():
    """Fixture for mocked Qdrant client."""
    with patch('src.services.qdrant_service.QdrantClient') as mock:
        yield mock


class TestQdrantService:
    """Test suite for QdrantService class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, qdrant_service, mock_qdrant_client):
        """Test service initialization creates collections."""
        # Mock get_collections response
        mock_collections = Mock()
        mock_collections.collections = []
        qdrant_service.client.get_collections.return_value = mock_collections
        
        # Mock get_collection to raise exception (collection doesn't exist)
        qdrant_service.client.get_collection.side_effect = Exception("Not found")
        
        # Initialize service
        await qdrant_service.initialize()
        
        # Verify initialization
        assert qdrant_service._initialized is True
        assert qdrant_service.client.create_collection.call_count == 3
    
    @pytest.mark.asyncio
    async def test_upsert_vectors(self, qdrant_service):
        """Test upserting vectors to collection."""
        points = [
            {
                "id": "doc-1",
                "vector": [0.1] * 384,
                "payload": {"title": "Test Doc"}
            }
        ]
        
        # Mock upsert
        qdrant_service.client.upsert = Mock()
        
        # Execute upsert
        await qdrant_service.upsert_vectors("test_collection", points)
        
        # Verify upsert was called
        qdrant_service.client.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_similar(self, qdrant_service):
        """Test similarity search."""
        query_vector = [0.5] * 384
        
        # Mock search results
        mock_result = Mock()
        mock_result.id = "doc-1"
        mock_result.score = 0.95
        mock_result.payload = {"title": "Test Doc"}
        
        qdrant_service.client.search = Mock(return_value=[mock_result])
        
        # Execute search
        results = await qdrant_service.search_similar(
            "test_collection",
            query_vector,
            limit=5
        )
        
        # Verify results
        assert len(results) == 1
        assert results[0]["id"] == "doc-1"
        assert results[0]["score"] == 0.95
        assert "title" in results[0]["payload"]
    
    @pytest.mark.asyncio
    async def test_delete_vectors(self, qdrant_service):
        """Test deleting vectors."""
        point_ids = ["doc-1", "doc-2"]
        
        # Mock delete
        qdrant_service.client.delete = Mock()
        
        # Execute delete
        await qdrant_service.delete_vectors("test_collection", point_ids)
        
        # Verify delete was called
        qdrant_service.client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_collection_info(self, qdrant_service):
        """Test getting collection information."""
        # Mock collection info
        mock_info = Mock()
        mock_info.vectors_count = 100
        mock_info.points_count = 100
        mock_info.segments_count = 1
        mock_info.status.name = "GREEN"
        mock_info.optimizer_status.name = "OK"
        mock_info.indexed_vectors_count = 100
        
        qdrant_service.client.get_collection = Mock(return_value=mock_info)
        
        # Get collection info
        info = await qdrant_service.get_collection_info("test_collection")
        
        # Verify info
        assert info["name"] == "test_collection"
        assert info["vectors_count"] == 100
        assert info["status"] == "GREEN"
    
    def test_singleton_pattern(self):
        """Test that get_qdrant_service returns singleton."""
        service1 = get_qdrant_service()
        service2 = get_qdrant_service()
        
        assert service1 is service2


@pytest.mark.integration
class TestQdrantIntegration:
    """Integration tests requiring actual Qdrant instance."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow: create, insert, search, delete."""
        # Skip if Qdrant not available
        pytest.skip("Requires running Qdrant instance")
        
        # This test would run against actual Qdrant
        # Useful for CI/CD with Docker Compose
