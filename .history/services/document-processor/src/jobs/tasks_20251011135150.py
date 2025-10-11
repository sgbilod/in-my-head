"""
Celery tasks for document processing pipeline.

This module defines all background tasks for:
- Complete document processing (orchestration)
- Document parsing
- Text preprocessing
- Embedding generation
- Metadata extraction
- Vector storage
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from celery import Task, chain, group
from celery.exceptions import SoftTimeLimitExceeded

from .celery_app import celery_app

logger = logging.getLogger(__name__)


# ============================================================================
# BASE TASK CLASS
# ============================================================================


class BaseTask(Task):
    """
    Base task class with common functionality.

    Provides:
    - Automatic retry on failure
    - Progress tracking
    - Error logging
    - Task state management
    """

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(
            f"Task {self.name} [{task_id}] failed: {exc}",
            exc_info=einfo
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(f"Task {self.name} [{task_id}] succeeded")
        super().on_success(retval, task_id, args, kwargs)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(
            f"Task {self.name} [{task_id}] retrying: {exc}"
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)


# ============================================================================
# ORCHESTRATION TASK
# ============================================================================


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="jobs.tasks.process_document_task"
)
def process_document_task(
    self,
    file_path: str,
    doc_id: Optional[str] = None,
    source: Optional[str] = None,
    collection_name: str = "documents",
) -> Dict[str, Any]:
    """
    Complete document processing pipeline (orchestration task).

    This task chains together all processing steps:
    1. Parse document → Extract text
    2. Preprocess text → Clean and chunk
    3. Generate embeddings → Create vectors
    4. Extract metadata → AI-powered extraction
    5. Store in vector DB → Searchable storage

    Args:
        file_path: Path to document file
        doc_id: Optional document ID
        source: Optional source identifier
        collection_name: Vector DB collection name

    Returns:
        Dictionary with:
        - doc_id: Document identifier
        - status: "completed" or "failed"
        - vector_id: Vector DB identifier
        - metadata: Extracted metadata
        - processing_time: Total time in seconds
        - task_ids: IDs of all subtasks

    Raises:
        Exception: If any step fails after retries
    """
    try:
        start_time = datetime.utcnow()

        # Update task state
        self.update_state(
            state="PROCESSING",
            meta={
                "current": 0,
                "total": 5,
                "status": "Starting document processing..."
            }
        )

        # Create task chain
        task_chain = chain(
            parse_document_task.s(file_path),
            preprocess_text_task.s(),
            group(
                generate_embeddings_task.s(),
                extract_metadata_task.s(),
            ),
            store_in_vector_db_task.s(
                doc_id=doc_id,
                source=source,
                collection_name=collection_name,
            ),
        )

        # Execute chain
        result = task_chain.apply_async()

        # Wait for completion
        final_result = result.get(
            timeout=600,
            propagate=True,
            interval=0.5,
        )

        processing_time = (
            datetime.utcnow() - start_time
        ).total_seconds()

        return {
            "doc_id": final_result.get("doc_id", doc_id),
            "status": "completed",
            "vector_id": final_result.get("vector_id"),
            "metadata": final_result.get("metadata"),
            "processing_time": processing_time,
            "task_id": self.request.id,
            "subtask_ids": [
                result.parent.parent.parent.id,  # Parse
                result.parent.parent.id,          # Preprocess
                result.parent.id,                 # Generate/Extract
                result.id,                        # Store
            ],
        }

    except SoftTimeLimitExceeded:
        logger.error(
            f"Task {self.request.id} exceeded time limit"
        )
        return {
            "doc_id": doc_id,
            "status": "failed",
            "error": "Time limit exceeded",
            "task_id": self.request.id,
        }

    except Exception as e:
        logger.error(
            f"Document processing failed for {file_path}: {e}",
            exc_info=True
        )
        return {
            "doc_id": doc_id,
            "status": "failed",
            "error": str(e),
            "task_id": self.request.id,
        }


# ============================================================================
# PARSING TASK
# ============================================================================


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="jobs.tasks.parse_document_task"
)
def parse_document_task(
    self,
    file_path: str
) -> Dict[str, Any]:
    """
    Parse document and extract text.

    Args:
        file_path: Path to document file

    Returns:
        Dictionary with:
        - text: Extracted text content
        - metadata: Document metadata
        - file_path: Original file path

    Raises:
        Exception: If parsing fails
    """
    try:
        self.update_state(
            state="PARSING",
            meta={"status": f"Parsing {file_path}..."}
        )

        # Import here to avoid circular imports
        from parsers import ParserFactory

        # Detect format and parse
        parser = ParserFactory.create_parser(file_path)
        result = parser.parse(file_path)

        logger.info(
            f"Parsed document: {file_path} "
            f"({len(result.content)} chars)"
        )

        return {
            "text": result.content,
            "metadata": result.metadata,
            "file_path": file_path,
        }

    except Exception as e:
        logger.error(f"Parsing failed for {file_path}: {e}")
        raise


# ============================================================================
# PREPROCESSING TASK
# ============================================================================


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="jobs.tasks.preprocess_text_task"
)
def preprocess_text_task(
    self,
    parse_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Preprocess text (clean, normalize, chunk).

    Args:
        parse_result: Result from parse_document_task

    Returns:
        Dictionary with:
        - text: Preprocessed text
        - chunks: List of text chunks
        - metadata: Original metadata
        - file_path: Original file path

    Raises:
        Exception: If preprocessing fails
    """
    try:
        self.update_state(
            state="PREPROCESSING",
            meta={"status": "Preprocessing text..."}
        )

        # Import here to avoid circular imports
        from preprocessing import TextCleaner, TextChunker

        text = parse_result["text"]

        # Clean text
        cleaner = TextCleaner()
        cleaned_text = cleaner.clean(text)

        # Chunk text
        chunker = TextChunker(chunk_size=1000, overlap=200)
        chunks = chunker.chunk(cleaned_text)

        logger.info(
            f"Preprocessed text: {len(cleaned_text)} chars, "
            f"{len(chunks)} chunks"
        )

        return {
            "text": cleaned_text,
            "chunks": [chunk.text for chunk in chunks],
            "metadata": parse_result.get("metadata", {}),
            "file_path": parse_result.get("file_path"),
        }

    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise


