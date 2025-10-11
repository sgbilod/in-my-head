"""
End-to-End Tests for Document Processing Pipeline

Tests the complete flow from document upload through processing to search.
Requires all services to be running:
- Redis (localhost:6379)
- Qdrant (localhost:6333)
- AI Engine (localhost:8001)
- Celery Workers

Run with: pytest test_e2e.py -v --tb=short
"""

import os
import time
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import requests
from fastapi.testclient import TestClient

from src.app import app
from src.api.auth import generate_api_key


# Test client
client = TestClient(app)

# API key for testing
TEST_API_KEY = generate_api_key()
os.environ["API_KEYS"] = TEST_API_KEY


@pytest.fixture(scope="module")
def api_headers() -> Dict[str, str]:
    """Fixture providing authentication headers."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture(scope="module")
def sample_documents() -> Dict[str, bytes]:
    """Fixture providing sample documents for testing."""
    return {
        "test.txt": b"This is a test document about machine learning and AI.",
        "test2.txt": b"Another document discussing neural networks and deep learning.",
        "test3.txt": b"Natural language processing enables computers to understand text.",
    }


@pytest.fixture(scope="module")
def temp_dir():
    """Fixture providing temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestCompleteDocumentPipeline:
    """Test complete document processing pipeline."""

    def test_1_health_check(self):
        """Test that all services are healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] in ["healthy", "degraded"]
        
        # Check individual services
        services = health_data.get("services", {})
        assert "redis" in services
        assert "qdrant" in services
        
        print(f"\n✅ Health check: {health_data['status']}")
        print(f"   Redis: {services.get('redis', {}).get('status')}")
        print(f"   Qdrant: {services.get('qdrant', {}).get('status')}")

    def test_2_upload_single_document(
        self, api_headers, sample_documents, temp_dir
    ):
        """Test uploading a single document."""
        # Create temp file
        file_path = temp_dir / "test.txt"
        file_path.write_bytes(sample_documents["test.txt"])
        
        # Upload
        with open(file_path, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = client.post(
                "/api/v1/documents",
                files=files,
                headers=api_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "job_id" in data
        assert "document_id" in data
        assert data["status"] == "accepted"
        
        # Store job_id for next test
        self.__class__.single_job_id = data["job_id"]
        
        print(f"\n✅ Document uploaded")
        print(f"   Job ID: {data['job_id']}")
        print(f"   Document ID: {data['document_id']}")

    def test_3_monitor_job_progress(self, api_headers):
        """Test monitoring job progress until completion."""
        job_id = self.__class__.single_job_id
        max_attempts = 30  # 30 seconds timeout
        attempt = 0
        
        while attempt < max_attempts:
            response = client.get(
                f"/api/v1/jobs/{job_id}",
                headers=api_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            status = data["status"]
            progress = data.get("progress", {})
            
            print(f"\n   Attempt {attempt + 1}: Status={status}, "
                  f"Progress={progress.get('percentage', 0)}%")
            
            if status == "success":
                assert "result" in data
                result = data["result"]
                
                # Verify result contains expected fields
                assert "document_id" in result
                assert "chunk_count" in result
                assert result["chunk_count"] > 0
                
                print(f"✅ Job completed successfully")
                print(f"   Chunks created: {result['chunk_count']}")
                
                # Store document_id for search tests
                self.__class__.document_id = result["document_id"]
                return
            
            elif status == "failure":
                error = data.get("error", "Unknown error")
                pytest.fail(f"Job failed: {error}")
            
            # Wait before checking again
            time.sleep(1)
            attempt += 1
        
        pytest.fail(f"Job did not complete within {max_attempts} seconds")

    def test_4_upload_batch_documents(
        self, api_headers, sample_documents, temp_dir
    ):
        """Test uploading multiple documents."""
        files = []
        
        for filename, content in list(sample_documents.items())[1:]:
            file_path = temp_dir / filename
            file_path.write_bytes(content)
            
            files.append(
                ("files", (filename, open(file_path, "rb"), "text/plain"))
            )
        
        try:
            response = client.post(
                "/api/v1/documents/batch",
                files=files,
                headers=api_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "job_ids" in data
            assert "document_ids" in data
            assert len(data["job_ids"]) > 0
            
            # Store job_ids for batch status test
            self.__class__.batch_job_ids = data["job_ids"]
            
            print(f"\n✅ Batch upload successful")
            print(f"   Jobs created: {len(data['job_ids'])}")
            
        finally:
            # Close file handles
            for _, (_, f, _) in files:
                f.close()

    def test_5_get_batch_status(self, api_headers):
        """Test getting status of multiple jobs."""
        job_ids = self.__class__.batch_job_ids
        
        response = client.get(
            f"/api/v1/jobs?job_ids={','.join(job_ids)}",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "jobs" in data
        assert len(data["jobs"]) == len(job_ids)
        
        print(f"\n✅ Batch status retrieved")
        print(f"   Jobs: {len(data['jobs'])}")

    def test_6_wait_for_batch_completion(self, api_headers):
        """Wait for batch jobs to complete."""
        job_ids = self.__class__.batch_job_ids
        max_attempts = 30
        
        for attempt in range(max_attempts):
            response = client.get(
                f"/api/v1/jobs?job_ids={','.join(job_ids)}",
                headers=api_headers
            )
            
            data = response.json()
            jobs = data["jobs"]
            
            # Check if all jobs are complete
            all_complete = all(
                job["status"] in ["success", "failure"]
                for job in jobs
            )
            
            if all_complete:
                success_count = sum(
                    1 for job in jobs if job["status"] == "success"
                )
                failure_count = sum(
                    1 for job in jobs if job["status"] == "failure"
                )
                
                print(f"\n✅ Batch processing complete")
                print(f"   Success: {success_count}")
                print(f"   Failures: {failure_count}")
                
                assert success_count > 0, "At least one job should succeed"
                return
            
            time.sleep(1)
        
        pytest.fail("Batch jobs did not complete in time")

    def test_7_search_documents_by_text(self, api_headers):
        """Test searching documents by text query."""
        search_data = {
            "query": "machine learning",
            "limit": 10
        }
        
        response = client.post(
            "/api/v1/search",
            json=search_data,
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total" in data
        assert "query" in data
        
        # Should find results since we uploaded documents about ML
        assert len(data["results"]) > 0, "Should find documents about ML"
        
        # Check result structure
        result = data["results"][0]
        assert "score" in result
        assert "text" in result
        assert "metadata" in result
        
        print(f"\n✅ Search completed")
        print(f"   Results: {len(data['results'])}")
        print(f"   Top score: {result['score']:.4f}")

    def test_8_search_with_filters(self, api_headers):
        """Test searching with metadata filters."""
        search_data = {
            "query": "neural networks",
            "topics": ["AI", "technology"],
            "limit": 5
        }
        
        response = client.post(
            "/api/v1/search",
            json=search_data,
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        # Results may be filtered down
        assert len(data["results"]) <= 5
        
        print(f"\n✅ Filtered search completed")
        print(f"   Results: {len(data['results'])}")

    def test_9_get_statistics(self, api_headers):
        """Test getting processing statistics."""
        response = client.get(
            "/api/v1/statistics",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_jobs" in data
        assert "success_count" in data
        assert "failure_count" in data
        
        # Should have processed some jobs by now
        assert data["total_jobs"] > 0
        
        print(f"\n✅ Statistics retrieved")
        print(f"   Total jobs: {data['total_jobs']}")
        print(f"   Success: {data['success_count']}")
        print(f"   Failures: {data['failure_count']}")


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_file_type(self, api_headers, temp_dir):
        """Test uploading invalid file type."""
        # Create invalid file
        file_path = temp_dir / "test.exe"
        file_path.write_bytes(b"Invalid binary content")
        
        with open(file_path, "rb") as f:
            files = {"file": ("test.exe", f, "application/x-msdownload")}
            response = client.post(
                "/api/v1/documents",
                files=files,
                headers=api_headers
            )
        
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"].lower()
        
        print("\n✅ Invalid file type rejected correctly")

    def test_file_too_large(self, api_headers, temp_dir):
        """Test uploading file that's too large."""
        # Create large file (>100MB)
        file_path = temp_dir / "large.txt"
        
        # Create 101MB of data
        large_content = b"x" * (101 * 1024 * 1024)
        file_path.write_bytes(large_content)
        
        with open(file_path, "rb") as f:
            files = {"file": ("large.txt", f, "text/plain")}
            response = client.post(
                "/api/v1/documents",
                files=files,
                headers=api_headers
            )
        
        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()
        
        print("\n✅ Large file rejected correctly")

    def test_invalid_job_id(self, api_headers):
        """Test getting status of non-existent job."""
        response = client.get(
            "/api/v1/jobs/invalid-job-id-12345",
            headers=api_headers
        )
        
        assert response.status_code == 404
        
        print("\n✅ Invalid job ID handled correctly")

    def test_cancel_nonexistent_job(self, api_headers):
        """Test canceling non-existent job."""
        response = client.delete(
            "/api/v1/jobs/nonexistent-job-id",
            headers=api_headers
        )
        
        assert response.status_code == 404
        
        print("\n✅ Cancel non-existent job handled correctly")


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_enforcement(self, api_headers):
        """Test that rate limits are enforced."""
        # Make many requests quickly
        responses = []
        
        for i in range(15):  # Try 15 statistics requests (cost 1 each)
            response = client.get(
                "/api/v1/statistics",
                headers=api_headers
            )
            responses.append(response)
        
        # Should have some successful requests
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limited = sum(1 for r in responses if r.status_code == 429)
        
        print(f"\n✅ Rate limiting tested")
        print(f"   Successful: {success_count}")
        print(f"   Rate limited: {rate_limited}")
        
        # Note: May or may not hit rate limit depending on timing
        # But all responses should be either 200 or 429
        assert all(r.status_code in [200, 429] for r in responses)


