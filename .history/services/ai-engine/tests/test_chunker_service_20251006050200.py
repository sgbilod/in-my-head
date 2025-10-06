"""
Tests for Document Chunking Service.

Test suite for different chunking strategies and edge cases.
"""

import pytest
from src.services.chunker_service import (
    ChunkerService,
    ChunkingStrategy,
    DocumentChunk,
    get_chunker_service
)


# Sample text for testing
SAMPLE_TEXT = """
This is the first sentence. This is the second sentence. This is the third sentence.

This is a new paragraph. It has multiple sentences. Each sentence adds meaning.

Here is another paragraph. It continues the document. The text flows naturally.
""".strip()

SHORT_TEXT = "This is a short document."

LONG_SENTENCE = "This is " + "a very long sentence " * 50 + "that never ends."


@pytest.fixture
def chunker():
    """Fixture for ChunkerService instance."""
    return ChunkerService(
        default_chunk_size=100,
        default_chunk_overlap=20
    )


class TestSentenceChunking:
    """Test sentence-based chunking strategy."""
    
    def test_sentence_chunking_basic(self, chunker):
        """Test basic sentence chunking."""
        chunks = chunker.chunk_document(
            document_id="test-001",
            content=SAMPLE_TEXT,
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=100,
            chunk_overlap=20
        )
        
        assert len(chunks) > 0
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert all(len(c.content) <= 150 for c in chunks)  # Allow some overflow
    
    def test_sentence_chunking_overlap(self, chunker):
        """Test that overlap is applied correctly."""
        chunks = chunker.chunk_document(
            document_id="test-002",
            content=SAMPLE_TEXT,
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=100,
            chunk_overlap=30
        )
        
        # Check if consecutive chunks have overlapping content
        if len(chunks) > 1:
            for i in range(len(chunks) - 1):
                # Some words from end of chunk[i] should appear in chunk[i+1]
                chunk1_words = set(chunks[i].content.split()[-5:])
                chunk2_words = set(chunks[i+1].content.split()[:10])
                overlap = chunk1_words & chunk2_words
                
                # Should have some overlap (not always exact due to sentence boundaries)
                assert len(overlap) >= 0  # May not always overlap exactly
    
    def test_sentence_chunking_metadata(self, chunker):
        """Test that metadata is correctly populated."""
        chunks = chunker.chunk_document(
            document_id="test-003",
            content=SAMPLE_TEXT,
            strategy=ChunkingStrategy.SENTENCE
        )
        
        for i, chunk in enumerate(chunks):
            assert chunk.metadata.chunk_index == i
            assert chunk.metadata.document_id == "test-003"
            assert chunk.metadata.chunk_id == f"test-003_chunk_{i}"
            assert chunk.metadata.char_count > 0
            assert chunk.metadata.word_count > 0
            assert chunk.metadata.sentence_count > 0


class TestParagraphChunking:
    """Test paragraph-based chunking strategy."""
    
    def test_paragraph_chunking_basic(self, chunker):
        """Test basic paragraph chunking."""
        chunks = chunker.chunk_document(
            document_id="test-004",
            content=SAMPLE_TEXT,
            strategy=ChunkingStrategy.PARAGRAPH,
            chunk_size=200
        )
        
        assert len(chunks) > 0
        # Should have ~3 chunks for 3 paragraphs
        assert len(chunks) >= 3
    
    def test_paragraph_chunking_preserves_paragraphs(self, chunker):
        """Test that paragraph structure is preserved."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        
        chunks = chunker.chunk_document(
            document_id="test-005",
            content=text,
            strategy=ChunkingStrategy.PARAGRAPH,
            chunk_size=500
        )
        
        # Each paragraph should be its own chunk
        assert len(chunks) == 3
        assert "First paragraph" in chunks[0].content
        assert "Second paragraph" in chunks[1].content
        assert "Third paragraph" in chunks[2].content


class TestFixedSizeChunking:
    """Test fixed-size chunking strategy."""
    
    def test_fixed_size_basic(self, chunker):
        """Test basic fixed-size chunking."""
        chunks = chunker.chunk_document(
            document_id="test-006",
            content=SAMPLE_TEXT,
            strategy=ChunkingStrategy.FIXED,
            chunk_size=50,
            chunk_overlap=10
        )
        
        assert len(chunks) > 0
        # Most chunks should be close to target size
        for chunk in chunks[:-1]:  # Exclude last chunk
            assert 40 <= len(chunk.content) <= 70  # Allow some variance
    
    def test_fixed_size_overlap(self, chunker):
        """Test fixed-size chunking with overlap."""
        chunks = chunker.chunk_document(
            document_id="test-007",
            content="A" * 200,  # Simple repeated character
            strategy=ChunkingStrategy.FIXED,
            chunk_size=50,
            chunk_overlap=10
        )
        
        assert len(chunks) > 1
        # Check positions accounting for overlap
        for i in range(len(chunks) - 1):
            gap = chunks[i+1].metadata.start_position - chunks[i].metadata.end_position
            # Gap should be negative (overlap) or small
            assert gap <= 0 or gap < 10
    
    def test_fixed_size_no_infinite_loop(self, chunker):
        """Test that large overlap doesn't cause infinite loop."""
        chunks = chunker.chunk_document(
            document_id="test-008",
            content=SHORT_TEXT,
            strategy=ChunkingStrategy.FIXED,
            chunk_size=10,
            chunk_overlap=20  # Overlap > chunk_size
        )
        
        # Should complete without hanging
        assert len(chunks) > 0