# ============================================================================
# EMBEDDING GENERATION TASK
# ============================================================================


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="jobs.tasks.generate_embeddings_task"
)
def generate_embeddings_task(
    self,
    preprocess_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate embeddings for text.

    Args:
        preprocess_result: Result from preprocess_text_task

    Returns:
        Dictionary with:
        - embedding: Vector embedding (3072-dim)
        - text: Original text
        - chunks: Text chunks
        - metadata: Original metadata
        - file_path: Original file path

    Raises:
        Exception: If embedding generation fails
    """
    try:
        self.update_state(
            state="GENERATING_EMBEDDINGS",
            meta={"status": "Generating embeddings..."}
        )

        # Import here to avoid circular imports
        import asyncio
        from embeddings import EmbeddingGenerator

        text = preprocess_result["text"]

        # Initialize generator
        generator = EmbeddingGenerator(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="text-embedding-3-large",
        )

        # Generate embedding (async)
        loop = asyncio.get_event_loop()
        embedding_result = loop.run_until_complete(
            generator.generate(text)
        )

        logger.info(
            f"Generated embedding: {len(embedding_result.vector)}D"
        )

        return {
            "embedding": embedding_result.vector,
            "text": text,
            "chunks": preprocess_result.get("chunks", []),
            "metadata": preprocess_result.get("metadata", {}),
            "file_path": preprocess_result.get("file_path"),
        }

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise


# ============================================================================
# METADATA EXTRACTION TASK
# ============================================================================


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="jobs.tasks.extract_metadata_task"
)
def extract_metadata_task(
    self,
    preprocess_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract metadata using AI.

    Args:
        preprocess_result: Result from preprocess_text_task

    Returns:
        Dictionary with:
        - extracted_metadata: AI-extracted metadata
        - text: Original text
        - chunks: Text chunks
        - metadata: Original metadata
        - file_path: Original file path

    Raises:
        Exception: If metadata extraction fails
    """
    try:
        self.update_state(
            state="EXTRACTING_METADATA",
            meta={"status": "Extracting metadata..."}
        )

        # Import here to avoid circular imports
        import asyncio
        from metadata import MetadataExtractor

        text = preprocess_result["text"]

        # Initialize extractor
        extractor = MetadataExtractor(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
        )

        # Extract metadata (async)
        loop = asyncio.get_event_loop()
        extracted_metadata = loop.run_until_complete(
            extractor.extract(text, use_cache=True)
        )

        # Close extractor
        loop.run_until_complete(extractor.close())

        logger.info("Metadata extracted successfully")

        return {
            "extracted_metadata": {
                "authors": [
                    a.to_dict() for a in extracted_metadata.authors
                ],
                "topics": [
                    t.to_dict() for t in extracted_metadata.topics
                ],
                "entities": [
                    e.to_dict() for e in extracted_metadata.entities
                ],
                "categories": [
                    c.to_dict() for c in extracted_metadata.categories
                ],
                "summary": extracted_metadata.summary,
                "keywords": extracted_metadata.keywords,
                "title": extracted_metadata.title,
                "language": extracted_metadata.language,
            },
            "text": text,
            "chunks": preprocess_result.get("chunks", []),
            "metadata": preprocess_result.get("metadata", {}),
            "file_path": preprocess_result.get("file_path"),
        }

    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        raise


# ============================================================================
# VECTOR STORAGE TASK
# ============================================================================


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="jobs.tasks.store_in_vector_db_task"
)
def store_in_vector_db_task(
    self,
    combined_results: List[Dict[str, Any]],
    doc_id: Optional[str] = None,
    source: Optional[str] = None,
    collection_name: str = "documents",
) -> Dict[str, Any]:
    """
    Store document in vector database.

    Args:
        combined_results: Results from embedding and metadata tasks
        doc_id: Optional document ID
        source: Optional source identifier
        collection_name: Vector DB collection name

    Returns:
        Dictionary with:
        - doc_id: Document identifier
        - vector_id: Vector DB identifier
        - metadata: Stored metadata

    Raises:
        Exception: If storage fails
    """
    try:
        self.update_state(
            state="STORING",
            meta={"status": "Storing in vector database..."}
        )

        # Import here to avoid circular imports
        import asyncio
        from vector_storage import VectorStore

        # Combine results from embedding and metadata tasks
        embedding_result = combined_results[0]
        metadata_result = combined_results[1]

        # Generate doc_id if not provided
        if doc_id is None:
            import hashlib
            text = embedding_result["text"]
            doc_id = hashlib.sha256(
                text[:1000].encode("utf-8")
            ).hexdigest()[:16]

        # Initialize vector store
        store = VectorStore(
            collection_name=collection_name,
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
        )

        # Prepare payload
        payload = {
            "id": doc_id,
            "text": embedding_result["text"][:1000],
            "source": source or embedding_result.get("file_path"),
            **metadata_result["extracted_metadata"],
        }

        # Store in vector DB (async)
        loop = asyncio.get_event_loop()
        vector_id = loop.run_until_complete(
            store.insert(
                vector=embedding_result["embedding"],
                payload=payload,
                doc_id=doc_id,
            )
        )

        logger.info(f"Stored in vector DB: {vector_id}")

        return {
            "doc_id": doc_id,
            "vector_id": vector_id,
            "metadata": metadata_result["extracted_metadata"],
        }

    except Exception as e:
        logger.error(f"Vector storage failed: {e}")
        raise


# ============================================================================
# CLEANUP TASK
# ============================================================================


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="jobs.tasks.cleanup_expired_jobs"
)
def cleanup_expired_jobs(self) -> Dict[str, int]:
    """
    Cleanup expired job results from Redis.

    This is a periodic task that runs every hour.

    Returns:
        Dictionary with cleanup statistics
    """
    try:
        # Import here to avoid circular imports
        from .job_manager import JobManager

        manager = JobManager()
        deleted_count = manager.cleanup_expired_jobs()

        logger.info(f"Cleaned up {deleted_count} expired jobs")

        return {
            "deleted_count": deleted_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise
