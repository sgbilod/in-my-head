"""
Text preprocessing module for document processing.

This module provides utilities for cleaning, normalizing, chunking,
and deduplicating text extracted from documents.
"""

from .text_cleaner import TextCleaner
from .text_normalizer import TextNormalizer
from .chunker import TextChunker, TextChunk
from .deduplicator import Deduplicator

__all__ = [
    "TextCleaner",
    "TextNormalizer",
    "TextChunker",
    "TextChunk",
    "Deduplicator",
]
