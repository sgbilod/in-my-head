"""
Tests for API endpoints.

Tests:
- Authentication
- Rate limiting
- Document upload
- Job status
- Search
- WebSocket
- Health check
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import after path setup
from src.app import app
from src.api.auth import generate_api_key, verify_api_key
from src.api.rate_limiter import RateLimiter


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def api_key():
    """Valid API key."""
    # Set test API key
    os.environ["API_KEYS"] = "test-api-key-123"
    return "test-api-key-123"


@pytest.fixture
def headers(api_key):
    """Request headers with API key."""
    return {"X-API-Key": api_key}


@pytest.fixture
def mock_job_manager():
    """Mock JobManager."""
    with patch("src.api.routes_documents.job_manager") as mock:
        yield mock


@pytest.fixture
def mock_vector_store():
    """Mock VectorStore."""
    with patch("src.api.routes_search.vector_store") as mock:
        yield mock


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================


class TestAuthentication:
    """Test authentication."""
    
    def test_generate_api_key(self):
        """Test API key generation."""
        key1 = generate_api_key()
        key2 = generate_api_key()
        
        assert len(key1) == 64  # 32 bytes hex
        assert len(key2) == 64
        assert key1 != key2  # Should be unique
    
    def test_verify_api_key_valid(self):
        """Test API key verification with valid key."""
        os.environ["API_KEYS"] = "key1,key2,key3"
        
        assert verify_api_key("key1") is True
        assert verify_api_key("key2") is True
        assert verify_api_key("key3") is True
    
    def test_verify_api_key_invalid(self):
        """Test API key verification with invalid key."""
        os.environ["API_KEYS"] = "key1,key2,key3"
        
        assert verify_api_key("invalid") is False
    
    def test_verify_api_key_no_config(self):
        """Test API key verification with no config (dev mode)."""
        os.environ["API_KEYS"] = ""
        
        # In dev mode, all keys are valid
        assert verify_api_key("anything") is True
    
    def test_endpoint_without_api_key(self, client):
        """Test endpoint without API key."""
        response = client.get("/api/v1/statistics")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "API key is required" in response.json()["detail"]
    
    def test_endpoint_with_invalid_api_key(self, client):
        """Test endpoint with invalid API key."""
        os.environ["API_KEYS"] = "valid-key"
        
        response = client.get(
            "/api/v1/statistics",
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid API key" in response.json()["detail"]
    
    def test_endpoint_with_valid_api_key(self, client, headers, mock_job_manager):
        """Test endpoint with valid API key."""
        mock_job_manager.get_stats.return_value = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "success_rate": 0.0,
        }
        
        response = client.get("/api/v1/statistics", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================


class TestRateLimiting:
    """Test rate limiting."""
    
    def test_rate_limiter_init(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(
            max_requests=10,
            window_seconds=60,
        )
        
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60
    
    def test_rate_limiter_allow(self):
        """Test rate limiter allows requests."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # First 5 requests should be allowed
        for i in range(5):
            allowed, retry_after = limiter.is_allowed("user123")
            assert allowed is True
            assert retry_after is None
    
    def test_rate_limiter_block(self):
        """Test rate limiter blocks excess requests."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # First 3 requests allowed
        for i in range(3):
            allowed, _ = limiter.is_allowed("user123")
            assert allowed is True
        
        # 4th request should be blocked
        allowed, retry_after = limiter.is_allowed("user123")
        assert allowed is False
        assert retry_after is not None
        assert retry_after > 0
    
    def test_rate_limiter_reset(self):
        """Test rate limiter reset."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # Use up limit
        limiter.is_allowed("user123")
        limiter.is_allowed("user123")
        
        # Should be blocked
        allowed, _ = limiter.is_allowed("user123")
        assert allowed is False
        
        # Reset
        limiter.reset("user123")
        
        # Should be allowed again
        allowed, _ = limiter.is_allowed("user123")
        assert allowed is True
    
    def test_rate_limiter_get_remaining(self):
        """Test getting remaining requests."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        assert limiter.get_remaining("user123") == 5
        
        limiter.is_allowed("user123")
        assert limiter.get_remaining("user123") == 4
        
        limiter.is_allowed("user123")
        assert limiter.get_remaining("user123") == 3


# ============================================================================
# DOCUMENT UPLOAD TESTS
# ============================================================================


class TestDocumentUpload:
    """Test document upload endpoints."""
    
    def test_upload_document_success(self, client, headers, mock_job_manager):
        """Test successful document upload."""
        mock_job_manager.submit_document.return_value = "job123"
        
        # Create test file
        files = {"file": ("test.txt", b"Hello, world!", "text/plain")}
        
        response = client.post(
            "/api/v1/documents",
            files=files,
            headers=headers,
        )
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "job_id" in data
        assert "doc_id" in data
        assert data["status"] == "pending"
    
    def test_upload_document_invalid_extension(self, client, headers):
        """Test upload with invalid file extension."""
        files = {"file": ("test.exe", b"binary", "application/octet-stream")}
        
        response = client.post(
            "/api/v1/documents",
            files=files,
            headers=headers,
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "File type not supported" in response.json()["detail"]
    
    def test_upload_batch_success(self, client, headers, mock_job_manager):
        """Test successful batch upload."""
        mock_job_manager.submit_batch.return_value = ["job1", "job2"]
        
        files = [
            ("files", ("test1.txt", b"Hello", "text/plain")),
            ("files", ("test2.txt", b"World", "text/plain")),
        ]
        
        response = client.post(
            "/api/v1/documents/batch",
            files=files,
            headers=headers,
        )
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert len(data["job_ids"]) == 2
        assert data["count"] == 2


# ============================================================================
# JOB STATUS TESTS
# ============================================================================


class TestJobStatus:
    """Test job status endpoints."""
    
    def test_get_job_status_success(self, client, headers, mock_job_manager):
        """Test getting job status."""
        from datetime import datetime
        from src.jobs import JobStatus, JobResult
        
        mock_result = JobResult(
            job_id="job123",
            status=JobStatus.SUCCESS,
            progress=1.0,
            result={"doc_id": "doc123"},
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            task_name="process_document",
            queue="default",
        )
        mock_job_manager.get_job_status.return_value = mock_result
        
        response = client.get("/api/v1/jobs/job123", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == "job123"
        assert data["status"] == "success"
    
    def test_get_job_status_not_found(self, client, headers, mock_job_manager):
        """Test getting non-existent job status."""
        mock_job_manager.get_job_status.side_effect = Exception("Job not found")
        
        response = client.get("/api/v1/jobs/invalid", headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_cancel_job_success(self, client, headers, mock_job_manager):
        """Test cancelling a job."""
        mock_job_manager.cancel_job.return_value = True
        
        response = client.delete("/api/v1/jobs/job123", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert "cancelled successfully" in response.json()["message"]
    
    def test_cancel_job_failure(self, client, headers, mock_job_manager):
        """Test cancelling a completed job."""
        mock_job_manager.cancel_job.return_value = False
        
        response = client.delete("/api/v1/jobs/job123", headers=headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# SEARCH TESTS
# ============================================================================


class TestSearch:
    """Test search endpoints."""
    
    def test_search_with_query(self, client, headers, mock_vector_store):
        """Test search with query."""
        mock_result = Mock()
        mock_result.id = "doc123"
        mock_result.score = 0.95
        mock_result.payload = {"text": "Hello, world!"}
        
        mock_vector_store.hybrid_search.return_value = [mock_result]
        
        response = client.post(
            "/api/v1/search",
            json={"query": "test", "limit": 10},
            headers=headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["doc_id"] == "doc123"
    
    def test_search_with_filters(self, client, headers, mock_vector_store):
        """Test search with metadata filters."""
        mock_vector_store.hybrid_search.return_value = []
        
        response = client.post(
            "/api/v1/search",
            json={
                "query": "test",
                "topics": ["AI"],
                "categories": ["research"],
                "limit": 10
            },
            headers=headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "AI" in data["filters"]["topics"]


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================


class TestHealth:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "uptime" in data
        assert "services" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "Document Processing API"
        assert "version" in data


# ============================================================================
# STATISTICS TESTS
# ============================================================================


class TestStatistics:
    """Test statistics endpoint."""
    
    def test_get_statistics(self, client, headers, mock_job_manager):
        """Test getting statistics."""
        mock_job_manager.get_stats.return_value = {
            "total": 100,
            "pending": 10,
            "running": 5,
            "completed": 80,
            "failed": 5,
            "success_rate": 0.94,
        }
        
        response = client.get("/api/v1/statistics", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_jobs"] == 100
        assert data["completed"] == 80
        assert data["failed"] == 5
        assert data["success_rate"] == 0.94
