"""
Metadata extraction package for In My Head.

Provides AI-powered metadata extraction from documents using Claude.
"""

from .metadata_extractor import MetadataExtractor, ExtractedMetadata
from .metadata_enricher import (
    MetadataEnricher,
    EnrichedDocument,
    EnrichmentStats,
)
from .metadata_types import (
    Author,
    Topic,
    Entity,
    DateReference,
    Category,
    Sentiment,
    EntityType,
    CategoryType,
    MetadataField,
)

__all__ = [
    "MetadataExtractor",
    "ExtractedMetadata",
    "MetadataEnricher",
    "EnrichedDocument",
    "EnrichmentStats",
    "Author",
    "Topic",
    "Entity",
    "DateReference",
    "Category",
    "Sentiment",
    "EntityType",
    "CategoryType",
    "MetadataField",
]
