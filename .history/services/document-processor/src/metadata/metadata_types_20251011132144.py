"""
Metadata type definitions.

Data structures for representing extracted metadata.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class EntityType(str, Enum):
    """Types of named entities."""

    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    PRODUCT = "product"
    EVENT = "event"
    CONCEPT = "concept"
    OTHER = "other"


class CategoryType(str, Enum):
    """Document category types."""

    TECHNOLOGY = "technology"
    SCIENCE = "science"
    BUSINESS = "business"
    EDUCATION = "education"
    HEALTH = "health"
    ENTERTAINMENT = "entertainment"
    POLITICS = "politics"
    SPORTS = "sports"
    ARTS = "arts"
    PERSONAL = "personal"
    OTHER = "other"


class MetadataField(str, Enum):
    """Available metadata fields."""

    AUTHORS = "authors"
    DATES = "dates"
    TOPICS = "topics"
    ENTITIES = "entities"
    CATEGORIES = "categories"
    SUMMARY = "summary"
    KEYWORDS = "keywords"
    TITLE = "title"
    LANGUAGE = "language"
    SENTIMENT = "sentiment"


@dataclass
class Author:
    """Represents a document author."""

    name: str
    role: Optional[str] = None  # e.g., "author", "editor", "contributor"
    affiliation: Optional[str] = None
    confidence: float = 1.0  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "role": self.role,
            "affiliation": self.affiliation,
            "confidence": self.confidence,
        }


@dataclass
class Topic:
    """Represents a document topic."""

    name: str
    relevance: float = 1.0  # 0.0 to 1.0
    subtopics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "relevance": self.relevance,
            "subtopics": self.subtopics,
        }


@dataclass
class Entity:
    """Represents a named entity."""

    name: str
    type: EntityType
    mentions: int = 1
    context: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "mentions": self.mentions,
            "context": self.context,
            "confidence": self.confidence,
        }


@dataclass
class DateReference:
    """Represents a date mentioned in the document."""

    date: str  # ISO 8601 format or natural language
    context: Optional[str] = None  # What the date refers to
    type: str = "mentioned"  # "created", "published", "modified", "mentioned"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "date": self.date,
            "context": self.context,
            "type": self.type,
        }


@dataclass
class Category:
    """Represents a document category."""

    name: CategoryType
    subcategory: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name.value,
            "subcategory": self.subcategory,
            "confidence": self.confidence,
        }


@dataclass
class Sentiment:
    """Represents document sentiment."""

    score: float  # -1.0 (negative) to 1.0 (positive)
    label: str  # "positive", "negative", "neutral"
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "score": self.score,
            "label": self.label,
            "confidence": self.confidence,
        }
