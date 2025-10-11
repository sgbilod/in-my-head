"""
Load Testing Script for Document Processing API

Tests API performance under load with multiple concurrent users.

Installation:
    pip install locust

Usage:
    # Start load test with web UI
    locust -f load_test.py --host=http://localhost:8000

    # Then open: http://localhost:8089

    # Or run headless
    locust -f load_test.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 5m --headless

Scenarios tested:
- Document uploads (single and batch)
- Job status checks
- Search operations
- Health checks
- Statistics retrieval
"""

import os
import time
import random
import tempfile
from pathlib import Path
from typing import Dict, Any

from locust import HttpUser, task, between, events
from locust.exception import StopUser


# Configuration
API_KEY = os.getenv("API_KEY", "test-api-key-123")

# Sample documents for testing
SAMPLE_TEXTS = [
    "This is a test document about artificial intelligence and machine learning.",
    "Natural language processing enables computers to understand human language.",
    "Deep learning uses neural networks with multiple layers to learn representations.",
    "Computer vision allows machines to interpret and understand visual information.",
    "Reinforcement learning trains agents through reward and punishment mechanisms.",
    "Transfer learning leverages pre-trained models for new tasks.",
    "Generative AI can create new content including text, images, and code.",
    "Large language models are trained on massive amounts of text data.",
]

SEARCH_QUERIES = [
    "machine learning",
    "artificial intelligence",
    "neural networks",
    "deep learning",
    "natural language",
    "computer vision",
    "AI technology",
    "data science",
]


class DocumentProcessingUser(HttpUser):
    """Simulated user performing document processing operations."""

    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = {"X-API-Key": API_KEY}
        self.job_ids = []
        self.temp_dir = tempfile.mkdtemp()

    def on_start(self):
        """Called when a user starts."""
        # Test authentication
        response = self.client.get("/health", headers=self.headers)
        if response.status_code != 200:
            print(f"Failed to connect to API: {response.status_code}")
            raise StopUser()

    @task(10)
    def upload_document(self):
        """Upload a single document (most common operation)."""
        # Create temp file with random text
        text = random.choice(SAMPLE_TEXTS)
        filename = f"test_{int(time.time() * 1000)}.txt"
        filepath = Path(self.temp_dir) / filename
        filepath.write_text(text)

        with open(filepath, "rb") as f:
            files = {"file": (filename, f, "text/plain")}

            with self.client.post(
                "/api/v1/documents",
                files=files,
                headers=self.headers,
                catch_response=True,
                name="/api/v1/documents [UPLOAD]"
            ) as response:
                if response.status_code == 200:
                    data = response.json()
                    self.job_ids.append(data["job_id"])
                    response.success()
                elif response.status_code == 429:
                    # Rate limited - expected under load
                    response.success()
                else:
                    response.failure(f"Got status {response.status_code}")

        # Clean up
        filepath.unlink(missing_ok=True)

    @task(5)
    def check_job_status(self):
        """Check status of uploaded jobs."""
        if not self.job_ids:
            return

        job_id = random.choice(self.job_ids)

        with self.client.get(
            f"/api/v1/jobs/{job_id}",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/jobs/{id} [STATUS]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Job expired or not found - remove from list
                self.job_ids.remove(job_id)
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(3)
    def search_documents(self):
        """Search for documents."""
        query = random.choice(SEARCH_QUERIES)

        search_data = {
            "query": query,
            "limit": random.randint(5, 20)
        }

        with self.client.post(
            "/api/v1/search",
            json=search_data,
            headers=self.headers,
            catch_response=True,
            name="/api/v1/search [QUERY]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(2)
    def get_statistics(self):
        """Get processing statistics."""
        with self.client.get(
            "/api/v1/statistics",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/statistics"
        ) as response:
            if response.status_code in [200, 429]:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(1)
    def health_check(self):
        """Check service health."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["healthy", "degraded"]:
                    response.success()
                else:
                    response.failure(f"Service unhealthy: {data.get('status')}")
            else:
                response.failure(f"Got status {response.status_code}")

    @task(2)
    def upload_batch(self):
        """Upload multiple documents at once."""
        # Create 3-5 temp files
        num_files = random.randint(3, 5)
        files = []
        filepaths = []

        for i in range(num_files):
            text = random.choice(SAMPLE_TEXTS)
            filename = f"batch_{int(time.time() * 1000)}_{i}.txt"
            filepath = Path(self.temp_dir) / filename
            filepath.write_text(text)
            filepaths.append(filepath)

            files.append(
                ("files", (filename, open(filepath, "rb"), "text/plain"))
            )

        try:
            with self.client.post(
                "/api/v1/documents/batch",
                files=files,
                headers=self.headers,
                catch_response=True,
                name="/api/v1/documents/batch [BATCH]"
            ) as response:
                if response.status_code == 200:
                    data = response.json()
                    self.job_ids.extend(data.get("job_ids", []))
                    response.success()
                elif response.status_code == 429:
                    response.success()
                else:
                    response.failure(f"Got status {response.status_code}")
        finally:
            # Close file handles and clean up
            for _, (_, f, _) in files:
                f.close()
            for filepath in filepaths:
                filepath.unlink(missing_ok=True)


class SearchHeavyUser(HttpUser):
    """User that primarily performs searches (analytics workload)."""

    wait_time = between(0.5, 2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = {"X-API-Key": API_KEY}

    @task(10)
    def search_documents(self):
        """Perform document searches."""
        query = random.choice(SEARCH_QUERIES)

        search_data = {
            "query": query,
            "limit": random.randint(10, 50),
        }

        # Sometimes add filters
        if random.random() > 0.5:
            search_data["topics"] = random.sample(
                ["AI", "ML", "technology", "science"],
                k=random.randint(1, 2)
            )

        with self.client.post(
            "/api/v1/search",
            json=search_data,
            headers=self.headers,
            catch_response=True,
            name="/api/v1/search [HEAVY]"
        ) as response:
            if response.status_code in [200, 429]:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(1)
    def get_statistics(self):
        """Check statistics."""
        with self.client.get(
            "/api/v1/statistics",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/statistics [HEAVY]"
        ) as response:
            if response.status_code in [200, 429]:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print(f"\n{'='*60}")
    print("LOAD TEST STARTING")
    print(f"{'='*60}")
    print(f"Target: {environment.host}")
    print(f"API Key: {API_KEY[:20]}...")
    print(f"{'='*60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print(f"\n{'='*60}")
    print("LOAD TEST COMPLETE")
    print(f"{'='*60}")

    stats = environment.stats

    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Failure rate: {stats.total.fail_ratio:.2%}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"RPS: {stats.total.current_rps:.2f}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    # Can run directly with: python load_test.py
    import subprocess
    import sys

    print("Starting Locust load testing...")
    print("Open http://localhost:8089 in your browser")

    subprocess.run([
        sys.executable, "-m", "locust",
        "-f", __file__,
        "--host", "http://localhost:8000"
    ])
