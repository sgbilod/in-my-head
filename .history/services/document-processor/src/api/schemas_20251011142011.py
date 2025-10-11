"""
Pydantic schemas for API requests and responses.

Defines:
- Request models
- Response models
- Validation rules
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


# ============================================================================
# DOCUMENT UPLOAD
# ============================================================================


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    
    job_id: str = Field(..., description="Job identifier")
    doc_id: str = Field(..., description="Document identifier")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc123",
                "doc_id": "doc456",
                "status": "pending",
                "message": "Document submitted for processing"
            }
        }


class BatchUploadResponse(BaseModel):
    """Response for batch document upload."""
    
    job_ids: List[str] = Field(..., description="List of job identifiers")
    doc_ids: List[str] = Field(..., description="List of document identifiers")
    count: int = Field(..., description="Number of documents submitted")
    message: str = Field(..., description="Success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_ids": ["job1", "job2", "job3"],
                "doc_ids": ["doc1", "doc2", "doc3"],
                "count": 3,
                "message": "3 documents submitted for processing"
            }
        }


# ============================================================================
# JOB STATUS
# ============================================================================


class JobStatusResponse(BaseModel):
    """Response for job status."""
    
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    progress: Dict[str, Any] = Field(default_factory=dict, description="Progress information")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result (if completed)")
    error: Optional[str] = Field(None, description="Error message (if failed)")
    duration: Optional[float] = Field(None, description="Duration in seconds (if completed)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc123",
                "status": "success",
                "created_at": "2025-10-11T12:00:00Z",
                "started_at": "2025-10-11T12:00:01Z",
                "completed_at": "2025-10-11T12:00:05Z",
                "progress": {},
                "result": {
                    "doc_id": "doc456",
                    "vector_id": "vec789",
                    "metadata": {}
                },
                "error": None,
                "duration": 4.2
            }
        }


class BatchJobStatusResponse(BaseModel):
    """Response for batch job status."""
    
    jobs: List[JobStatusResponse] = Field(..., description="List of job statuses")
    total: int = Field(..., description="Total number of jobs")
    completed: int = Field(..., description="Number of completed jobs")
    failed: int = Field(..., description="Number of failed jobs")
    pending: int = Field(..., description="Number of pending jobs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "jobs": [],
                "total": 10,
                "completed": 8,
                "failed": 1,
                "pending": 1
            }
        }


# ============================================================================
# SEARCH
# ============================================================================


class SearchRequest(BaseModel):
    """Request for document search."""
    
    query: Optional[str] = Field(None, description="Search query text")
    authors: Optional[List[str]] = Field(None, description="Filter by authors")
    topics: Optional[List[str]] = Field(None, description="Filter by topics")
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    entities: Optional[List[str]] = Field(None, description="Filter by entities")
    date_from: Optional[str] = Field(None, description="Filter by date (from)")
    date_to: Optional[str] = Field(None, description="Filter by date (to)")
    sentiment: Optional[str] = Field(None, description="Filter by sentiment")
    language: Optional[str] = Field(None, description="Filter by language")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")
    
    @validator("sentiment")
    def validate_sentiment(cls, v):
        """Validate sentiment value."""
        if v and v not in ["positive", "negative", "neutral", "mixed"]:
            raise ValueError("Invalid sentiment. Must be: positive, negative, neutral, or mixed")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "machine learning",
                "topics": ["AI", "technology"],
                "categories": ["research"],
                "limit": 10
            }
        }


class SearchResult(BaseModel):
    """Individual search result."""
    
    doc_id: str = Field(..., description="Document identifier")
    score: float = Field(..., description="Relevance score")
    text: str = Field(..., description="Document text (excerpt)")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc123",
                "score": 0.95,
                "text": "This is a document about machine learning...",
                "metadata": {
                    "title": "ML Research Paper",
                    "authors": ["Dr. Smith"],
                    "topics": ["AI", "ML"]
                }
            }
        }


class SearchResponse(BaseModel):
    """Response for document search."""
    
    results: List[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: Optional[str] = Field(None, description="Original query")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [],
                "total": 42,
                "query": "machine learning",
                "filters": {
                    "topics": ["AI"],
                    "limit": 10
                }
            }
        }


# ============================================================================
# STATISTICS
# ============================================================================


class StatisticsResponse(BaseModel):
    """Response for job statistics."""
    
    total_jobs: int = Field(..., description="Total number of jobs")
    pending: int = Field(..., description="Pending jobs")
    processing: int = Field(..., description="Processing jobs")
    completed: int = Field(..., description="Completed jobs")
    failed: int = Field(..., description="Failed jobs")
    cancelled: int = Field(..., description="Cancelled jobs")
    avg_duration: float = Field(..., description="Average duration in seconds")
    success_rate: float = Field(..., description="Success rate (0-1)")
    failure_rate: float = Field(..., description="Failure rate (0-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_jobs": 1000,
                "pending": 10,
                "processing": 5,
                "completed": 950,
                "failed": 30,
                "cancelled": 5,
                "avg_duration": 4.2,
                "success_rate": 0.95,
                "failure_rate": 0.03
            }
        }


# ============================================================================
# HEALTH
# ============================================================================


class ServiceHealth(BaseModel):
    """Health status of a service."""
    
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Status: healthy, degraded, unhealthy")
    details: Optional[str] = Field(None, description="Additional details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "redis",
                "status": "healthy",
                "details": "Connected"
            }
        }


class HealthResponse(BaseModel):
    """Response for health check."""
    
    status: str = Field(..., description="Overall status")
    version: str = Field(..., description="Service version")
    uptime: float = Field(..., description="Uptime in seconds")
    services: List[ServiceHealth] = Field(..., description="Service health statuses")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600.0,
                "services": [
                    {"name": "redis", "status": "healthy"},
                    {"name": "qdrant", "status": "healthy"},
                    {"name": "celery", "status": "healthy"}
                ]
            }
        }


# ============================================================================
# WEBSOCKET
# ============================================================================


class WebSocketMessage(BaseModel):
    """WebSocket message for job updates."""
    
    type: str = Field(..., description="Message type: status, progress, result, error")
    job_id: str = Field(..., description="Job identifier")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "progress",
                "job_id": "abc123",
                "data": {
                    "status": "processing",
                    "current": 3,
                    "total": 5,
                    "message": "Generating embeddings..."
                },
                "timestamp": "2025-10-11T12:00:03Z"
            }
        }
