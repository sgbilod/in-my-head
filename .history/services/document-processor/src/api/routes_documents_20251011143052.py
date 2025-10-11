"""
Document processing API router.

Provides endpoints for:
- Document upload (single and batch)
- Job status tracking
- Job cancellation
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
    status,
    Query,
)
from fastapi.responses import JSONResponse

from ..jobs import JobManager, celery_app
from ..api.auth import get_api_key
from ..api.rate_limiter import rate_limit
from ..api.schemas import (
    DocumentUploadResponse,
    BatchUploadResponse,
    JobStatusResponse,
    BatchJobStatusResponse,
    StatisticsResponse,
)

# Create router
router = APIRouter(prefix="/api/v1", tags=["documents"])

# Initialize job manager
job_manager = JobManager(celery_app)

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".html", ".htm",
    ".md", ".markdown", ".json", ".xml", ".csv",
}

# Maximum file size (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024


def validate_file(file: UploadFile) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded file.
    
    Args:
        file: Uploaded file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check filename
    if not file.filename:
        return False, "Filename is required"
    
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size (if available)
    if hasattr(file, "size") and file.size:
        if file.size > MAX_FILE_SIZE:
            return False, f"File too large. Maximum: {MAX_FILE_SIZE / (1024*1024)}MB"
    
    return True, None


async def save_uploaded_file(file: UploadFile) -> Path:
    """
    Save uploaded file to disk.
    
    Args:
        file: Uploaded file
        
    Returns:
        Path to saved file
        
    Raises:
        HTTPException: If save fails
    """
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        ext = Path(file.filename).suffix.lower()
        filename = f"{file_id}{ext}"
        file_path = UPLOAD_DIR / filename
        
        # Save file
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        return file_path
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )


@router.post(
    "/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a document for processing",
    description="Upload a single document and start background processing",
)
@rate_limit(cost=5)
async def upload_document(
    file: UploadFile = File(..., description="Document file to process"),
    extract_metadata: bool = Query(True, description="Extract AI metadata"),
    generate_embeddings: bool = Query(True, description="Generate embeddings"),
    store_in_vector_db: bool = Query(True, description="Store in vector database"),
    api_key: str = Depends(get_api_key),
):
    """
    Upload a document for processing.
    
    The document will be:
    1. Validated for type and size
    2. Saved to disk
    3. Submitted to background job queue
    4. Processed asynchronously
    
    Returns:
        Job ID and document ID for tracking
        
    Example:
        ```python
        import requests
        
        files = {"file": open("document.pdf", "rb")}
        headers = {"X-API-Key": "your-api-key"}
        
        response = requests.post(
            "http://localhost:8000/api/v1/documents",
            files=files,
            headers=headers,
        )
        
        job_id = response.json()["job_id"]
        ```
    """
    # Validate file
    is_valid, error_message = validate_file(file)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Save file
    file_path = await save_uploaded_file(file)
    
    # Submit job
    try:
        job_id = job_manager.submit_document(
            file_path=str(file_path),
            extract_metadata=extract_metadata,
            generate_embeddings=generate_embeddings,
            store_in_vector_db=store_in_vector_db,
            priority=5,
        )
        
        # Get document ID from job result (when available)
        # For now, use job_id as doc_id
        doc_id = job_id
        
        return DocumentUploadResponse(
            job_id=job_id,
            doc_id=doc_id,
            status="pending",
            message=f"Document '{file.filename}' submitted for processing"
        )
    
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit job: {str(e)}"
        )


@router.post(
    "/documents/batch",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload multiple documents for processing",
    description="Upload multiple documents and start batch processing",
)
@rate_limit(cost=10)
async def upload_documents_batch(
    files: List[UploadFile] = File(..., description="Document files to process"),
    extract_metadata: bool = Query(True, description="Extract AI metadata"),
    generate_embeddings: bool = Query(True, description="Generate embeddings"),
    store_in_vector_db: bool = Query(True, description="Store in vector database"),
    api_key: str = Depends(get_api_key),
):
    """
    Upload multiple documents for batch processing.
    
    All documents will be:
    1. Validated for type and size
    2. Saved to disk
    3. Submitted to batch job queue
    4. Processed asynchronously
    
    Returns:
        List of job IDs and document IDs for tracking
        
    Example:
        ```python
        import requests
        
        files = [
            ("files", open("doc1.pdf", "rb")),
            ("files", open("doc2.docx", "rb")),
            ("files", open("doc3.txt", "rb")),
        ]
        headers = {"X-API-Key": "your-api-key"}
        
        response = requests.post(
            "http://localhost:8000/api/v1/documents/batch",
            files=files,
            headers=headers,
        )
        
        job_ids = response.json()["job_ids"]
        ```
    """
    # Validate all files first
    for file in files:
        is_valid, error_message = validate_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}': {error_message}"
            )
    
    # Save all files
    saved_files = []
    try:
        for file in files:
            file_path = await save_uploaded_file(file)
            saved_files.append(file_path)
    except Exception as e:
        # Clean up any saved files on error
        for file_path in saved_files:
            if file_path.exists():
                file_path.unlink()
        raise
    
    # Submit batch job
    try:
        job_ids = job_manager.submit_batch(
            file_paths=[str(f) for f in saved_files],
            extract_metadata=extract_metadata,
            generate_embeddings=generate_embeddings,
            store_in_vector_db=store_in_vector_db,
            priority=4,
        )
        
        # Use job_ids as doc_ids for now
        doc_ids = job_ids
        
        return BatchUploadResponse(
            job_ids=job_ids,
            doc_ids=doc_ids,
            count=len(job_ids),
            message=f"{len(job_ids)} documents submitted for processing"
        )
    
    except Exception as e:
        # Clean up files on error
        for file_path in saved_files:
            if file_path.exists():
                file_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit batch job: {str(e)}"
        )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Get the status of a processing job",
)
async def get_job_status(
    job_id: str,
    api_key: str = Depends(get_api_key),
):
    """
    Get the status of a processing job.
    
    Returns detailed information about:
    - Current status (pending, processing, completed, failed)
    - Progress information
    - Result data (if completed)
    - Error message (if failed)
    - Duration (if completed)
    
    Example:
        ```python
        import requests
        
        headers = {"X-API-Key": "your-api-key"}
        
        response = requests.get(
            f"http://localhost:8000/api/v1/jobs/{job_id}",
            headers=headers,
        )
        
        status = response.json()["status"]
        ```
    """
    try:
        job_result = job_manager.get_job_status(job_id)
        
        # Calculate duration if completed
        duration = None
        if job_result.status.value in ["success", "failure"]:
            duration = (
                job_result.updated_at - job_result.created_at
            ).total_seconds()
        
        return JobStatusResponse(
            job_id=job_result.job_id,
            status=job_result.status.value,
            created_at=job_result.created_at,
            started_at=job_result.created_at if job_result.status.value != "pending" else None,
            completed_at=job_result.updated_at if job_result.status.value in ["success", "failure"] else None,
            progress={"percentage": job_result.progress * 100},
            result=job_result.result,
            error=job_result.error,
            duration=duration,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {str(e)}"
        )


@router.get(
    "/jobs",
    response_model=BatchJobStatusResponse,
    summary="Get batch job status",
    description="Get the status of multiple jobs",
)
async def get_batch_job_status(
    job_ids: List[str] = Query(..., description="List of job IDs"),
    api_key: str = Depends(get_api_key),
):
    """
    Get the status of multiple jobs.
    
    Returns:
        Status information for all requested jobs
        
    Example:
        ```python
        import requests
        
        headers = {"X-API-Key": "your-api-key"}
        params = {"job_ids": ["job1", "job2", "job3"]}
        
        response = requests.get(
            "http://localhost:8000/api/v1/jobs",
            params=params,
            headers=headers,
        )
        
        jobs = response.json()["jobs"]
        ```
    """
    try:
        job_results = job_manager.get_batch_status(job_ids)
        
        # Convert to response format
        jobs = []
        completed = 0
        failed = 0
        pending = 0
        
        for job_result in job_results:
            duration = None
            if job_result.status.value in ["success", "failure"]:
                duration = (
                    job_result.updated_at - job_result.created_at
                ).total_seconds()
                
                if job_result.status.value == "success":
                    completed += 1
                else:
                    failed += 1
            elif job_result.status.value == "pending":
                pending += 1
            
            jobs.append(JobStatusResponse(
                job_id=job_result.job_id,
                status=job_result.status.value,
                created_at=job_result.created_at,
                started_at=job_result.created_at if job_result.status.value != "pending" else None,
                completed_at=job_result.updated_at if job_result.status.value in ["success", "failure"] else None,
                progress={"percentage": job_result.progress * 100},
                result=job_result.result,
                error=job_result.error,
                duration=duration,
            ))
        
        return BatchJobStatusResponse(
            jobs=jobs,
            total=len(jobs),
            completed=completed,
            failed=failed,
            pending=pending,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch status: {str(e)}"
        )


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Cancel a job",
    description="Cancel a running or pending job",
)
async def cancel_job(
    job_id: str,
    api_key: str = Depends(get_api_key),
):
    """
    Cancel a running or pending job.
    
    Example:
        ```python
        import requests
        
        headers = {"X-API-Key": "your-api-key"}
        
        response = requests.delete(
            f"http://localhost:8000/api/v1/jobs/{job_id}",
            headers=headers,
        )
        ```
    """
    try:
        success = job_manager.cancel_job(job_id)
        
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": f"Job {job_id} cancelled successfully"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job cannot be cancelled (already completed or failed)"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="Get job statistics",
    description="Get overall job processing statistics",
)
async def get_statistics(
    api_key: str = Depends(get_api_key),
):
    """
    Get overall job processing statistics.
    
    Returns:
        Comprehensive statistics about job processing
        
    Example:
        ```python
        import requests
        
        headers = {"X-API-Key": "your-api-key"}
        
        response = requests.get(
            "http://localhost:8000/api/v1/statistics",
            headers=headers,
        )
        
        stats = response.json()
        print(f"Success rate: {stats['success_rate']*100}%")
        ```
    """
    try:
        stats = job_manager.get_stats()
        
        return StatisticsResponse(
            total_jobs=stats.get("total", 0),
            pending=stats.get("pending", 0),
            processing=stats.get("running", 0),
            completed=stats.get("completed", 0),
            failed=stats.get("failed", 0),
            cancelled=0,  # Not tracked yet
            avg_duration=0.0,  # Not tracked yet
            success_rate=stats.get("success_rate", 0.0),
            failure_rate=1.0 - stats.get("success_rate", 0.0),
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )
