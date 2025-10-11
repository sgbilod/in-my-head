"""
Job manager for tracking and managing background jobs.

This module provides:
- Job status tracking
- Progress monitoring
- Result retrieval
- Job cancellation
- Statistics and metrics
"""

import json
import logging
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import redis
from celery.result import AsyncResult

from .celery_app import celery_app

logger = logging.getLogger(__name__)


# ============================================================================
# JOB STATUS ENUM
# ============================================================================


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    STARTED = "started"
    PROCESSING = "processing"
    PARSING = "parsing"
    PREPROCESSING = "preprocessing"
    GENERATING_EMBEDDINGS = "generating_embeddings"
    EXTRACTING_METADATA = "extracting_metadata"
    STORING = "storing"
    SUCCESS = "success"
    FAILURE = "failure"
    REVOKED = "revoked"
    RETRY = "retry"


# ============================================================================
# JOB RESULT DATACLASS
# ============================================================================


@dataclass
class JobResult:
    """
    Job result container.

    Attributes:
        job_id: Unique job identifier (Celery task ID)
        status: Current job status
        created_at: Job creation timestamp
        started_at: Job start timestamp
        completed_at: Job completion timestamp
        result: Job result data (if completed)
        error: Error message (if failed)
        progress: Progress information (current, total, status)
        retries: Number of retry attempts
        metadata: Additional metadata
    """

    job_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)

        # Convert datetime to ISO format
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()

        # Convert status to string
        data["status"] = self.status.value

        # Calculate duration
        if self.started_at and self.completed_at:
            duration = (
                self.completed_at - self.started_at
            ).total_seconds()
            data["duration"] = duration

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobResult":
        """Create from dictionary."""
        # Convert ISO format to datetime
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(
                data["created_at"]
            )
        if isinstance(data.get("started_at"), str):
            data["started_at"] = datetime.fromisoformat(
                data["started_at"]
            )
        if isinstance(data.get("completed_at"), str):
            data["completed_at"] = datetime.fromisoformat(
                data["completed_at"]
            )

        # Convert status to enum
        if isinstance(data.get("status"), str):
            data["status"] = JobStatus(data["status"])

        # Remove computed fields
        data.pop("duration", None)

        return cls(**data)


# ============================================================================
# JOB MANAGER
# ============================================================================


