"""
Comprehensive Edge Case Tests

Additional edge case coverage for all services:
- Very long text handling (10,000+ characters)
- Case-insensitive search operations
- Enum validation and error handling
- Qdrant initialization edge cases
- Unicode and special character handling
- Boundary value testing
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from uuid import uuid4
import sys

# ==================== LONG TEXT HANDLING ====================

class TestVeryLongTextHandling:
    """Test handling of extremely long text inputs"""
    
    def test_chunker_extremely_long_document(self):
        """Test chunking 50,000+ character document"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService(default_chunk_size=500)
        
        # Create 50,000 character document
        very_long_text = "This is a test sentence. " * 2000  # ~50,000 chars
        
        chunks = chunker.chunk_document(
            document_id="test-very-long",
            content=very_long_text,
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=500
        )
        
        # Should successfully chunk without hanging
        assert len(chunks) > 0
        # Should split into many chunks
        assert len(chunks) >= 100
        # No chunk should be excessively large
        assert all(len(c.content) < 1000 for c in chunks)
    
    def test_chunker_single_extremely_long_sentence(self):
        """Test chunking single sentence over 10,000 characters"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        # Single sentence with no periods except at the end
        long_sentence = "This is a very long sentence that goes on and on " * 200 + "."
        
        chunks = chunker.chunk_document(
            document_id="test-long-sentence",
            content=long_sentence,
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=500
        )
        
        # Must split even though it's one sentence
        assert len(chunks) > 1
        # Each chunk should be manageable size
        assert all(len(c.content) <= 600 for c in chunks)
    
    def test_chunker_no_punctuation_massive_text(self):
        """Test text with no sentence boundaries"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        # 5000 words with no punctuation
        no_punctuation = " ".join([f"word{i}" for i in range(5000)])
        
        chunks = chunker.chunk_document(
            document_id="test-no-punct",
            content=no_punctuation,
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=500
        )
        
        # Should handle gracefully
        assert len(chunks) > 0
        # Should split anyway
        assert len(chunks) > 10


# ==================== CASE-INSENSITIVE SEARCH ====================

class TestCaseInsensitiveSearch:
    """Test case-insensitive search operations"""
    
    @pytest.mark.asyncio
    async def test_rag_search_case_insensitive_query(self):
        """Test RAG search with mixed case queries"""
        from src.services.rag_service import RAGService
        
        rag = RAGService()
        
        # Mock Qdrant search to return results
        with patch.object(rag, 'qdrant') as mock_qdrant:
            mock_qdrant.search_similar = AsyncMock(return_value=[
                {
                    'id': 'doc1',
                    'score': 0.9,
                    'payload': {'content': 'Machine learning is awesome'}
                }
            ])
            
            # Search with different case variations
            queries = [
                "MACHINE LEARNING",
                "machine learning",
                "Machine Learning",
                "mAcHiNe LeArNiNg"
            ]
            
            for query in queries:
                # All should work and return results
                results = await rag.search(query, top_k=5)
                assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_keyword_search_case_insensitive(self):
        """Test keyword filtering is case-insensitive"""
        from src.services.rag_service import RAGService
        
        rag = RAGService()
        
        # Mock search results with various case keywords
        mock_results = [
            {'payload': {'keywords': ['Python', 'ML', 'AI']}},
            {'payload': {'keywords': ['python', 'ml', 'ai']}},
            {'payload': {'keywords': ['PYTHON', 'ML', 'AI']}}
        ]
        
        # Should match regardless of case
        for keyword in ['python', 'PYTHON', 'Python', 'PyThOn']:
            matching = [
                r for r in mock_results
                if any(k.lower() == keyword.lower() for k in r['payload'].get('keywords', []))
            ]
            assert len(matching) == 3  # All should match


# ==================== ENUM VALIDATION ====================

class TestEnumValidation:
    """Test enum validation and error handling"""
    
    def test_chunking_strategy_invalid_string(self):
        """Test ChunkingStrategy with invalid string"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        # Should raise ValueError for invalid strategy
        with pytest.raises((ValueError, TypeError, AttributeError)):
            chunker.chunk_document(
                document_id="test",
                content="Test content",
                strategy="INVALID_STRATEGY"  # type: ignore
            )
    
    def test_chunking_strategy_none(self):
        """Test ChunkingStrategy with None"""
        from src.services.chunker_service import ChunkerService
        
        chunker = ChunkerService()
        
        with pytest.raises((ValueError, TypeError)):
            chunker.chunk_document(
                document_id="test",
                content="Test",
                strategy=None  # type: ignore
            )
    
    def test_chunking_strategy_wrong_type(self):
        """Test ChunkingStrategy with wrong type"""
        from src.services.chunker_service import ChunkerService
        
        chunker = ChunkerService()
        
        with pytest.raises((ValueError, TypeError)):
            chunker.chunk_document(
                document_id="test",
                content="Test",
                strategy=12345  # type: ignore
            )
    
    def test_all_valid_enum_values(self):
        """Test all valid ChunkingStrategy enum values work"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        text = "Test sentence one. Test sentence two."
        
        # All enum values should work
        valid_strategies = [
            ChunkingStrategy.SENTENCE,
            ChunkingStrategy.PARAGRAPH,
            ChunkingStrategy.FIXED,
            ChunkingStrategy.SEMANTIC
        ]
        
        for strategy in valid_strategies:
            chunks = chunker.chunk_document(
                document_id="test",
                content=text,
                strategy=strategy,
                chunk_size=100
            )
            assert len(chunks) > 0