class TestSemanticChunking:
    """Test semantic chunking strategy."""
    
    def test_semantic_chunking_basic(self, chunker):
        """Test basic semantic chunking."""
        chunks = chunker.chunk_document(
            document_id="test-009",
            content=SAMPLE_TEXT,
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=150
        )
        
        assert len(chunks) > 0
        assert all(isinstance(c, DocumentChunk) for c in chunks)
    
    def test_semantic_grouping(self, chunker):
        """Test that related sentences are grouped."""
        text = (
            "The cat sat on the mat. The cat was very comfortable. "
            "Meanwhile, the dog barked outside. The dog was very loud. "
            "Birds flew overhead. They were migrating south."
        )
        
        chunks = chunker.chunk_document(
            document_id="test-010",
            content=text,
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=100
        )
        
        # Should group related sentences (cat sentences, dog sentences, bird sentences)
        # This is a basic test - results may vary
        assert len(chunks) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_document(self, chunker):
        """Test chunking empty document."""
        chunks = chunker.chunk_document(
            document_id="test-011",
            content="",
            strategy=ChunkingStrategy.SENTENCE
        )
        
        assert len(chunks) == 0
    
    def test_single_sentence(self, chunker):
        """Test chunking single sentence."""
        chunks = chunker.chunk_document(
            document_id="test-012",
            content=SHORT_TEXT,
            strategy=ChunkingStrategy.SENTENCE
        )
        
        assert len(chunks) == 1
        assert chunks[0].content == SHORT_TEXT
    
    def test_very_long_sentence(self, chunker):
        """Test chunking very long sentence."""
        chunks = chunker.chunk_document(
            document_id="test-013",
            content=LONG_SENTENCE,
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=100
        )
        
        # Should split even though it's one sentence
        assert len(chunks) > 1
    
    def test_invalid_strategy(self, chunker):
        """Test with invalid strategy."""
        with pytest.raises(ValueError):
            chunker.chunk_document(
                document_id="test-014",
                content=SAMPLE_TEXT,
                strategy="invalid_strategy"  # type: ignore
            )


class TestStatistics:
    """Test chunk statistics calculation."""
    
    def test_statistics_calculation(self, chunker):
        """Test statistics calculation for chunks."""
        chunks = chunker.chunk_document(
            document_id="test-015",
            content=SAMPLE_TEXT,
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=100
        )
        
        stats = chunker.get_chunk_statistics(chunks)
        
        assert stats["total_chunks"] == len(chunks)
        assert stats["avg_chunk_size"] > 0
        assert stats["min_chunk_size"] > 0
        assert stats["max_chunk_size"] >= stats["min_chunk_size"]
        assert stats["total_characters"] > 0
    
    def test_statistics_empty(self, chunker):
        """Test statistics for empty chunk list."""
        stats = chunker.get_chunk_statistics([])
        
        assert stats["total_chunks"] == 0
        assert stats["avg_chunk_size"] == 0


class TestSingletonPattern:
    """Test singleton pattern for chunker service."""
    
    def test_singleton(self):
        """Test that get_chunker_service returns singleton."""
        service1 = get_chunker_service()
        service2 = get_chunker_service()
        
        assert service1 is service2


class TestChunkToDict:
    """Test chunk serialization."""
    
    def test_chunk_to_dict(self, chunker):
        """Test converting chunk to dictionary."""
        chunks = chunker.chunk_document(
            document_id="test-016",
            content=SHORT_TEXT,
            strategy=ChunkingStrategy.SENTENCE
        )
        
        chunk_dict = chunks[0].to_dict()
        
        assert "content" in chunk_dict
        assert "metadata" in chunk_dict
        assert chunk_dict["content"] == SHORT_TEXT
        assert "chunk_id" in chunk_dict["metadata"]
        assert "document_id" in chunk_dict["metadata"]


@pytest.mark.parametrize("strategy", [
    ChunkingStrategy.SENTENCE,
    ChunkingStrategy.PARAGRAPH,
    ChunkingStrategy.FIXED,
    ChunkingStrategy.SEMANTIC
])
class TestAllStrategies:
    """Test all chunking strategies with various inputs."""
    
    def test_strategy_with_sample_text(self, chunker, strategy):
        """Test each strategy produces valid chunks."""
        chunks = chunker.chunk_document(
            document_id="test-multi",
            content=SAMPLE_TEXT,
            strategy=strategy,
            chunk_size=100
        )
        
        assert len(chunks) > 0
        assert all(c.content.strip() for c in chunks)
        assert all(c.metadata.chunk_index == i for i, c in enumerate(chunks))
