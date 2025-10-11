"""
Embeddings package for document processing.

Provides:
- EmbeddingGenerator: Generate embeddings using OpenAI API
- EmbeddingCache: Redis-based caching for embeddings
- BatchEmbeddingProcessor: Efficient batch processing
"""

from .embedding_generator import EmbeddingGenerator, Embedding
from .embedding_cache import EmbeddingCache
from .batch_processor import BatchEmbeddingProcessor

__all__ = [
    # Classes
    "EmbeddingGenerator",
    "Embedding",
    "EmbeddingCache",
    "BatchEmbeddingProcessor",
]
