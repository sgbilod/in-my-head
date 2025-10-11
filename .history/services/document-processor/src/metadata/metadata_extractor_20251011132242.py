"""
AI-powered metadata extraction using Claude.

Extracts rich metadata from documents including:
- Authors and contributors
- Topics and subtopics
- Named entities (people, organizations, locations, etc.)
- Dates and temporal references
- Categories and tags
- Summaries and keywords
- Language and sentiment
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import datetime

from anthropic import Anthropic
import redis.asyncio as redis

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

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ExtractedMetadata:
    """Container for extracted metadata."""

    text: str
    authors: List[Author] = field(default_factory=list)
    topics: List[Topic] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    dates: List[DateReference] = field(default_factory=list)
    categories: List[Category] = field(default_factory=list)
    summary: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    title: Optional[str] = None
    language: Optional[str] = None
    sentiment: Optional[Sentiment] = None
    extracted_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "authors": [a.to_dict() for a in self.authors],
            "topics": [t.to_dict() for t in self.topics],
            "entities": [e.to_dict() for e in self.entities],
            "dates": [d.to_dict() for d in self.dates],
            "categories": [c.to_dict() for c in self.categories],
            "summary": self.summary,
            "keywords": self.keywords,
            "title": self.title,
            "language": self.language,
            "sentiment": self.sentiment.to_dict() if self.sentiment else None,
            "extracted_at": self.extracted_at.isoformat(),
            "confidence": self.confidence,
        }


class MetadataExtractor:
    """
    Extract metadata from documents using Claude AI.

    Features:
    - Intelligent metadata extraction
    - Redis caching for performance
    - Batch processing support
    - Configurable fields
    - Error handling and retry logic
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        model: str = "claude-sonnet-4-20250514",
        cache_ttl: int = 604800,  # 7 days
        max_tokens: int = 4096,
    ):
        """
        Initialize metadata extractor.

        Args:
            anthropic_api_key: Anthropic API key (or from env)
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database number
            model: Claude model to use
            cache_ttl: Cache TTL in seconds (default: 7 days)
            max_tokens: Maximum tokens for response
        """
        # Initialize Anthropic client
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided")

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

        # Initialize Redis for caching
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
        )
        self.cache_ttl = cache_ttl

        # Statistics
        self.stats = {
            "total_extracted": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "failed_extractions": 0,
        }

        logger.info(
            f"Initialized MetadataExtractor with model={model}, "
            f"cache_ttl={cache_ttl}s"
        )

    async def extract(
        self,
        text: str,
        fields: Optional[Set[MetadataField]] = None,
        use_cache: bool = True,
    ) -> ExtractedMetadata:
        """
        Extract metadata from text.

        Args:
            text: Text to extract metadata from
            fields: Specific fields to extract (None = all)
            use_cache: Whether to use cached results

        Returns:
            ExtractedMetadata object

        Raises:
            Exception: If extraction fails
        """
        # Check cache
        if use_cache:
            cached = await self._get_cached(text, fields)
            if cached:
                self.stats["cache_hits"] += 1
                logger.debug("Cache hit for metadata extraction")
                return cached
            self.stats["cache_misses"] += 1

        try:
            # Extract metadata using Claude
            metadata = await self._extract_with_claude(text, fields)

            # Cache result
            if use_cache:
                await self._cache_metadata(text, metadata, fields)

            self.stats["total_extracted"] += 1
            logger.info("Successfully extracted metadata")

            return metadata

        except Exception as e:
            self.stats["failed_extractions"] += 1
            logger.error(f"Metadata extraction failed: {e}")
            raise

    async def extract_batch(
        self,
        texts: List[str],
        fields: Optional[Set[MetadataField]] = None,
        use_cache: bool = True,
    ) -> List[ExtractedMetadata]:
        """
        Extract metadata from multiple texts.

        Args:
            texts: List of texts to process
            fields: Specific fields to extract
            use_cache: Whether to use cached results

        Returns:
            List of ExtractedMetadata objects
        """
        results = []

        for i, text in enumerate(texts):
            try:
                metadata = await self.extract(text, fields, use_cache)
                results.append(metadata)
                logger.debug(f"Processed {i + 1}/{len(texts)}")

            except Exception as e:
                logger.error(f"Failed to extract metadata for text {i}: {e}")
                # Return empty metadata on failure
                results.append(
                    ExtractedMetadata(
                        text=text[:100],
                        confidence=0.0,
                    )
                )

        return results

    async def _extract_with_claude(
        self,
        text: str,
        fields: Optional[Set[MetadataField]] = None,
    ) -> ExtractedMetadata:
        """
        Extract metadata using Claude API.

        Args:
            text: Text to analyze
            fields: Specific fields to extract

        Returns:
            ExtractedMetadata object
        """
        # Build prompt
        prompt = self._build_extraction_prompt(text, fields)

        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        # Parse response
        response_text = response.content[0].text
        metadata_dict = json.loads(response_text)

        # Convert to ExtractedMetadata
        metadata = self._parse_metadata(text, metadata_dict)

        return metadata

    def _build_extraction_prompt(
        self,
        text: str,
        fields: Optional[Set[MetadataField]] = None,
    ) -> str:
        """
        Build extraction prompt for Claude.

        Args:
            text: Text to analyze
            fields: Specific fields to extract

        Returns:
            Formatted prompt
        """
        # Determine which fields to extract
        if fields is None:
            fields = set(MetadataField)

        field_descriptions = []

        if MetadataField.AUTHORS in fields:
            field_descriptions.append(
                '- "authors": List of authors/contributors with their roles'
            )

        if MetadataField.TOPICS in fields:
            field_descriptions.append(
                '- "topics": Main topics with relevance scores (0.0-1.0)'
            )

        if MetadataField.ENTITIES in fields:
            field_descriptions.append(
                '- "entities": Named entities (people, organizations, '
                'locations, etc.)'
            )

        if MetadataField.DATES in fields:
            field_descriptions.append(
                '- "dates": Date references with context'
            )

        if MetadataField.CATEGORIES in fields:
            field_descriptions.append(
                '- "categories": Document categories '
                '(technology, science, business, etc.)'
            )

        if MetadataField.SUMMARY in fields:
            field_descriptions.append(
                '- "summary": Brief summary (2-3 sentences)'
            )

        if MetadataField.KEYWORDS in fields:
            field_descriptions.append(
                '- "keywords": 5-10 key terms'
            )

        if MetadataField.TITLE in fields:
            field_descriptions.append(
                '- "title": Suggested title if not present'
            )

        if MetadataField.LANGUAGE in fields:
            field_descriptions.append(
                '- "language": Detected language (ISO 639-1 code)'
            )

        if MetadataField.SENTIMENT in fields:
            field_descriptions.append(
                '- "sentiment": Overall sentiment (-1.0 to 1.0)'
            )

        fields_str = "\n".join(field_descriptions)

        prompt = f"""
You are an expert metadata extraction system. Analyze the following text
and extract structured metadata.

TEXT:
{text[:4000]}  # Limit to ~4000 chars to avoid token limits

Extract the following metadata fields:
{fields_str}

Respond with ONLY a valid JSON object (no markdown, no explanations):

{{
  "authors": [
    {{"name": "Author Name", "role": "author", "confidence": 0.9}}
  ],
  "topics": [
    {{"name": "Topic Name", "relevance": 0.95, "subtopics": ["subtopic1"]}}
  ],
  "entities": [
    {{
      "name": "Entity Name",
      "type": "person|organization|location|product|event|concept",
      "mentions": 3,
      "confidence": 0.9
    }}
  ],
  "dates": [
    {{"date": "2025-10-11", "context": "publication date", "type": "published"}}
  ],
  "categories": [
    {{
      "name": "technology|science|business|education|health|entertainment",
      "subcategory": "AI",
      "confidence": 0.95
    }}
  ],
  "summary": "Brief summary of the text...",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "title": "Suggested Title",
  "language": "en",
  "sentiment": {{"score": 0.5, "label": "positive", "confidence": 0.9}}
}}

Important:
- Only include fields that are present/relevant
- Be precise and confident in your extractions
- Use confidence scores to indicate certainty
- Respond with ONLY the JSON object
"""

        return prompt

    def _parse_metadata(
        self, text: str, metadata_dict: Dict[str, Any]
    ) -> ExtractedMetadata:
        """
        Parse metadata dictionary into ExtractedMetadata object.

        Args:
            text: Original text
            metadata_dict: Parsed JSON from Claude

        Returns:
            ExtractedMetadata object
        """
        # Parse authors
        authors = [
            Author(
                name=a.get("name", ""),
                role=a.get("role"),
                affiliation=a.get("affiliation"),
                confidence=a.get("confidence", 1.0),
            )
            for a in metadata_dict.get("authors", [])
        ]

        # Parse topics
        topics = [
            Topic(
                name=t.get("name", ""),
                relevance=t.get("relevance", 1.0),
                subtopics=t.get("subtopics", []),
            )
            for t in metadata_dict.get("topics", [])
        ]

        # Parse entities
        entities = [
            Entity(
                name=e.get("name", ""),
                type=EntityType(e.get("type", "other")),
                mentions=e.get("mentions", 1),
                context=e.get("context"),
                confidence=e.get("confidence", 1.0),
            )
            for e in metadata_dict.get("entities", [])
        ]

        # Parse dates
        dates = [
            DateReference(
                date=d.get("date", ""),
                context=d.get("context"),
                type=d.get("type", "mentioned"),
            )
            for d in metadata_dict.get("dates", [])
        ]

        # Parse categories
        categories = [
            Category(
                name=CategoryType(c.get("name", "other")),
                subcategory=c.get("subcategory"),
                confidence=c.get("confidence", 1.0),
            )
            for c in metadata_dict.get("categories", [])
        ]

        # Parse sentiment
        sentiment_data = metadata_dict.get("sentiment")
        sentiment = None
        if sentiment_data:
            sentiment = Sentiment(
                score=sentiment_data.get("score", 0.0),
                label=sentiment_data.get("label", "neutral"),
                confidence=sentiment_data.get("confidence", 1.0),
            )

        return ExtractedMetadata(
            text=text[:500],  # Store preview
            authors=authors,
            topics=topics,
            entities=entities,
            dates=dates,
            categories=categories,
            summary=metadata_dict.get("summary"),
            keywords=metadata_dict.get("keywords", []),
            title=metadata_dict.get("title"),
            language=metadata_dict.get("language"),
            sentiment=sentiment,
        )

    async def _get_cached(
        self,
        text: str,
        fields: Optional[Set[MetadataField]] = None,
    ) -> Optional[ExtractedMetadata]:
        """
        Get cached metadata.

        Args:
            text: Text to look up
            fields: Fields that were extracted

        Returns:
            Cached metadata or None
        """
        try:
            cache_key = self._get_cache_key(text, fields)
            cached_json = await self.redis_client.get(cache_key)

            if cached_json:
                metadata_dict = json.loads(cached_json)
                # Reconstruct ExtractedMetadata
                return self._parse_metadata(text, metadata_dict)

            return None

        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
            return None

    async def _cache_metadata(
        self,
        text: str,
        metadata: ExtractedMetadata,
        fields: Optional[Set[MetadataField]] = None,
    ):
        """
        Cache extracted metadata.

        Args:
            text: Text that was analyzed
            metadata: Extracted metadata
            fields: Fields that were extracted
        """
        try:
            cache_key = self._get_cache_key(text, fields)
            metadata_json = json.dumps(metadata.to_dict())

            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                metadata_json,
            )

            logger.debug(f"Cached metadata with key: {cache_key}")

        except Exception as e:
            logger.warning(f"Failed to cache metadata: {e}")

    def _get_cache_key(
        self,
        text: str,
        fields: Optional[Set[MetadataField]] = None,
    ) -> str:
        """
        Generate cache key.

        Args:
            text: Text being analyzed
            fields: Fields being extracted

        Returns:
            Cache key
        """
        import hashlib

        # Hash text
        text_hash = hashlib.sha256(text.encode()).hexdigest()

        # Hash fields
        if fields:
            fields_str = ",".join(sorted(f.value for f in fields))
        else:
            fields_str = "all"

        fields_hash = hashlib.sha256(fields_str.encode()).hexdigest()[:8]

        return f"metadata:{text_hash}:{fields_hash}"

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get extraction statistics.

        Returns:
            Statistics dictionary
        """
        cache_info = await self.redis_client.info("stats")

        return {
            **self.stats,
            "cache_hit_rate": (
                self.stats["cache_hits"]
                / max(
                    self.stats["cache_hits"] + self.stats["cache_misses"],
                    1,
                )
            ),
            "redis_keys": cache_info.get("db0", {}).get("keys", 0),
        }

    async def close(self):
        """Close connections."""
        await self.redis_client.close()
        logger.info("Closed MetadataExtractor connections")
