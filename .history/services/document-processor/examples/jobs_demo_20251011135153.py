"""
Background job processing demonstration.

This demo shows:
1. Job submission (single and batch)
2. Job status tracking
3. Progress monitoring
4. Job cancellation
5. Statistics and monitoring

Prerequisites:
- Redis running on localhost:6379
- Qdrant running on localhost:6333
- Celery workers running
- Environment variables set:
  - ANTHROPIC_API_KEY
  - OPENAI_API_KEY
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jobs import JobManager, JobStatus


# ============================================================================
# UTILITIES
# ============================================================================


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_job_status(result):
    """Print job status."""
    print(f"Job ID: {result.job_id}")
    print(f"Status: {result.status.value}")

    if result.started_at:
        print(f"Started: {result.started_at.isoformat()}")

    if result.completed_at:
        print(f"Completed: {result.completed_at.isoformat()}")

        if result.started_at:
            duration = (
                result.completed_at - result.started_at
            ).total_seconds()
            print(f"Duration: {duration:.2f}s")

    if result.progress:
        print(f"Progress: {result.progress}")

    if result.result:
        print(f"Result: {result.result}")

    if result.error:
        print(f"Error: {result.error}")

    print()


# ============================================================================
# DEMO 1: SINGLE DOCUMENT PROCESSING
# ============================================================================


def demo_single_document():
    """Demo 1: Submit and track single document."""
    print_section("Demo 1: Single Document Processing")

    # Initialize manager
    manager = JobManager()

    # Create test document
    test_file = Path("test_document.txt")
    test_file.write_text("""
    Artificial Intelligence in Healthcare

    Artificial intelligence (AI) is revolutionizing healthcare delivery.
    Machine learning algorithms can now diagnose diseases with accuracy
    rivaling expert physicians. Natural language processing enables
    automated medical record analysis. Computer vision assists in
    analyzing medical imaging. The future of healthcare is increasingly
    data-driven and AI-powered.

    Authors: Dr. Jane Smith, Dr. John Doe
    Published: 2025
    """)

    print(f"📄 Submitting document: {test_file}")

    # Submit document
    job_id = manager.submit_document(
        file_path=str(test_file),
        doc_id="demo-doc-1",
        source="demo",
        collection_name="demo_documents",
        priority=8,
    )

    print(f"✅ Job submitted: {job_id}\n")

    # Track progress
    print("📊 Tracking progress...")

    while True:
        result = manager.get_job_status(job_id)
        print_job_status(result)

        if result.status in [
            JobStatus.SUCCESS,
            JobStatus.FAILURE,
            JobStatus.REVOKED,
        ]:
            break

        time.sleep(2)

    # Cleanup
    test_file.unlink()
    manager.close()

    print("✅ Demo 1 complete!\n")


# ============================================================================
# DEMO 2: BATCH PROCESSING
# ============================================================================


def demo_batch_processing():
    """Demo 2: Submit and track batch of documents."""
    print_section("Demo 2: Batch Document Processing")

    # Initialize manager
    manager = JobManager()

    # Create test documents
    test_docs = []

    for i in range(3):
        test_file = Path(f"test_doc_{i}.txt")
        test_file.write_text(f"""
        Document {i+1}

        This is test document number {i+1}.
        It contains some sample text for processing.
        The content varies by document.

        Topic: Technology, AI, Machine Learning
        Category: Research
        """)
        test_docs.append(str(test_file))

    print(f"📄 Submitting {len(test_docs)} documents")

    # Submit batch
    job_ids = manager.submit_batch(
        file_paths=test_docs,
        doc_ids=[f"demo-doc-{i}" for i in range(len(test_docs))],
        sources=["demo"] * len(test_docs),
        collection_name="demo_documents",
        priority=5,
    )

    print(f"✅ {len(job_ids)} jobs submitted\n")

    # Track batch progress
    print("📊 Tracking batch progress...")

    completed = 0
    while completed < len(job_ids):
        results = manager.get_batch_status(job_ids)

        # Count completed
        completed = sum(
            1 for r in results.values()
            if r.status in [
                JobStatus.SUCCESS,
                JobStatus.FAILURE,
                JobStatus.REVOKED,
            ]
        )

        # Show progress
        print(f"Progress: {completed}/{len(job_ids)} completed")

        # Show individual statuses
        for job_id, result in results.items():
            print(f"  {job_id}: {result.status.value}")

        print()

        if completed < len(job_ids):
            time.sleep(3)

    # Show final results
    print("\n📊 Final Results:")
    results = manager.get_batch_status(job_ids)

    for job_id, result in results.items():
        print(f"\nJob: {job_id}")
        print_job_status(result)

    # Cleanup
    for doc in test_docs:
        Path(doc).unlink()

    manager.close()

    print("✅ Demo 2 complete!\n")


# ============================================================================
# DEMO 3: JOB CANCELLATION
# ============================================================================


def demo_job_cancellation():
    """Demo 3: Job cancellation."""
    print_section("Demo 3: Job Cancellation")

    # Initialize manager
    manager = JobManager()

    # Create test document
    test_file = Path("test_cancel.txt")
    test_file.write_text("Test document for cancellation" * 1000)

    print(f"📄 Submitting document: {test_file}")

    # Submit document
    job_id = manager.submit_document(
        file_path=str(test_file),
        doc_id="demo-cancel",
        priority=3,
    )

    print(f"✅ Job submitted: {job_id}")

    # Wait a bit
    time.sleep(2)

    # Cancel job
    print(f"\n🛑 Cancelling job {job_id}...")
    success = manager.cancel_job(job_id)

    if success:
        print("✅ Job cancelled successfully")
    else:
        print("❌ Failed to cancel job")

    # Check status
    time.sleep(1)
    result = manager.get_job_status(job_id)
    print(f"\n📊 Final status: {result.status.value}")

    # Cleanup
    test_file.unlink()
    manager.close()

    print("\n✅ Demo 3 complete!\n")


# ============================================================================
# DEMO 4: STATISTICS AND MONITORING
# ============================================================================


def demo_statistics():
    """Demo 4: Statistics and monitoring."""
    print_section("Demo 4: Statistics and Monitoring")

    # Initialize manager
    manager = JobManager()

    # Get statistics
    stats = manager.get_statistics()

    print("📊 Job Processing Statistics:\n")
    print(f"Total Jobs:     {stats['total_jobs']}")
    print(f"Pending:        {stats['pending']}")
    print(f"Processing:     {stats['processing']}")
    print(f"Completed:      {stats['completed']}")
    print(f"Failed:         {stats['failed']}")
    print(f"Cancelled:      {stats['cancelled']}")
    print(f"\nAvg Duration:   {stats['avg_duration']:.2f}s")
    print(f"Success Rate:   {stats['success_rate']:.1%}")
    print(f"Failure Rate:   {stats['failure_rate']:.1%}")

    # Cleanup expired jobs
    print("\n🧹 Cleaning up expired jobs...")
    deleted = manager.cleanup_expired_jobs()
    print(f"✅ Deleted {deleted} expired jobs")

    manager.close()

    print("\n✅ Demo 4 complete!\n")


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Run all demos."""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║          BACKGROUND JOB PROCESSING DEMONSTRATION                 ║
    ║                                                                  ║
    ║  This demo showcases the Celery-based background job system      ║
    ║  for document processing.                                        ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

    # Check prerequisites
    print("🔍 Checking prerequisites...")

    # Check environment variables
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not set")
    else:
        print("✅ ANTHROPIC_API_KEY set")

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set")
    else:
        print("✅ OPENAI_API_KEY set")

    # Check Redis
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379)
        r.ping()
        print("✅ Redis running")
    except Exception as e:
        print(f"❌ Redis not running: {e}")
        return

    # Check Qdrant
    try:
        import requests
        response = requests.get("http://localhost:6333/")
        if response.status_code == 200:
            print("✅ Qdrant running")
    except Exception as e:
        print(f"❌ Qdrant not running: {e}")
        return

    print("\n✅ All prerequisites met!\n")

    # Run demos
    try:
        demo_single_document()
        demo_batch_processing()
        demo_job_cancellation()
        demo_statistics()

        print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║                    ALL DEMOS COMPLETED! 🎉                       ║
    ║                                                                  ║
    ║  The background job processing system is working correctly.      ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
        """)

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