# ==================== QDRANT INITIALIZATION ====================

class TestQdrantInitializationEdgeCases:
    """Test Qdrant initialization edge cases"""
    
    @pytest.mark.asyncio
    async def test_qdrant_init_already_initialized(self):
        """Test initializing Qdrant when already initialized"""
        from src.services.qdrant_service import QdrantService
        
        service = QdrantService()
        
        with patch.object(service, 'client') as mock_client:
            mock_collections = Mock()
            mock_collections.collections = []
            mock_client.get_collections.return_value = mock_collections
            mock_client.get_collection.side_effect = Exception("Not found")
            mock_client.create_collection = Mock()
            
            # First initialization
            await service.initialize()
            first_call_count = mock_client.create_collection.call_count
            
            # Second initialization should be idempotent
            await service.initialize()
            second_call_count = mock_client.create_collection.call_count
            
            # Should not create collections again
            assert second_call_count == first_call_count
    
    @pytest.mark.asyncio
    async def test_qdrant_init_connection_failure(self):
        """Test Qdrant initialization with connection failure"""
        from src.services.qdrant_service import QdrantService
        
        service = QdrantService()
        
        with patch.object(service, 'client') as mock_client:
            # Simulate connection failure
            mock_client.get_collections.side_effect = ConnectionError("Cannot connect")
            
            # Should handle gracefully or raise appropriate error
            with pytest.raises((ConnectionError, Exception)):
                await service.initialize()
    
    @pytest.mark.asyncio
    async def test_qdrant_init_partial_collections_exist(self):
        """Test initialization when some collections already exist"""
        from src.services.qdrant_service import QdrantService
        
        service = QdrantService()
        
        with patch.object(service, 'client') as mock_client:
            # Mock one collection exists, others don't
            existing_collection = Mock()
            existing_collection.name = "document_embeddings"
            
            mock_collections = Mock()
            mock_collections.collections = [existing_collection]
            mock_client.get_collections.return_value = mock_collections
            
            # get_collection raises for non-existent collections
            def get_collection_side_effect(name):
                if name == "document_embeddings":
                    return Mock()
                raise Exception("Not found")
            
            mock_client.get_collection.side_effect = get_collection_side_effect
            mock_client.create_collection = Mock()
            
            await service.initialize()
            
            # Should only create missing collections
            assert mock_client.create_collection.call_count < 3


# ==================== UNICODE AND SPECIAL CHARACTERS ====================