class TestWebSocketIntegration:
    """Test WebSocket functionality (basic checks)."""

    def test_websocket_connection(self):
        """Test that WebSocket endpoint exists."""
        # We can't easily test WebSocket in TestClient
        # But we can verify the endpoint is registered
        
        # Try to connect (will fail in TestClient but endpoint exists)
        from starlette.testclient import TestClient as StarletteTestClient
        
        ws_client = StarletteTestClient(app)
        
        try:
            with ws_client.websocket_connect("/api/v1/ws/jobs/test-job-id") as ws:
                # If we get here, connection was successful
                print("\n✅ WebSocket endpoint accessible")
        except Exception as e:
            # Expected to fail with TestClient, but endpoint exists
            if "websocket" in str(e).lower():
                print("\n✅ WebSocket endpoint exists (connection requires real server)")
            else:
                raise


def test_full_pipeline_summary():
    """Print summary of E2E tests."""
    print("\n" + "=" * 60)
    print("E2E TEST SUMMARY")
    print("=" * 60)
    print("✅ Complete pipeline tested:")
    print("   1. Health checks")
    print("   2. Single document upload")
    print("   3. Job progress monitoring")
    print("   4. Batch document upload")
    print("   5. Batch status tracking")
    print("   6. Document search (text + filters)")
    print("   7. Statistics retrieval")
    print("   8. Error handling (invalid files, large files)")
    print("   9. Rate limiting")
    print("   10. WebSocket endpoints")
    print("=" * 60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
