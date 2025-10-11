"""
Vector storage package for In My Head.

Provides Qdrant integration for storing and searching embeddings.
"""

from .vector_store import VectorStore, VectorDocument, SearchResult
from .collection_manager import CollectionManager, CollectionConfig
from .search_engine import SearchEngine, SearchQuery, SearchFilter

__all__ = [
    "VectorStore",
    "VectorDocument",
    "SearchResult",
    "CollectionManager",
    "CollectionConfig",
    "SearchEngine",
    "SearchQuery",
    "SearchFilter",
]
