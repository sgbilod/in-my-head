"""
Demonstration script for Document Processing API.

Shows:
- Document upload
- Job status tracking
- Search functionality
- WebSocket real-time updates

Prerequisites:
- Redis running (localhost:6379)
- Qdrant running (localhost:6333)
- Celery workers running
- API server running (localhost:8000)
"""

import asyncio
import time
import requests
import websockets
import json
from pathlib import Path
from typing import Optional


# Configuration
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
API_KEY = "test-api-key-123"  # Change to your API key


class APIClient:
    """Client for Document Processing API."""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize API client.
        
        Args:
            base_url: API base URL
            api_key: API key for authentication
        """
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    def upload_document(
        self,
        file_path: str,
        extract_metadata: bool = True,
        generate_embeddings: bool = True,
        store_in_vector_db: bool = True,
    ) -> dict:
        """
        Upload a document.
        
        Args:
            file_path: Path to document
            extract_metadata: Extract metadata
            generate_embeddings: Generate embeddings
            store_in_vector_db: Store in vector DB
            
        Returns:
            Response data
        """
        with open(file_path, "rb") as f:
            files = {"file": f}
            params = {
                "extract_metadata": extract_metadata,
                "generate_embeddings": generate_embeddings,
                "store_in_vector_db": store_in_vector_db,
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/documents",
                files=files,
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()
    
    def upload_batch(
        self,
        file_paths: list[str],
        extract_metadata: bool = True,
        generate_embeddings: bool = True,
        store_in_vector_db: bool = True,
    ) -> dict:
        """
        Upload multiple documents.
        
        Args:
            file_paths: List of document paths
            extract_metadata: Extract metadata
            generate_embeddings: Generate embeddings
            store_in_vector_db: Store in vector DB
            
        Returns:
            Response data
        """
        files = [("files", open(path, "rb")) for path in file_paths]
        params = {
            "extract_metadata": extract_metadata,
            "generate_embeddings": generate_embeddings,
            "store_in_vector_db": store_in_vector_db,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/documents/batch",
                files=files,
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()
        finally:
            # Close files
            for _, f in files:
                f.close()
    
    def get_job_status(self, job_id: str) -> dict:
        """
        Get job status.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status
        """
        response = requests.get(
            f"{self.base_url}/api/v1/jobs/{job_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()
    
    def cancel_job(self, job_id: str) -> dict:
        """
        Cancel a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Response data
        """
        response = requests.delete(
            f"{self.base_url}/api/v1/jobs/{job_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()
    
    def search(
        self,
        query: Optional[str] = None,
        topics: Optional[list[str]] = None,
        categories: Optional[list[str]] = None,
        limit: int = 10,
    ) -> dict:
        """
        Search documents.
        
        Args:
            query: Search query
            topics: Topic filters
            categories: Category filters
            limit: Maximum results
            
        Returns:
            Search results
        """
        data = {
            "query": query,
            "topics": topics,
            "categories": categories,
            "limit": limit,
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/search",
            json=data,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()
    
    def get_statistics(self) -> dict:
        """
        Get statistics.
        
        Returns:
            Statistics data
        """
        response = requests.get(
            f"{self.base_url}/api/v1/statistics",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()
    
    def check_health(self) -> dict:
        """
        Check service health.
        
        Returns:
            Health status
        """
        response = requests.get(f"{self.base_url}/health")
        return response.json()


async def monitor_job_websocket(job_id: str):
    """
    Monitor job via WebSocket.
    
    Args:
        job_id: Job to monitor
    """
    uri = f"{WS_URL}/api/v1/ws/jobs/{job_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"\n📡 Connected to WebSocket for job: {job_id}")
            
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                
                print(f"\n📨 WebSocket Message:")
                print(f"  Type: {data['type']}")
                print(f"  Data: {json.dumps(data['data'], indent=2)}")
                
                # Stop if terminal state
                if data['type'] in ['result', 'error']:
                    break
        
        print(f"\n✅ WebSocket monitoring complete")
    
    except Exception as e:
        print(f"\n❌ WebSocket error: {e}")


def demo_1_upload_document():
    """Demo 1: Upload single document."""
    print("\n" + "=" * 60)
    print("DEMO 1: Upload Single Document")
    print("=" * 60)
    
    client = APIClient(API_URL, API_KEY)
    
    # Create test file
    test_file = Path("test_document.txt")
    test_file.write_text("This is a test document about machine learning and AI.")
    
    try:
        # Upload document
        print(f"\n📤 Uploading document: {test_file}")
        result = client.upload_document(str(test_file))
        
        print(f"\n✅ Upload successful!")
        print(f"  Job ID: {result['job_id']}")
        print(f"  Doc ID: {result['doc_id']}")
        print(f"  Status: {result['status']}")
        print(f"  Message: {result['message']}")
        
        # Monitor job status
        job_id = result['job_id']
        print(f"\n⏳ Monitoring job status...")
        
        for i in range(30):  # Poll for 30 seconds
            time.sleep(1)
            status = client.get_job_status(job_id)
            
            print(f"\r  Status: {status['status']} | Progress: {status['progress']}%", end="")
            
            if status['status'] in ['success', 'failure']:
                print()  # New line
                break
        
        # Final status
        final_status = client.get_job_status(job_id)
        print(f"\n📊 Final Status:")
        print(f"  Status: {final_status['status']}")
        if final_status.get('result'):
            print(f"  Result: {json.dumps(final_status['result'], indent=2)}")
        if final_status.get('error'):
            print(f"  Error: {final_status['error']}")
    
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


def demo_2_upload_batch():
    """Demo 2: Upload batch of documents."""
    print("\n" + "=" * 60)
    print("DEMO 2: Upload Batch of Documents")
    print("=" * 60)
    
    client = APIClient(API_URL, API_KEY)
    
    # Create test files
    test_files = []
    for i in range(3):
        test_file = Path(f"test_doc_{i+1}.txt")
        test_file.write_text(f"Document {i+1}: Content about topic {i+1}")
        test_files.append(test_file)
    
    try:
        # Upload batch
        print(f"\n📤 Uploading {len(test_files)} documents...")
        result = client.upload_batch([str(f) for f in test_files])
        
        print(f"\n✅ Batch upload successful!")
        print(f"  Count: {result['count']}")
        print(f"  Job IDs: {result['job_ids']}")
        
        # Monitor all jobs
        print(f"\n⏳ Monitoring batch jobs...")
        
        for i in range(30):  # Poll for 30 seconds
            time.sleep(1)
            
            # Get status of all jobs
            statuses = []
            for job_id in result['job_ids']:
                status = client.get_job_status(job_id)
                statuses.append(status['status'])
            
            # Count statuses
            completed = statuses.count('success')
            failed = statuses.count('failure')
            pending = len(statuses) - completed - failed
            
            print(f"\r  Completed: {completed} | Failed: {failed} | Pending: {pending}", end="")
            
            if pending == 0:
                print()  # New line
                break
        
        print(f"\n✅ Batch processing complete!")
    
    finally:
        # Clean up
        for test_file in test_files:
            if test_file.exists():
                test_file.unlink()


def demo_3_search():
    """Demo 3: Search documents."""
    print("\n" + "=" * 60)
    print("DEMO 3: Search Documents")
    print("=" * 60)
    
    client = APIClient(API_URL, API_KEY)
    
    # Search with query
    print(f"\n🔍 Searching for 'machine learning'...")
    results = client.search(query="machine learning", limit=5)
    
    print(f"\n📊 Search Results:")
    print(f"  Total: {results['total']}")
    print(f"  Query: {results['query']}")
    
    for i, result in enumerate(results['results'][:3], 1):
        print(f"\n  Result {i}:")
        print(f"    Doc ID: {result['doc_id']}")
        print(f"    Score: {result['score']:.3f}")
        print(f"    Text: {result['text'][:100]}...")


def demo_4_websocket():
    """Demo 4: WebSocket monitoring."""
    print("\n" + "=" * 60)
    print("DEMO 4: WebSocket Monitoring")
    print("=" * 60)
    
    client = APIClient(API_URL, API_KEY)
    
    # Create test file
    test_file = Path("test_websocket.txt")
    test_file.write_text("WebSocket test document")
    
    try:
        # Upload document
        print(f"\n📤 Uploading document...")
        result = client.upload_document(str(test_file))
        job_id = result['job_id']
        
        print(f"\n✅ Document uploaded, monitoring via WebSocket...")
        
        # Monitor via WebSocket
        asyncio.run(monitor_job_websocket(job_id))
    
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


def demo_5_statistics():
    """Demo 5: Get statistics."""
    print("\n" + "=" * 60)
    print("DEMO 5: Get Statistics")
    print("=" * 60)
    
    client = APIClient(API_URL, API_KEY)
    
    # Get statistics
    print(f"\n📊 Fetching statistics...")
    stats = client.get_statistics()
    
    print(f"\n📈 Statistics:")
    print(f"  Total Jobs: {stats['total_jobs']}")
    print(f"  Completed: {stats['completed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  Success Rate: {stats['success_rate']*100:.1f}%")


def demo_6_health_check():
    """Demo 6: Health check."""
    print("\n" + "=" * 60)
    print("DEMO 6: Health Check")
    print("=" * 60)
    
    client = APIClient(API_URL, API_KEY)
    
    # Check health
    print(f"\n🏥 Checking service health...")
    health = client.check_health()
    
    print(f"\n💚 Health Status:")
    print(f"  Overall: {health['status']}")
    print(f"  Version: {health['version']}")
    print(f"  Uptime: {health['uptime']:.1f}s")
    
    print(f"\n  Services:")
    for service in health['services']:
        status_emoji = "✅" if service['status'] == "healthy" else "❌"
        print(f"    {status_emoji} {service['name']}: {service['status']}")
        if service.get('details'):
            print(f"       {service['details']}")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("DOCUMENT PROCESSING API - DEMONSTRATION")
    print("=" * 60)
    
    print("\n⚙️  Prerequisites:")
    print("  - Redis running (localhost:6379)")
    print("  - Qdrant running (localhost:6333)")
    print("  - Celery workers running")
    print("  - API server running (localhost:8000)")
    
    input("\nPress Enter to start demos...")
    
    try:
        # Run demos
        demo_6_health_check()  # Start with health check
        demo_1_upload_document()
        demo_2_upload_batch()
        demo_3_search()
        demo_4_websocket()
        demo_5_statistics()
        
        print("\n" + "=" * 60)
        print("✅ ALL DEMOS COMPLETE")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
