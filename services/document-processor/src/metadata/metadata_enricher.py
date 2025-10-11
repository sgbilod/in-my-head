"""
Metadata enricher for In My Head.

This module provides the MetadataEnricher class that integrates:
- Document parsing
- Text preprocessing
- Embedding generation
- AI-powered metadata extraction
- Vector storage with rich metadata

The enricher orchestrates the complete pipeline from raw documents
to searchable, semantically-indexed content with AI-extracted metadata.
"""

import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path

from .metadata_types import MetadataField
from .metadata_extractor import MetadataExtractor, ExtractedMetadata


logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================


@dataclass
class EnrichedDocument:
    """
    A document enriched with embeddings and AI-extracted metadata.

    Attributes:
        id: Unique document identifier
        text: Document text content
        embedding: Vector embedding (3072-dim)
        metadata: AI-extracted metadata
        source: Original source file path or URL
        created_at: Document creation timestamp
        enriched_at: Enrichment processing timestamp
        vector_id: ID in vector database
        confidence: Overall enrichment confidence score
    """

    id: str
    text: str
    embedding: List[float]
    metadata: ExtractedMetadata
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    enriched_at: datetime = field(default_factory=datetime.utcnow)
    vector_id: Optional[str] = None
    confidence: float = 1.0

    def to_vector_payload(self) -> Dict[str, Any]:
        """
        Convert to payload format for vector storage.

        Returns:
            Dictionary with document data and metadata for Qdrant.
        """
        payload = {
            "id": self.id,
            "text": self.text[:1000],  # Store preview (first 1000 chars)
            "full_text_length": len(self.text),
            "source": self.source,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "enriched_at": self.enriched_at.isoformat(),
            "confidence": self.confidence,
            # Metadata fields
            "authors": [
                {
                    "name": a.name,
                    "role": a.role,
                    "affiliation": a.affiliation,
                    "confidence": a.confidence,
                }
                for a in self.metadata.authors
            ],
            "topics": [
                {
                    "name": t.name,
                    "relevance": t.relevance,
                    "subtopics": t.subtopics,
                }
                for t in self.metadata.topics
            ],
            "entities": [
                {
                    "name": e.name,
                    "type": e.type.value,
                    "mentions": e.mentions,
                    "context": e.context,
                    "confidence": e.confidence,
                }
                for e in self.metadata.entities
            ],
            "dates": [
                {
                    "date": d.date,
                    "context": d.context,
                    "type": d.type,
                }
                for d in self.metadata.dates
            ],
            "categories": [
                {
                    "name": c.name.value,
                    "subcategory": c.subcategory,
                    "confidence": c.confidence,
                }
                for c in self.metadata.categories
            ],
            "summary": self.metadata.summary,
            "keywords": self.metadata.keywords,
            "title": self.metadata.title,
            "language": self.metadata.language,
            "sentiment": (
                {
                    "score": self.metadata.sentiment.score,
                    "label": self.metadata.sentiment.label,
                    "confidence": self.metadata.sentiment.confidence,
                }
                if self.metadata.sentiment
                else None
            ),
        }
        return payload


@dataclass
class EnrichmentStats:
    """
    Statistics for enrichment operations.

    Attributes:
        total_processed: Total documents processed
        successful: Successfully enriched documents
        failed: Failed enrichment attempts
        total_tokens: Total tokens processed
        avg_processing_time: Average processing time per document
        cache_hits: Number of cache hits
        cache_misses: Number of cache misses
    """

    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    total_tokens: int = 0
    avg_processing_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_processed": self.total_processed,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": (
                self.successful / max(self.total_processed, 1)
            ),
            "total_tokens": self.total_tokens,
            "avg_processing_time": self.avg_processing_time,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (
                self.cache_hits / max(self.cache_hits + self.cache_misses, 1)
            ),
        }


# ============================================================================
# METADATA ENRICHER
# ============================================================================


