"""
Comprehensive tests for background job processing.

Tests cover:
- Celery task execution
- Job manager functionality
- Job status tracking
- Progress monitoring
- Batch processing
- Error handling and retries
"""

import sys
import os
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from jobs import (
    JobManager,
    JobStatus,
    JobResult,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_mock = Mock()
    redis_mock.keys.return_value = []
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.close.return_value = None
    return redis_mock


@pytest.fixture
def job_manager(mock_redis):
    """JobManager instance with mocked Redis."""
    with patch("jobs.job_manager.redis.Redis") as mock_redis_class:
        mock_redis_class.return_value = mock_redis
        manager = JobManager()
        yield manager
        manager.close()


@pytest.fixture
def sample_job_result():
    """Sample JobResult."""
    return JobResult(
        job_id="test-job-123",
        status=JobStatus.PENDING,
        created_at=datetime.utcnow(),
        metadata={"file_path": "test.pdf"},
    )


# ============================================================================
# TEST JOB STATUS
# ============================================================================


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_status_values(self):
        """Test that all status values are strings."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.STARTED.value == "started"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.SUCCESS.value == "success"
        assert JobStatus.FAILURE.value == "failure"
        assert JobStatus.REVOKED.value == "revoked"

    def test_status_comparison(self):
        """Test status comparison."""
        assert JobStatus.PENDING == "pending"
        assert JobStatus.SUCCESS == "success"


# ============================================================================
# TEST JOB RESULT
# ============================================================================


class TestJobResult:
    """Tests for JobResult dataclass."""

    def test_creation(self, sample_job_result):
        """Test JobResult creation."""
        assert sample_job_result.job_id == "test-job-123"
        assert sample_job_result.status == JobStatus.PENDING
        assert isinstance(sample_job_result.created_at, datetime)
        assert sample_job_result.started_at is None
        assert sample_job_result.completed_at is None
        assert sample_job_result.result is None
        assert sample_job_result.error is None

    def test_to_dict(self, sample_job_result):
        """Test conversion to dictionary."""
        data = sample_job_result.to_dict()

        assert data["job_id"] == "test-job-123"
        assert data["status"] == "pending"
        assert isinstance(data["created_at"], str)
        assert "duration" not in data  # No duration without completion

    def test_to_dict_with_duration(self):
        """Test dictionary includes duration when completed."""
        result = JobResult(
            job_id="test-job-123",
            status=JobStatus.SUCCESS,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow() + timedelta(seconds=10),
        )

        data = result.to_dict()
        assert "duration" in data
        assert data["duration"] >= 10.0

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "job_id": "test-job-456",
            "status": "success",
            "created_at": "2025-10-11T12:00:00",
            "started_at": "2025-10-11T12:00:01",
            "completed_at": "2025-10-11T12:00:11",
            "result": {"doc_id": "doc123"},
            "error": None,
            "progress": {},
            "retries": 0,
            "metadata": {},
        }

        result = JobResult.from_dict(data)

        assert result.job_id == "test-job-456"
        assert result.status == JobStatus.SUCCESS
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.started_at, datetime)
        assert isinstance(result.completed_at, datetime)
        assert result.result == {"doc_id": "doc123"}

    def test_round_trip_serialization(self, sample_job_result):
        """Test round-trip serialization."""
        # Add some data
        sample_job_result.started_at = datetime.utcnow()
        sample_job_result.completed_at = datetime.utcnow()
        sample_job_result.result = {"doc_id": "doc123"}
        sample_job_result.status = JobStatus.SUCCESS

        # Convert to dict and back
        data = sample_job_result.to_dict()
        restored = JobResult.from_dict(data)

        assert restored.job_id == sample_job_result.job_id
        assert restored.status == sample_job_result.status
        assert restored.result == sample_job_result.result


# ============================================================================
# TEST JOB MANAGER
# ============================================================================


class TestJobManager:
    """Tests for JobManager."""

    def test_initialization(self, job_manager):
        """Test JobManager initialization."""
        assert job_manager.redis_client is not None
        assert job_manager.result_ttl == 86400

    @patch("jobs.job_manager.process_document_task")
    def test_submit_document(self, mock_task, job_manager):
        """Test document submission."""
        # Mock task result
        mock_result = Mock()
        mock_result.id = "task-123"
        mock_task.apply_async.return_value = mock_result

        # Submit document
        job_id = job_manager.submit_document(
            file_path="test.pdf",
            doc_id="doc123",
        )

        assert job_id == "task-123"

        # Verify task was called
        mock_task.apply_async.assert_called_once()
        args, kwargs = mock_task.apply_async.call_args
        assert kwargs["args"] == ["test.pdf"]
        assert kwargs["kwargs"]["doc_id"] == "doc123"

    @patch("jobs.job_manager.process_document_task")
    def test_submit_batch(self, mock_task, job_manager):
        """Test batch submission."""
        # Mock task results
        mock_task.apply_async.side_effect = [
            Mock(id=f"task-{i}") for i in range(3)
        ]

        # Submit batch
        job_ids = job_manager.submit_batch(
            file_paths=["doc1.pdf", "doc2.docx", "doc3.txt"],
            doc_ids=["doc1", "doc2", "doc3"],
        )

        assert len(job_ids) == 3
        assert job_ids == ["task-0", "task-1", "task-2"]
        assert mock_task.apply_async.call_count == 3

    @patch("jobs.job_manager.AsyncResult")
    def test_get_job_status_pending(
        self, mock_async_result, job_manager, mock_redis
    ):
        """Test getting pending job status."""
        # Mock Celery result
        mock_result = Mock()
        mock_result.state = "PENDING"
        mock_result.info = None
        mock_async_result.return_value = mock_result

        # Mock Redis response (no cached result)
        mock_redis.get.return_value = None

        # Get status
        result = job_manager.get_job_status("job-123")

        assert result.job_id == "job-123"
        assert result.status == JobStatus.PENDING

    @patch("jobs.job_manager.AsyncResult")
    def test_get_job_status_success(
        self, mock_async_result, job_manager, mock_redis
    ):
        """Test getting successful job status."""
        # Mock Celery result
        mock_result = Mock()
        mock_result.state = "SUCCESS"
        mock_result.result = {"doc_id": "doc123", "vector_id": "vec123"}
        mock_async_result.return_value = mock_result

        # Mock Redis response
        mock_redis.get.return_value = None

        # Get status
        result = job_manager.get_job_status("job-123")

        assert result.job_id == "job-123"
        assert result.status == JobStatus.SUCCESS
        assert result.result == {"doc_id": "doc123", "vector_id": "vec123"}
        assert result.completed_at is not None

    @patch("jobs.job_manager.AsyncResult")
    def test_get_job_status_failure(
        self, mock_async_result, job_manager, mock_redis
    ):
        """Test getting failed job status."""
        # Mock Celery result
        mock_result = Mock()
        mock_result.state = "FAILURE"
        mock_result.info = Exception("Processing failed")
        mock_async_result.return_value = mock_result

        # Mock Redis response
        mock_redis.get.return_value = None

        # Get status
        result = job_manager.get_job_status("job-123")

        assert result.job_id == "job-123"
        assert result.status == JobStatus.FAILURE
        assert "Processing failed" in result.error
        assert result.completed_at is not None

    @patch("jobs.job_manager.AsyncResult")
    def test_get_batch_status(
        self, mock_async_result, job_manager, mock_redis
    ):
        """Test getting batch status."""
        # Mock Celery results
        def create_mock_result(state):
            mock_result = Mock()
            mock_result.state = state
            mock_result.info = None
            mock_result.result = None
            return mock_result

        mock_async_result.side_effect = [
            create_mock_result("SUCCESS"),
            create_mock_result("PROCESSING"),
            create_mock_result("FAILURE"),
        ]

        # Mock Redis
        mock_redis.get.return_value = None

        # Get batch status
        job_ids = ["job-1", "job-2", "job-3"]
        results = job_manager.get_batch_status(job_ids)

        assert len(results) == 3
        assert results["job-1"].status == JobStatus.SUCCESS
        assert results["job-2"].status == JobStatus.PROCESSING
        assert results["job-3"].status == JobStatus.FAILURE

    @patch("jobs.job_manager.celery_app")
    def test_cancel_job(self, mock_celery, job_manager, mock_redis):
        """Test job cancellation."""
        # Mock Redis
        mock_redis.get.return_value = None

        # Cancel job
        success = job_manager.cancel_job("job-123")

        assert success is True
        mock_celery.control.revoke.assert_called_once_with(
            "job-123",
            terminate=True,
            signal="SIGKILL",
        )

    @patch("jobs.job_manager.celery_app")
    def test_cancel_batch(self, mock_celery, job_manager, mock_redis):
        """Test batch cancellation."""
        # Mock Redis
        mock_redis.get.return_value = None

        # Cancel batch
        job_ids = ["job-1", "job-2", "job-3"]
        cancelled = job_manager.cancel_batch(job_ids)

        assert cancelled == 3
        assert mock_celery.control.revoke.call_count == 3

    def test_get_statistics_empty(self, job_manager, mock_redis):
        """Test statistics with no jobs."""
        # Mock Redis (no jobs)
        mock_redis.keys.return_value = []

        # Get statistics
        stats = job_manager.get_statistics()

        assert stats["total_jobs"] == 0
        assert stats["pending"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0
        assert stats["avg_duration"] == 0.0

    def test_get_statistics_with_jobs(self, job_manager, mock_redis):
        """Test statistics with jobs."""
        import json

        # Create mock jobs
        jobs = [
            JobResult(
                job_id="job-1",
                status=JobStatus.SUCCESS,
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow() + timedelta(seconds=10),
            ),
            JobResult(
                job_id="job-2",
                status=JobStatus.FAILURE,
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow() + timedelta(seconds=5),
            ),
            JobResult(
                job_id="job-3",
                status=JobStatus.PENDING,
                created_at=datetime.utcnow(),
            ),
        ]

        # Mock Redis responses
        mock_redis.keys.return_value = [
            "job:job-1",
            "job:job-2",
            "job:job-3",
        ]

        mock_redis.get.side_effect = [
            json.dumps(job.to_dict()) for job in jobs
        ]

        # Get statistics
        stats = job_manager.get_statistics()

        assert stats["total_jobs"] == 3
        assert stats["pending"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["avg_duration"] > 0
        assert stats["success_rate"] == 1/3
        assert stats["failure_rate"] == 1/3

    def test_cleanup_expired_jobs(self, job_manager, mock_redis):
        """Test cleanup of expired jobs."""
        import json

        # Create expired and active jobs
        expired_job = JobResult(
            job_id="expired-job",
            status=JobStatus.SUCCESS,
            created_at=datetime.utcnow() - timedelta(days=2),
            completed_at=datetime.utcnow() - timedelta(days=2),
        )

        active_job = JobResult(
            job_id="active-job",
            status=JobStatus.SUCCESS,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        # Mock Redis
        mock_redis.keys.return_value = [
            "job:expired-job",
            "job:active-job",
        ]

        mock_redis.get.side_effect = [
            json.dumps(expired_job.to_dict()),
            json.dumps(active_job.to_dict()),
        ]

        mock_redis.delete.return_value = 1

        # Cleanup
        deleted = job_manager.cleanup_expired_jobs()

        assert deleted == 1
        mock_redis.delete.assert_called_once_with("job:expired-job")


# ============================================================================
# TEST TASK EXECUTION (MOCKED)
# ============================================================================


class TestTaskExecution:
    """Tests for task execution (mocked)."""

    @patch("jobs.tasks.ParserFactory")
    def test_parse_document_task(self, mock_factory):
        """Test parse_document_task."""
        from jobs.tasks import parse_document_task

        # Mock parser
        mock_parser = Mock()
        mock_result = Mock()
        mock_result.content = "Test content"
        mock_result.metadata = {"title": "Test"}
        mock_parser.parse.return_value = mock_result
        mock_factory.create_parser.return_value = mock_parser

        # Execute task
        result = parse_document_task("test.pdf")

        assert result["text"] == "Test content"
        assert result["metadata"] == {"title": "Test"}
        assert result["file_path"] == "test.pdf"

    @patch("jobs.tasks.TextCleaner")
    @patch("jobs.tasks.TextChunker")
    def test_preprocess_text_task(self, mock_chunker_class, mock_cleaner_class):
        """Test preprocess_text_task."""
        from jobs.tasks import preprocess_text_task

        # Mock cleaner
        mock_cleaner = Mock()
        mock_cleaner.clean.return_value = "Cleaned text"
        mock_cleaner_class.return_value = mock_cleaner

        # Mock chunker
        mock_chunk = Mock()
        mock_chunk.text = "Chunk 1"
        mock_chunker = Mock()
        mock_chunker.chunk.return_value = [mock_chunk]
        mock_chunker_class.return_value = mock_chunker

        # Execute task
        parse_result = {
            "text": "Original text",
            "metadata": {},
            "file_path": "test.pdf",
        }

        result = preprocess_text_task(parse_result)

        assert result["text"] == "Cleaned text"
        assert result["chunks"] == ["Chunk 1"]
        assert "metadata" in result


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
