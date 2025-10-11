"""
Background job processing for In My Head.

This package provides Celery-based background job processing for:
- Document parsing and text extraction
- Text preprocessing and chunking
- Embedding generation
- Metadata extraction with AI
- Vector storage and indexing

All operations are performed asynchronously with:
- Job retry logic
- Progress tracking
- Result persistence
- Error handling
- Task monitoring
"""

from .celery_app import celery_app
from .tasks import (
    process_document_task,
    parse_document_task,
    preprocess_text_task,
    generate_embeddings_task,
    extract_metadata_task,
    store_in_vector_db_task,
)
from .job_manager import JobManager, JobStatus, JobResult

__all__ = [
    "celery_app",
    "process_document_task",
    "parse_document_task",
    "preprocess_text_task",
    "generate_embeddings_task",
    "extract_metadata_task",
    "store_in_vector_db_task",
    "JobManager",
    "JobStatus",
    "JobResult",
]
