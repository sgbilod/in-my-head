"""
Intelligent text chunker for creating optimal chunks for embeddings.

Features:
- Semantic chunking (preserves sentence boundaries)
- Token-based sizing (using tiktoken)
- Configurable overlap between chunks
- Special handling for code blocks and tables
"""

import os
import re
import tiktoken
from dataclasses import dataclass, field
from typing import List, Optional

# Fix SSL certificate issue on Windows (PostgreSQL sets invalid SSL_CERT_FILE)
if 'SSL_CERT_FILE' in os.environ:
    ssl_cert_file = os.environ['SSL_CERT_FILE']
    if not os.path.exists(ssl_cert_file):
        # Use certifi's certificate bundle instead
        try:
            import certifi
            os.environ['SSL_CERT_FILE'] = certifi.where()
        except ImportError:
            del os.environ['SSL_CERT_FILE']


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""

    text: str
    start_pos: int
    end_pos: int
    token_count: int
    chunk_index: int
    overlap_with_previous: int = 0
    metadata: dict = field(default_factory=dict)

    def __len__(self) -> int:
        """Return character length of chunk."""
        return len(self.text)


class TextChunker:
    """
    Intelligent text chunker for embeddings.

    Creates chunks that:
    - Respect sentence boundaries
    - Target specific token counts
    - Include overlap for context preservation
    - Handle special content (code, tables) appropriately
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap_size: int = 50,
        model: str = "cl100k_base",  # GPT-4/GPT-3.5 tokenizer
        min_chunk_size: int = 100,
        respect_paragraphs: bool = True,
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target token count per chunk
            overlap_size: Number of tokens to overlap between chunks
            model: Tiktoken model name
            min_chunk_size: Minimum tokens per chunk
            respect_paragraphs: Try to keep paragraphs together
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        self.respect_paragraphs = respect_paragraphs

        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding(model)
        except Exception:
            # Fallback to default
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # Compile patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for text segmentation."""
        # Sentence boundaries (improved pattern)
        self.sentence_end = re.compile(
            r"(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\n+(?=[A-Z])"
        )

        # Paragraph boundaries
        self.paragraph_end = re.compile(r"\n\s*\n")

        # Code blocks (markdown and common patterns)
        self.code_block = re.compile(
            r"```[\s\S]*?```|~~~[\s\S]*?~~~|"
            r"(?:^|\n)(?:    |\t).+(?:\n(?:    |\t).+)*",
            re.MULTILINE
        )

        # Table patterns (markdown tables)
        self.table_pattern = re.compile(
            r"(?:^|\n)\|.+\|(?:\n\|.+\|)+",
            re.MULTILINE
        )

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        if not text:
            return 0
        return len(self.tokenizer.encode(text))

    def chunk_text(self, text: str, metadata: Optional[dict] = None) -> List[TextChunk]:
        """
        Split text into optimal chunks for embeddings.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to all chunks

        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []

        metadata = metadata or {}

        # Check if text is small enough for single chunk
        token_count = self.count_tokens(text)
        if token_count <= self.chunk_size:
            return [
                TextChunk(
                    text=text.strip(),
                    start_pos=0,
                    end_pos=len(text),
                    token_count=token_count,
                    chunk_index=0,
                    metadata=metadata,
                )
            ]

        # Extract special content (code blocks, tables)
        special_content = self._extract_special_content(text)

        # Split into segments (paragraphs or sentences)
        if self.respect_paragraphs:
            segments = self._split_by_paragraphs(text)
        else:
            segments = self._split_by_sentences(text)

        # Create chunks from segments
        chunks = self._create_chunks_from_segments(
            segments, special_content, metadata
        )

        return chunks

    def _extract_special_content(self, text: str) -> dict:
        """
        Extract and index special content (code blocks, tables).

        Returns dict mapping position to (type, content).
        """
        special = {}

        # Find code blocks
        for match in self.code_block.finditer(text):
            special[match.start()] = ("code", match.group())

        # Find tables
        for match in self.table_pattern.finditer(text):
            special[match.start()] = ("table", match.group())

        return special

    def _split_by_paragraphs(self, text: str) -> List[tuple[str, int]]:
        """
        Split text into paragraphs with positions.

        Returns list of (paragraph_text, start_position) tuples.
        """
        segments = []
        last_pos = 0

        for match in self.paragraph_end.finditer(text):
            segment = text[last_pos:match.start()].strip()
            if segment:
                segments.append((segment, last_pos))
            last_pos = match.end()

        # Add final segment
        if last_pos < len(text):
            segment = text[last_pos:].strip()
            if segment:
                segments.append((segment, last_pos))

        # If no paragraphs found, fall back to sentences
        if not segments:
            return self._split_by_sentences(text)

        return segments

    def _split_by_sentences(self, text: str) -> List[tuple[str, int]]:
        """
        Split text into sentences with positions.

        Returns list of (sentence_text, start_position) tuples.
        """
        segments = []
        last_pos = 0

        for match in self.sentence_end.finditer(text):
            segment = text[last_pos:match.start()].strip()
            if segment:
                segments.append((segment, last_pos))
            last_pos = match.end()

        # Add final segment
        if last_pos < len(text):
            segment = text[last_pos:].strip()
            if segment:
                segments.append((segment, last_pos))

        # If no sentences found (e.g., single long line), split by max tokens
        if not segments:
            return self._split_by_tokens(text)

        return segments

    def _split_by_tokens(self, text: str) -> List[tuple[str, int]]:
        """
        Emergency fallback: split by token count directly.

        Used when text has no clear sentence/paragraph boundaries.
        """
        segments = []
        words = text.split()
        current_chunk = []
        current_tokens = 0
        pos = 0

        for word in words:
            word_tokens = self.count_tokens(word)

            if current_tokens + word_tokens > self.chunk_size:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                segments.append((chunk_text, pos))
                pos += len(chunk_text) + 1

                # Start new chunk
                current_chunk = [word]
                current_tokens = word_tokens
            else:
                current_chunk.append(word)
                current_tokens += word_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            segments.append((chunk_text, pos))

        return segments

    def _create_chunks_from_segments(
        self,
        segments: List[tuple[str, int]],
        special_content: dict,
        metadata: dict,
    ) -> List[TextChunk]:
        """
        Combine segments into chunks with optimal token counts.
        """
        chunks = []
        current_segments = []
        current_tokens = 0
        current_start_pos = 0
        overlap_segments = []
        chunk_index = 0

        for segment_text, segment_pos in segments:
            segment_tokens = self.count_tokens(segment_text)

            # Handle oversized segments (shouldn't happen often)
            if segment_tokens > self.chunk_size:
                # Save current chunk if any
                if current_segments:
                    chunks.append(
                        self._create_chunk(
                            current_segments,
                            current_start_pos,
                            chunk_index,
                            overlap_segments,
                            metadata,
                        )
                    )
                    chunk_index += 1
                    current_segments = []
                    current_tokens = 0

                # Split oversized segment by tokens
                sub_segments = self._split_by_tokens(segment_text)
                for sub_text, sub_pos in sub_segments:
                    sub_tokens = self.count_tokens(sub_text)
                    chunks.append(
                        TextChunk(
                            text=sub_text,
                            start_pos=segment_pos + sub_pos,
                            end_pos=segment_pos + sub_pos + len(sub_text),
                            token_count=sub_tokens,
                            chunk_index=chunk_index,
                            metadata=metadata,
                        )
                    )
                    chunk_index += 1

                overlap_segments = []
                continue

            # Check if adding this segment would exceed chunk size
            if current_tokens + segment_tokens > self.chunk_size:
                # Save current chunk
                chunks.append(
                    self._create_chunk(
                        current_segments,
                        current_start_pos,
                        chunk_index,
                        overlap_segments,
                        metadata,
                    )
                )
                chunk_index += 1

                # Start new chunk with overlap
                overlap_segments = self._get_overlap_segments(
                    current_segments, self.overlap_size
                )
                current_segments = overlap_segments + [(segment_text, segment_pos)]
                current_tokens = sum(
                    self.count_tokens(seg[0]) for seg in current_segments
                )
                current_start_pos = (
                    overlap_segments[0][1] if overlap_segments else segment_pos
                )
            else:
                # Add segment to current chunk
                if not current_segments:
                    current_start_pos = segment_pos
                current_segments.append((segment_text, segment_pos))
                current_tokens += segment_tokens

        # Add final chunk
        if current_segments:
            chunks.append(
                self._create_chunk(
                    current_segments,
                    current_start_pos,
                    chunk_index,
                    overlap_segments,
                    metadata,
                )
            )

        return chunks

    def _create_chunk(
        self,
        segments: List[tuple[str, int]],
        start_pos: int,
        chunk_index: int,
        overlap_segments: List[tuple[str, int]],
        metadata: dict,
    ) -> TextChunk:
        """Create a TextChunk from segments."""
        chunk_text = " ".join(seg[0] for seg in segments)
        token_count = self.count_tokens(chunk_text)

        # Calculate overlap tokens
        overlap_tokens = 0
        if overlap_segments:
            overlap_text = " ".join(seg[0] for seg in overlap_segments)
            overlap_tokens = self.count_tokens(overlap_text)

        return TextChunk(
            text=chunk_text,
            start_pos=start_pos,
            end_pos=start_pos + len(chunk_text),
            token_count=token_count,
            chunk_index=chunk_index,
            overlap_with_previous=overlap_tokens,
            metadata=metadata,
        )

    def _get_overlap_segments(
        self,
        segments: List[tuple[str, int]],
        target_overlap_tokens: int,
    ) -> List[tuple[str, int]]:
        """
        Get segments from end of list that total approximately target tokens.
        """
        overlap = []
        overlap_tokens = 0

        # Work backwards from end
        for segment in reversed(segments):
            segment_tokens = self.count_tokens(segment[0])

            if overlap_tokens + segment_tokens > target_overlap_tokens:
                break

            overlap.insert(0, segment)
            overlap_tokens += segment_tokens

        return overlap


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
) -> List[TextChunk]:
    """
    Convenience function for quick text chunking.

    Args:
        text: Text to chunk
        chunk_size: Target tokens per chunk
        overlap: Overlap tokens between chunks

    Returns:
        List of TextChunk objects
    """
    chunker = TextChunker(chunk_size=chunk_size, overlap_size=overlap)
    return chunker.chunk_text(text)
