"""
Text preprocessing package for document processing.

Provides:
- TextCleaner: Remove noise and normalize whitespace
- TextNormalizer: Unicode and case normalization
- TextChunker: Intelligent chunking for embeddings
- Deduplicator: Remove duplicate content
- PreprocessingPipeline: Unified pipeline combining all components
"""

from .text_cleaner import TextCleaner, clean_text
from .text_normalizer import TextNormalizer, normalize_text
from .chunker import TextChunker, TextChunk, chunk_text
from .deduplicator import Deduplicator, deduplicate_texts
from .pipeline import PreprocessingPipeline, process_text

__all__ = [
    # Classes
    "TextCleaner",
    "TextNormalizer",
    "TextChunker",
    "TextChunk",
    "Deduplicator",
    "PreprocessingPipeline",
    # Convenience functions
    "clean_text",
    "normalize_text",
    "chunk_text",
    "deduplicate_texts",
    "process_text",
]