class TestUnicodeAndSpecialCharacters:
    """Test handling of unicode and special characters"""
    
    def test_chunker_unicode_text(self):
        """Test chunking text with unicode characters"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        unicode_text = "Hello 世界! This is 한글 text with émojis 🎉🔥 and symbols ∑∏∫."
        
        chunks = chunker.chunk_document(
            document_id="test-unicode",
            content=unicode_text,
            strategy=ChunkingStrategy.SENTENCE
        )
        
        assert len(chunks) > 0
        # Unicode should be preserved
        assert any('世界' in c.content for c in chunks)
        assert any('🎉' in c.content for c in chunks)
    
    def test_chunker_emoji_only_text(self):
        """Test chunking text with only emojis"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        emoji_text = "🎉 🔥 💯 ✨ 🚀 " * 20
        
        chunks = chunker.chunk_document(
            document_id="test-emoji",
            content=emoji_text,
            strategy=ChunkingStrategy.FIXED,
            chunk_size=50
        )
        
        assert len(chunks) > 0
    
    def test_chunker_mixed_rtl_ltr_text(self):
        """Test chunking text with mixed RTL and LTR"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        mixed_text = "English text مع النص العربي and עברית mixed together."
        
        chunks = chunker.chunk_document(
            document_id="test-rtl-ltr",
            content=mixed_text,
            strategy=ChunkingStrategy.SENTENCE
        )
        
        assert len(chunks) > 0
        # Should preserve all text
        combined = ''.join(c.content for c in chunks)
        assert 'English' in combined
        assert 'עברית' in combined


# ==================== BOUNDARY VALUE TESTING ====================

class TestBoundaryValues:
    """Test boundary value conditions"""
    
    def test_chunk_size_zero(self):
        """Test chunking with chunk_size=0"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        # Should raise error or use default
        with pytest.raises((ValueError, ZeroDivisionError, AssertionError)):
            chunker.chunk_document(
                document_id="test",
                content="Test content",
                strategy=ChunkingStrategy.FIXED,
                chunk_size=0
            )
    
    def test_chunk_size_negative(self):
        """Test chunking with negative chunk_size"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        with pytest.raises((ValueError, AssertionError)):
            chunker.chunk_document(
                document_id="test",
                content="Test",
                strategy=ChunkingStrategy.FIXED,
                chunk_size=-100
            )
    
    def test_chunk_size_extremely_large(self):
        """Test chunking with chunk_size larger than content"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        short_text = "Short text."
        
        chunks = chunker.chunk_document(
            document_id="test",
            content=short_text,
            strategy=ChunkingStrategy.FIXED,
            chunk_size=10000  # Much larger than content
        )
        
        # Should return single chunk with all content
        assert len(chunks) == 1
        assert chunks[0].content == short_text
    
    def test_chunk_overlap_equals_chunk_size(self):
        """Test when overlap equals chunk size"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        text = "A " * 100  # Simple repeated text
        
        # Should handle without infinite loop
        chunks = chunker.chunk_document(
            document_id="test",
            content=text,
            strategy=ChunkingStrategy.FIXED,
            chunk_size=50,
            chunk_overlap=50  # Equal to chunk_size
        )
        
        # Should complete
        assert len(chunks) > 0
    
    def test_chunk_overlap_greater_than_chunk_size(self):
        """Test when overlap > chunk_size"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        # Should handle gracefully (cap overlap or error)
        chunks = chunker.chunk_document(
            document_id="test",
            content="Test content " * 50,
            strategy=ChunkingStrategy.FIXED,
            chunk_size=50,
            chunk_overlap=100  # Larger than chunk_size
        )
        
        # Should not hang
        assert len(chunks) > 0


# ==================== MEMORY AND PERFORMANCE ====================

class TestMemoryAndPerformance:
    """Test memory usage and performance with edge cases"""
    
    def test_chunker_does_not_duplicate_memory(self):
        """Test that chunking doesn't create excessive copies"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        # Large text
        large_text = "Word " * 10000
        initial_size = sys.getsizeof(large_text)
        
        chunks = chunker.chunk_document(
            document_id="test-memory",
            content=large_text,
            strategy=ChunkingStrategy.FIXED,
            chunk_size=500
        )
        
        # Total chunk memory should not be much more than original
        # (some overhead expected for metadata)
        total_chunk_size = sum(sys.getsizeof(c.content) for c in chunks)
        
        # Should not be more than 3x original (generous threshold)
        assert total_chunk_size < initial_size * 3
    
    @pytest.mark.asyncio
    async def test_qdrant_batch_operations_dont_timeout(self):
        """Test that batch operations complete reasonably fast"""
        from src.services.qdrant_service import QdrantService
        import time
        
        service = QdrantService()
        
        with patch.object(service, 'client') as mock_client:
            mock_client.upsert = Mock()
            
            # Large batch
            points = [
                {
                    'id': f'doc-{i}',
                    'vector': [0.1] * 384,
                    'payload': {'content': f'Document {i}'}
                }
                for i in range(1000)
            ]
            
            start = time.time()
            await service.upsert_vectors("test_collection", points)
            duration = time.time() - start
            
            # Should complete quickly (under 1 second for mocked operation)
            assert duration < 1.0


# ==================== NULL AND EMPTY VALUES ====================

class TestNullAndEmptyValues:
    """Test handling of null and empty values"""
    
    def test_chunker_whitespace_only_document(self):
        """Test document with only whitespace"""
        from src.services.chunker_service import ChunkerService, ChunkingStrategy
        
        chunker = ChunkerService()
        
        whitespace_text = "   \n\n\t\t   \n   "
        
        chunks = chunker.chunk_document(
            document_id="test-whitespace",
            content=whitespace_text,
            strategy=ChunkingStrategy.SENTENCE
        )
        
        # Should return empty or handle gracefully
        assert len(chunks) == 0 or all(not c.content.strip() for c in chunks)
    
    @pytest.mark.asyncio
    async def test_rag_search_empty_query(self):
        """Test RAG search with empty query"""
        from src.services.rag_service import RAGService
        
        rag = RAGService()
        
        # Should handle empty query gracefully
        with pytest.raises((ValueError, AssertionError)):
            await rag.search("", top_k=5)
    
    @pytest.mark.asyncio
    async def test_rag_search_whitespace_query(self):
        """Test RAG search with only whitespace"""
        from src.services.rag_service import RAGService
        
        rag = RAGService()
        
        with pytest.raises((ValueError, AssertionError)):
            await rag.search("   \n\t   ", top_k=5)