class MetadataEnricher:
    """
    Orchestrates document enrichment pipeline.

    This class integrates multiple components to provide a complete
    pipeline from raw documents to searchable, semantically-indexed
    content with AI-extracted metadata.

    Pipeline stages:
    1. Text extraction (from documents)
    2. Text preprocessing (cleaning, chunking)
    3. Embedding generation (OpenAI)
    4. Metadata extraction (Claude AI)
    5. Vector storage (Qdrant)

    Example:
        >>> enricher = MetadataEnricher(
        ...     metadata_extractor=extractor,
        ...     embedding_generator=generator,
        ...     vector_store=store
        ... )
        >>>
        >>> # Enrich single document
        >>> doc = await enricher.enrich_document(
        ...     text="Your document text...",
        ...     doc_id="doc123",
        ...     source="path/to/file.pdf"
        ... )
        >>>
        >>> # Batch processing
        >>> docs = await enricher.enrich_batch([
        ...     {"text": "Doc 1...", "id": "1"},
        ...     {"text": "Doc 2...", "id": "2"},
        ... ])
        >>>
        >>> # Get statistics
        >>> stats = enricher.get_stats()
    """

    def __init__(
        self,
        metadata_extractor: MetadataExtractor,
        embedding_generator: Any,  # EmbeddingGenerator from embeddings pkg
        vector_store: Any,  # VectorStore from vector_storage package
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        metadata_fields: Optional[Set[MetadataField]] = None,
    ):
        """
        Initialize the metadata enricher.

        Args:
            metadata_extractor: MetadataExtractor instance
            embedding_generator: EmbeddingGenerator instance
            vector_store: VectorStore instance
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
            metadata_fields: Specific metadata fields to extract
                           (None = extract all fields)
        """
        self.metadata_extractor = metadata_extractor
        self.embedding_generator = embedding_generator
        self.vector_store = vector_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.metadata_fields = metadata_fields

        # Statistics tracking
        self._stats = EnrichmentStats()

        logger.info("MetadataEnricher initialized")

    async def enrich_document(
        self,
        text: str,
        doc_id: Optional[str] = None,
        source: Optional[str] = None,
        metadata_fields: Optional[Set[MetadataField]] = None,
        store_in_vector_db: bool = True,
    ) -> EnrichedDocument:
        """
        Enrich a single document with embeddings and metadata.

        Args:
            text: Document text content
            doc_id: Document identifier (auto-generated if None)
            source: Source file path or URL
            metadata_fields: Specific fields to extract (None = use default)
            store_in_vector_db: Whether to store in vector database

        Returns:
            EnrichedDocument with embeddings and metadata

        Raises:
            ValueError: If text is empty
            Exception: If enrichment fails
        """
        if not text or not text.strip():
            raise ValueError("Document text cannot be empty")

        # Generate document ID if not provided
        if doc_id is None:
            doc_id = self._generate_doc_id(text, source)

        start_time = datetime.utcnow()
        logger.info(f"Enriching document: {doc_id}")

        try:
            # Step 1: Extract metadata using Claude
            fields = metadata_fields or self.metadata_fields
            metadata = await self.metadata_extractor.extract(
                text=text, fields=fields, use_cache=True
            )
            logger.debug(f"Metadata extracted for {doc_id}")

            # Step 2: Generate embedding
            embedding_result = await self.embedding_generator.generate(text)
            embedding = embedding_result.vector
            logger.debug(f"Embedding generated for {doc_id}: {len(embedding)}D")

            # Step 3: Create enriched document
            enriched_doc = EnrichedDocument(
                id=doc_id,
                text=text,
                embedding=embedding,
                metadata=metadata,
                source=source,
                confidence=metadata.confidence,
            )

            # Step 4: Store in vector database
            if store_in_vector_db:
                vector_id = await self._store_in_vector_db(enriched_doc)
                enriched_doc.vector_id = vector_id
                logger.debug(f"Stored in vector DB: {vector_id}")

            # Update statistics
            processing_time = (
                datetime.utcnow() - start_time
            ).total_seconds()
            self._update_stats(success=True, processing_time=processing_time)

            logger.info(
                f"Document enriched successfully: {doc_id} "
                f"({processing_time:.2f}s)"
            )
            return enriched_doc

        except Exception as e:
            self._update_stats(success=False)
            logger.error(f"Failed to enrich document {doc_id}: {e}")
            raise

    async def enrich_batch(
        self,
        documents: List[Dict[str, str]],
        metadata_fields: Optional[Set[MetadataField]] = None,
        store_in_vector_db: bool = True,
    ) -> List[EnrichedDocument]:
        """
        Enrich multiple documents in batch.

        Args:
            documents: List of dicts with 'text', optional 'id', 'source'
            metadata_fields: Specific fields to extract
            store_in_vector_db: Whether to store in vector database

        Returns:
            List of EnrichedDocument objects

        Example:
            >>> docs = await enricher.enrich_batch([
            ...     {"text": "Document 1...", "id": "doc1"},
            ...     {"text": "Document 2...", "source": "file.pdf"},
            ... ])
        """
        logger.info(f"Starting batch enrichment of {len(documents)} documents")

        enriched_docs = []
        for doc_dict in documents:
            try:
                enriched_doc = await self.enrich_document(
                    text=doc_dict["text"],
                    doc_id=doc_dict.get("id"),
                    source=doc_dict.get("source"),
                    metadata_fields=metadata_fields,
                    store_in_vector_db=store_in_vector_db,
                )
                enriched_docs.append(enriched_doc)

            except Exception as e:
                logger.error(
                    f"Failed to enrich document "
                    f"{doc_dict.get('id', 'unknown')}: {e}"
                )
                # Continue with next document
                continue

        logger.info(
            f"Batch enrichment complete: "
            f"{len(enriched_docs)}/{len(documents)} successful"
        )
        return enriched_docs

    async def search_by_metadata(
        self,
        query_text: Optional[str] = None,
        authors: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
        date_range: Optional[tuple] = None,
        sentiment: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search documents by metadata filters.

        Args:
            query_text: Text query for semantic search
            authors: Filter by author names
            topics: Filter by topic names
            categories: Filter by category names
            entities: Filter by entity names
            date_range: Tuple of (start_date, end_date)
            sentiment: Filter by sentiment label
            language: Filter by language code
            limit: Maximum results to return

        Returns:
            List of matching documents with metadata

        Example:
            >>> results = await enricher.search_by_metadata(
            ...     query_text="machine learning",
            ...     categories=["technology"],
            ...     authors=["Dr. Smith"],
            ...     limit=5
            ... )
        """
        logger.info(f"Searching with metadata filters: {locals()}")

        # Build metadata filters
        filters = []

        if authors:
            filters.append({"field": "authors.name", "values": authors})

        if topics:
            filters.append({"field": "topics.name", "values": topics})

        if categories:
            filters.append({"field": "categories.name", "values": categories})

        if entities:
            filters.append({"field": "entities.name", "values": entities})

        if sentiment:
            filters.append({"field": "sentiment.label", "value": sentiment})

        if language:
            filters.append({"field": "language", "value": language})

        # Perform search
        if query_text:
            # Generate query embedding
            query_embedding = await self.embedding_generator.generate(
                query_text
            )
            results = await self.vector_store.search(
                query_vector=query_embedding.vector,
                filters=filters,
                limit=limit,
            )
        else:
            # Filter-only search (no vector similarity)
            results = await self.vector_store.filter_search(
                filters=filters, limit=limit
            )

        logger.info(f"Search returned {len(results)} results")
        return results

    async def update_document_metadata(
        self, doc_id: str, metadata_updates: Dict[str, Any]
    ) -> bool:
        """
        Update metadata for an existing document.

        Args:
            doc_id: Document identifier
            metadata_updates: Dictionary of metadata fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update in vector database
            success = await self.vector_store.update_payload(
                doc_id=doc_id, payload_updates=metadata_updates
            )

            if success:
                logger.info(f"Metadata updated for document: {doc_id}")
            else:
                logger.warning(f"Failed to update metadata for: {doc_id}")

            return success

        except Exception as e:
            logger.error(f"Error updating metadata for {doc_id}: {e}")
            return False

    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the vector database.

        Args:
            doc_id: Document identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            success = await self.vector_store.delete(doc_id)

            if success:
                logger.info(f"Document deleted: {doc_id}")
            else:
                logger.warning(f"Failed to delete document: {doc_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get enrichment statistics.

        Returns:
            Dictionary with statistics
        """
        return self._stats.to_dict()

    async def close(self):
        """Close connections and cleanup resources."""
        logger.info("Closing MetadataEnricher...")
        await self.metadata_extractor.close()
        # Note: embedding_generator and vector_store should be closed
        # by their owners, not here
        logger.info("MetadataEnricher closed")

    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================

    def _generate_doc_id(
        self, text: str, source: Optional[str] = None
    ) -> str:
        """
        Generate a unique document ID based on content and source.

        Args:
            text: Document text
            source: Source identifier

        Returns:
            Unique document ID (SHA256 hash)
        """
        content = f"{text[:1000]}{source or ''}"
        hash_obj = hashlib.sha256(content.encode("utf-8"))
        return hash_obj.hexdigest()[:16]

    async def _store_in_vector_db(
        self, enriched_doc: EnrichedDocument
    ) -> str:
        """
        Store enriched document in vector database.

        Args:
            enriched_doc: EnrichedDocument to store

        Returns:
            Vector ID in database
        """
        payload = enriched_doc.to_vector_payload()

        # Store in vector database
        vector_id = await self.vector_store.insert(
            vector=enriched_doc.embedding,
            payload=payload,
            doc_id=enriched_doc.id,
        )

        return vector_id

    def _update_stats(
        self, success: bool, processing_time: float = 0.0
    ) -> None:
        """
        Update enrichment statistics.

        Args:
            success: Whether enrichment was successful
            processing_time: Processing time in seconds
        """
        self._stats.total_processed += 1

        if success:
            self._stats.successful += 1
        else:
            self._stats.failed += 1

        if processing_time > 0:
            # Update running average
            total_time = (
                self._stats.avg_processing_time
                * (self._stats.total_processed - 1)
            ) + processing_time
            self._stats.avg_processing_time = (
                total_time / self._stats.total_processed
            )
