"""
Metadata extraction package for In My Head.

Provides AI-powered metadata extraction from documents using Claude.
"""

from .metadata_extractor import MetadataExtractor, ExtractedMetadata
from .metadata_types import (
    Author,
    Topic,
    Entity,
    DateReference,
    Category,
    MetadataField,
)

__all__ = [
    "MetadataExtractor",
    "ExtractedMetadata",
    "Author",
    "Topic",
    "Entity",
    "DateReference",
    "Category",
    "MetadataField",
]
