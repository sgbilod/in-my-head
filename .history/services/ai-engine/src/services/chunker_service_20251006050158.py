"""
Document Chunking Service.

Provides intelligent document chunking strategies for RAG:
- Sentence-based: Respects sentence boundaries
- Paragraph-based: Preserves paragraph structure
- Fixed-size: Fixed character/token count with overlap
- Semantic: Groups semantically related sentences

Each strategy balances chunk size, semantic coherence, and context preservation.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import nltk

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

from nltk.tokenize import sent_tokenize, word_tokenize

logger = logging.getLogger(__name__)


class ChunkingStrategy(str, Enum):
    """Available chunking strategies."""
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    FIXED = "fixed"
    SEMANTIC = "semantic"


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""
    chunk_id: str
    document_id: str
    chunk_index: int
    start_position: int
    end_position: int
    sentence_count: int = 0
    word_count: int = 0
    char_count: int = 0
    tokens: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "sentence_count": self.sentence_count,
            "word_count": self.word_count,
            "char_count": self.char_count
        }


@dataclass
class DocumentChunk:
    """A chunk of a document with metadata."""
    content: str
    metadata: ChunkMetadata
    
    def __post_init__(self):
        """Calculate statistics after initialization."""
        if not self.metadata.char_count:
            self.metadata.char_count = len(self.content)
        if not self.metadata.word_count:
            words = word_tokenize(self.content)
            self.metadata.word_count = len(words)
            self.metadata.tokens = words
        if not self.metadata.sentence_count:
            sentences = sent_tokenize(self.content)
            self.metadata.sentence_count = len(sentences)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "metadata": self.metadata.to_dict()
        }


class ChunkerService:
    """
    Service for chunking documents with multiple strategies.
    
    Strategies:
    1. Sentence-based: Respects sentence boundaries, combines sentences
    2. Paragraph-based: Preserves paragraph structure
    3. Fixed-size: Fixed character count with overlap
    4. Semantic: Groups semantically related sentences (basic implementation)
    """
    
    def __init__(
        self,
        default_chunk_size: int = 500,
        default_chunk_overlap: int = 50,
        preserve_sentences: bool = True
    ):
        """
        Initialize chunker service.
        
        Args:
            default_chunk_size: Target chunk size in characters
            default_chunk_overlap: Overlap between chunks in characters
            preserve_sentences: Whether to preserve sentence boundaries
        """
        self.default_chunk_size = default_chunk_size
        self.default_chunk_overlap = default_chunk_overlap
        self.preserve_sentences = preserve_sentences
        
        logger.info(
            f"Chunker initialized: size={default_chunk_size}, "
            f"overlap={default_chunk_overlap}, preserve_sentences={preserve_sentences}"
        )
    
    def chunk_document(
        self,
        document_id: str,
        content: str,
        strategy: ChunkingStrategy = ChunkingStrategy.SENTENCE,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[DocumentChunk]:
        """
        Chunk a document using the specified strategy.
        
        Args:
            document_id: Unique document identifier
            content: Document content to chunk
            strategy: Chunking strategy to use
            chunk_size: Override default chunk size
            chunk_overlap: Override default chunk overlap
        
        Returns:
            List of DocumentChunk objects
        """
        chunk_size = chunk_size or self.default_chunk_size
        chunk_overlap = chunk_overlap or self.default_chunk_overlap
        
        logger.info(
            f"Chunking document {document_id} with strategy={strategy.value}, "
            f"size={chunk_size}, overlap={chunk_overlap}"
        )
        
        # Select chunking method
        if strategy == ChunkingStrategy.SENTENCE:
            chunks = self._chunk_by_sentences(
                document_id, content, chunk_size, chunk_overlap
            )
        elif strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraphs(
                document_id, content, chunk_size
            )
        elif strategy == ChunkingStrategy.FIXED:
            chunks = self._chunk_fixed_size(
                document_id, content, chunk_size, chunk_overlap
            )
        elif strategy == ChunkingStrategy.SEMANTIC:
            chunks = self._chunk_semantic(
                document_id, content, chunk_size
            )
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
        
        logger.info(
            f"Created {len(chunks)} chunks for document {document_id}"
        )
        
        return chunks
    
    def _chunk_by_sentences(
        self,
        document_id: str,
        content: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[DocumentChunk]:
        """
        Chunk by sentences, respecting sentence boundaries.
        
        Combines sentences until target size is reached, then starts new chunk
        with overlap from previous chunk.
        """
        # Split into sentences
        sentences = sent_tokenize(content)
        
        chunks = []
        current_chunk = []
        current_size = 0
        current_position = 0
        
        for sentence in sentences:
            sentence_len = len(sentence)
            
            # If adding this sentence exceeds chunk size and we have content
            if current_size + sentence_len > chunk_size and current_chunk:
                # Create chunk from accumulated sentences
                chunk_text = " ".join(current_chunk)
                chunk_start = current_position
                chunk_end = chunk_start + len(chunk_text)
                
                chunk = DocumentChunk(
                    content=chunk_text,
                    metadata=ChunkMetadata(
                        chunk_id=f"{document_id}_chunk_{len(chunks)}",
                        document_id=document_id,
                        chunk_index=len(chunks),
                        start_position=chunk_start,
                        end_position=chunk_end
                    )
                )
                chunks.append(chunk)
                
                # Handle overlap: keep last few sentences
                if chunk_overlap > 0:
                    overlap_text = ""
                    overlap_sentences = []
                    
                    # Work backwards from end of chunk
                    for prev_sentence in reversed(current_chunk):
                        test_overlap = " ".join(
                            [prev_sentence] + overlap_sentences
                        )
                        if len(test_overlap) <= chunk_overlap:
                            overlap_sentences.insert(0, prev_sentence)
                            overlap_text = test_overlap
                        else:
                            break
                    
                    # Start new chunk with overlap
                    current_chunk = overlap_sentences
                    current_size = len(overlap_text)
                    current_position = chunk_end - current_size
                else:
                    current_chunk = []
                    current_size = 0
                    current_position = chunk_end
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_size += sentence_len + 1  # +1 for space
        
        # Add final chunk if any content remains
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_start = current_position
            chunk_end = chunk_start + len(chunk_text)
            
            chunk = DocumentChunk(
                content=chunk_text,
                metadata=ChunkMetadata(
                    chunk_id=f"{document_id}_chunk_{len(chunks)}",
                    document_id=document_id,
                    chunk_index=len(chunks),
                    start_position=chunk_start,
                    end_position=chunk_end
                )
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_by_paragraphs(
        self,
        document_id: str,
        content: str,
        chunk_size: int
    ) -> List[DocumentChunk]:
        """
        Chunk by paragraphs, preserving paragraph structure.
        
        Each paragraph becomes a chunk. If a paragraph exceeds chunk_size,
        it's split using sentence-based chunking.
        """
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', content)
        
        chunks = []
        current_position = 0
        
        for para_index, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If paragraph is within size limit, make it a chunk
            if len(paragraph) <= chunk_size:
                chunk = DocumentChunk(
                    content=paragraph,
                    metadata=ChunkMetadata(
                        chunk_id=f"{document_id}_chunk_{len(chunks)}",
                        document_id=document_id,
                        chunk_index=len(chunks),
                        start_position=current_position,
                        end_position=current_position + len(paragraph)
                    )
                )
                chunks.append(chunk)
                current_position += len(paragraph) + 2  # +2 for \n\n
            else:
                # Paragraph too large, split by sentences
                para_chunks = self._chunk_by_sentences(
                    document_id,
                    paragraph,
                    chunk_size,
                    chunk_overlap=0  # No overlap within paragraphs
                )
                
                # Adjust positions and IDs
                for para_chunk in para_chunks:
                    para_chunk.metadata.chunk_id = (
                        f"{document_id}_chunk_{len(chunks)}"
                    )
                    para_chunk.metadata.chunk_index = len(chunks)
                    para_chunk.metadata.start_position += current_position
                    para_chunk.metadata.end_position += current_position
                    chunks.append(para_chunk)
                
                current_position += len(paragraph) + 2
        
        return chunks
    
    def _chunk_fixed_size(
        self,
        document_id: str,
        content: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[DocumentChunk]:
        """
        Chunk with fixed character size and overlap.
        
        Optionally respects sentence boundaries if preserve_sentences=True.
        """
        chunks = []
        current_position = 0
        
        while current_position < len(content):
            # Calculate chunk end position
            chunk_end = min(
                current_position + chunk_size,
                len(content)
            )
            
            # Extract chunk text
            chunk_text = content[current_position:chunk_end]
            
            # If preserve_sentences and not at end, try to end at sentence
            if (
                self.preserve_sentences
                and chunk_end < len(content)
                and len(chunk_text) > 50  # Only for reasonable size
            ):
                # Find last sentence boundary
                last_period = chunk_text.rfind('.')
                last_question = chunk_text.rfind('?')
                last_exclaim = chunk_text.rfind('!')
                
                last_boundary = max(last_period, last_question, last_exclaim)
                
                # If found a boundary in last 20% of chunk, use it
                if last_boundary > chunk_size * 0.8:
                    chunk_end = current_position + last_boundary + 1
                    chunk_text = content[current_position:chunk_end]
            
            # Create chunk
            chunk = DocumentChunk(
                content=chunk_text.strip(),
                metadata=ChunkMetadata(
                    chunk_id=f"{document_id}_chunk_{len(chunks)}",
                    document_id=document_id,
                    chunk_index=len(chunks),
                    start_position=current_position,
                    end_position=chunk_end
                )
            )
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            current_position = chunk_end - chunk_overlap
            
            # Prevent infinite loop if overlap >= chunk_size
            if current_position <= chunks[-1].metadata.start_position:
                current_position = chunk_end
        
        return chunks
    
    def _chunk_semantic(
        self,
        document_id: str,
        content: str,
        chunk_size: int
    ) -> List[DocumentChunk]:
        """
        Chunk by semantic similarity (basic implementation).
        
        Groups sentences that are semantically related based on:
        - Shared keywords
        - Similar sentence structure
        - Continuation indicators (pronouns, conjunctions)
        
        Note: This is a basic implementation. Advanced semantic chunking
        would use embeddings and similarity scores.
        """
        # Split into sentences
        sentences = sent_tokenize(content)
        
        chunks = []
        current_group = []
        current_size = 0
        current_position = 0
        previous_keywords = set()
        
        for sentence in sentences:
            # Extract keywords (simple: nouns and verbs)
            words = word_tokenize(sentence.lower())
            keywords = {
                w for w in words
                if len(w) > 4 and w.isalpha()
            }
            
            # Check for continuation indicators
            starts_with_pronoun = any(
                sentence.lower().startswith(p)
                for p in ['he', 'she', 'it', 'they', 'this', 'that', 'these']
            )
            starts_with_conjunction = any(
                sentence.lower().startswith(c)
                for c in ['and', 'but', 'however', 'moreover', 'furthermore']
            )
            
            # Calculate semantic similarity (simple: shared keywords)
            if previous_keywords:
                shared = len(keywords & previous_keywords)
                total = len(keywords | previous_keywords)
                similarity = shared / total if total > 0 else 0
            else:
                similarity = 1.0  # First sentence
            
            # Decide whether to continue current group or start new one
            should_continue = (
                similarity > 0.2  # Share some keywords
                or starts_with_pronoun
                or starts_with_conjunction
                or current_size + len(sentence) <= chunk_size
            )
            
            if should_continue and current_group:
                # Continue current group
                current_group.append(sentence)
                current_size += len(sentence) + 1
                previous_keywords |= keywords
            else:
                # Start new group
                if current_group:
                    # Save current group as chunk
                    chunk_text = " ".join(current_group)
                    chunk_start = current_position
                    chunk_end = chunk_start + len(chunk_text)
                    
                    chunk = DocumentChunk(
                        content=chunk_text,
                        metadata=ChunkMetadata(
                            chunk_id=f"{document_id}_chunk_{len(chunks)}",
                            document_id=document_id,
                            chunk_index=len(chunks),
                            start_position=chunk_start,
                            end_position=chunk_end
                        )
                    )
                    chunks.append(chunk)
                    current_position = chunk_end
                
                # Start new group
                current_group = [sentence]
                current_size = len(sentence)
                previous_keywords = keywords
        
        # Add final group
        if current_group:
            chunk_text = " ".join(current_group)
            chunk_start = current_position
            chunk_end = chunk_start + len(chunk_text)
            
            chunk = DocumentChunk(
                content=chunk_text,
                metadata=ChunkMetadata(
                    chunk_id=f"{document_id}_chunk_{len(chunks)}",
                    document_id=document_id,
                    chunk_index=len(chunks),
                    start_position=chunk_start,
                    end_position=chunk_end
                )
            )
            chunks.append(chunk)
        
        return chunks
    
    def get_chunk_statistics(
        self, chunks: List[DocumentChunk]
    ) -> Dict[str, Any]:
        """
        Calculate statistics for a list of chunks.
        
        Args:
            chunks: List of document chunks
        
        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
                "avg_word_count": 0,
                "avg_sentence_count": 0
            }
        
        sizes = [chunk.metadata.char_count for chunk in chunks]
        word_counts = [chunk.metadata.word_count for chunk in chunks]
        sentence_counts = [chunk.metadata.sentence_count for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(sizes) / len(sizes),
            "min_chunk_size": min(sizes),
            "max_chunk_size": max(sizes),
            "avg_word_count": sum(word_counts) / len(word_counts),
            "avg_sentence_count": sum(sentence_counts) / len(sentence_counts),
            "total_characters": sum(sizes),
            "total_words": sum(word_counts),
            "total_sentences": sum(sentence_counts)
        }


# Global chunker service instance (singleton)
_chunker_service: Optional[ChunkerService] = None


def get_chunker_service() -> ChunkerService:
    """
    Get or create the global chunker service instance.
    
    Returns:
        ChunkerService instance
    """
    global _chunker_service
    if _chunker_service is None:
        _chunker_service = ChunkerService()
    return _chunker_service