class JobManager:
    """
    Manager for background jobs.

    Provides:
    - Job submission
    - Status tracking
    - Progress monitoring
    - Result retrieval
    - Job cancellation
    - Statistics
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 1,  # Use different DB than Celery
        result_ttl: int = 86400,  # 24 hours
    ):
        """
        Initialize job manager.

        Args:
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database number
            result_ttl: Result time-to-live in seconds
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
        )
        self.result_ttl = result_ttl

        logger.info(
            f"JobManager initialized with Redis "
            f"{redis_host}:{redis_port}/{redis_db}"
        )

    # ========================================================================
    # JOB SUBMISSION
    # ========================================================================

    def submit_document(
        self,
        file_path: str,
        doc_id: Optional[str] = None,
        source: Optional[str] = None,
        collection_name: str = "documents",
        priority: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Submit document for processing.

        Args:
            file_path: Path to document file
            doc_id: Optional document ID
            source: Optional source identifier
            collection_name: Vector DB collection name
            priority: Task priority (0-10, higher = more important)
            metadata: Optional additional metadata

        Returns:
            Job ID (Celery task ID)

        Example:
            >>> manager = JobManager()
            >>> job_id = manager.submit_document("document.pdf")
            >>> print(f"Job submitted: {job_id}")
        """
        from .tasks import process_document_task

        # Submit task with priority
        result = process_document_task.apply_async(
            args=[file_path],
            kwargs={
                "doc_id": doc_id,
                "source": source,
                "collection_name": collection_name,
            },
            priority=priority,
        )

        job_id = result.id

        # Store initial job state
        job_result = JobResult(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata=metadata or {},
        )

        self._store_job_result(job_result)

        logger.info(f"Submitted job {job_id} for {file_path}")

        return job_id

    def submit_batch(
        self,
        file_paths: List[str],
        doc_ids: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        collection_name: str = "documents",
        priority: int = 5,
    ) -> List[str]:
        """
        Submit batch of documents for processing.

        Args:
            file_paths: List of document file paths
            doc_ids: Optional list of document IDs
            sources: Optional list of source identifiers
            collection_name: Vector DB collection name
            priority: Task priority (0-10)

        Returns:
            List of job IDs

        Example:
            >>> manager = JobManager()
            >>> job_ids = manager.submit_batch([
            ...     "doc1.pdf",
            ...     "doc2.docx",
            ...     "doc3.txt"
            ... ])
            >>> print(f"Submitted {len(job_ids)} jobs")
        """
        job_ids = []

        # Prepare parameters
        doc_ids = doc_ids or [None] * len(file_paths)
        sources = sources or [None] * len(file_paths)

        # Submit each document
        for file_path, doc_id, source in zip(
            file_paths, doc_ids, sources
        ):
            job_id = self.submit_document(
                file_path=file_path,
                doc_id=doc_id,
                source=source,
                collection_name=collection_name,
                priority=priority,
            )
            job_ids.append(job_id)

        logger.info(f"Submitted batch of {len(job_ids)} jobs")

        return job_ids

    # ========================================================================
    # JOB STATUS & PROGRESS
    # ========================================================================

    def get_job_status(self, job_id: str) -> JobResult:
        """
        Get job status and result.

        Args:
            job_id: Job identifier

        Returns:
            JobResult with current status and result

        Example:
            >>> manager = JobManager()
            >>> result = manager.get_job_status(job_id)
            >>> print(f"Status: {result.status}")
            >>> if result.status == JobStatus.SUCCESS:
            ...     print(f"Result: {result.result}")
        """
        # Get from Redis cache first
        cached_result = self._get_job_result(job_id)

        # Get from Celery
        celery_result = AsyncResult(job_id, app=celery_app)

        # Update cached result with Celery state
        if cached_result:
            job_result = cached_result
        else:
            job_result = JobResult(
                job_id=job_id,
                status=JobStatus.PENDING,
                created_at=datetime.utcnow(),
            )

        # Map Celery state to JobStatus
        state_mapping = {
            "PENDING": JobStatus.PENDING,
            "STARTED": JobStatus.STARTED,
            "PROCESSING": JobStatus.PROCESSING,
            "PARSING": JobStatus.PARSING,
            "PREPROCESSING": JobStatus.PREPROCESSING,
            "GENERATING_EMBEDDINGS": JobStatus.GENERATING_EMBEDDINGS,
            "EXTRACTING_METADATA": JobStatus.EXTRACTING_METADATA,
            "STORING": JobStatus.STORING,
            "SUCCESS": JobStatus.SUCCESS,
            "FAILURE": JobStatus.FAILURE,
            "REVOKED": JobStatus.REVOKED,
            "RETRY": JobStatus.RETRY,
        }

        job_result.status = state_mapping.get(
            celery_result.state,
            JobStatus.PENDING,
        )

        # Update progress
        if celery_result.state in ["PROCESSING", "PARSING",
                                    "PREPROCESSING", "GENERATING_EMBEDDINGS",
                                    "EXTRACTING_METADATA", "STORING"]:
            job_result.progress = celery_result.info or {}

            if not job_result.started_at:
                job_result.started_at = datetime.utcnow()

        # Update result
        if celery_result.state == "SUCCESS":
            job_result.result = celery_result.result
            job_result.completed_at = datetime.utcnow()

        # Update error
        if celery_result.state == "FAILURE":
            job_result.error = str(celery_result.info)
            job_result.completed_at = datetime.utcnow()

        # Store updated result
        self._store_job_result(job_result)

        return job_result

    def get_batch_status(
        self,
        job_ids: List[str]
    ) -> Dict[str, JobResult]:
        """
        Get status for multiple jobs.

        Args:
            job_ids: List of job identifiers

        Returns:
            Dictionary mapping job_id to JobResult

        Example:
            >>> manager = JobManager()
            >>> results = manager.get_batch_status(job_ids)
            >>> completed = sum(
            ...     1 for r in results.values()
            ...     if r.status == JobStatus.SUCCESS
            ... )
            >>> print(f"{completed}/{len(job_ids)} completed")
        """
        results = {}

        for job_id in job_ids:
            results[job_id] = self.get_job_status(job_id)

        return results

    # ========================================================================
    # JOB CONTROL
    # ========================================================================

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.

        Args:
            job_id: Job identifier

        Returns:
            True if cancelled successfully

        Example:
            >>> manager = JobManager()
            >>> success = manager.cancel_job(job_id)
            >>> if success:
            ...     print("Job cancelled")
        """
        try:
            celery_app.control.revoke(
                job_id,
                terminate=True,
                signal="SIGKILL",
            )

            # Update job result
            job_result = self.get_job_status(job_id)
            job_result.status = JobStatus.REVOKED
            job_result.completed_at = datetime.utcnow()
            self._store_job_result(job_result)

            logger.info(f"Cancelled job {job_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False

    def cancel_batch(self, job_ids: List[str]) -> int:
        """
        Cancel multiple jobs.

        Args:
            job_ids: List of job identifiers

        Returns:
            Number of jobs cancelled successfully

        Example:
            >>> manager = JobManager()
            >>> cancelled = manager.cancel_batch(job_ids)
            >>> print(f"Cancelled {cancelled} jobs")
        """
        cancelled = 0

        for job_id in job_ids:
            if self.cancel_job(job_id):
                cancelled += 1

        return cancelled

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get job processing statistics.

        Returns:
            Dictionary with statistics:
            - total_jobs: Total number of jobs
            - pending: Number of pending jobs
            - processing: Number of processing jobs
            - completed: Number of completed jobs
            - failed: Number of failed jobs
            - avg_duration: Average job duration

        Example:
            >>> manager = JobManager()
            >>> stats = manager.get_statistics()
            >>> print(f"Total: {stats['total_jobs']}")
            >>> print(f"Success rate: {stats['success_rate']:.1%}")
        """
        # Get all job keys
        job_keys = self.redis_client.keys("job:*")

        stats = {
            "total_jobs": len(job_keys),
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "avg_duration": 0.0,
        }

        durations = []

        for key in job_keys:
            job_data = self.redis_client.get(key)
            if not job_data:
                continue

            try:
                result = JobResult.from_dict(
                    json.loads(job_data)
                )

                # Count by status
                if result.status == JobStatus.PENDING:
                    stats["pending"] += 1
                elif result.status in [
                    JobStatus.PROCESSING,
                    JobStatus.PARSING,
                    JobStatus.PREPROCESSING,
                    JobStatus.GENERATING_EMBEDDINGS,
                    JobStatus.EXTRACTING_METADATA,
                    JobStatus.STORING,
                ]:
                    stats["processing"] += 1
                elif result.status == JobStatus.SUCCESS:
                    stats["completed"] += 1
                elif result.status == JobStatus.FAILURE:
                    stats["failed"] += 1
                elif result.status == JobStatus.REVOKED:
                    stats["cancelled"] += 1

                # Calculate duration
                if result.started_at and result.completed_at:
                    duration = (
                        result.completed_at - result.started_at
                    ).total_seconds()
                    durations.append(duration)

            except Exception as e:
                logger.warning(f"Failed to parse job data: {e}")
                continue

        # Calculate average duration
        if durations:
            stats["avg_duration"] = sum(durations) / len(durations)

        # Calculate rates
        if stats["total_jobs"] > 0:
            stats["success_rate"] = (
                stats["completed"] / stats["total_jobs"]
            )
            stats["failure_rate"] = (
                stats["failed"] / stats["total_jobs"]
            )
        else:
            stats["success_rate"] = 0.0
            stats["failure_rate"] = 0.0

        return stats

    # ========================================================================
    # CLEANUP
    # ========================================================================

    def cleanup_expired_jobs(self) -> int:
        """
        Cleanup expired job results.

        Returns:
            Number of jobs deleted

        Example:
            >>> manager = JobManager()
            >>> deleted = manager.cleanup_expired_jobs()
            >>> print(f"Deleted {deleted} expired jobs")
        """
        deleted = 0
        expiry_time = datetime.utcnow() - timedelta(
            seconds=self.result_ttl
        )

        job_keys = self.redis_client.keys("job:*")

        for key in job_keys:
            job_data = self.redis_client.get(key)
            if not job_data:
                continue

            try:
                result = JobResult.from_dict(
                    json.loads(job_data)
                )

                # Delete if expired
                if (result.completed_at and
                    result.completed_at < expiry_time):
                    self.redis_client.delete(key)
                    deleted += 1

            except Exception as e:
                logger.warning(
                    f"Failed to parse job data for cleanup: {e}"
                )
                continue

        logger.info(f"Cleaned up {deleted} expired jobs")

        return deleted

    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================

    def _store_job_result(self, job_result: JobResult) -> None:
        """Store job result in Redis."""
        key = f"job:{job_result.job_id}"
        value = json.dumps(job_result.to_dict())

        self.redis_client.setex(
            key,
            self.result_ttl,
            value,
        )

    def _get_job_result(
        self,
        job_id: str
    ) -> Optional[JobResult]:
        """Get job result from Redis."""
        key = f"job:{job_id}"
        value = self.redis_client.get(key)

        if not value:
            return None

        try:
            return JobResult.from_dict(json.loads(value))
        except Exception as e:
            logger.warning(
                f"Failed to parse job result for {job_id}: {e}"
            )
            return None

    def close(self):
        """Close Redis connection."""
        self.redis_client.close()
        logger.info("JobManager closed")
