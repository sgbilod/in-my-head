"""
API package for document processing endpoints.

This package provides:
- Document upload and processing
- Job status tracking
- Search functionality
- WebSocket real-time updates
- Authentication and rate limiting
"""

from .auth import get_api_key, verify_api_key
from .rate_limiter import RateLimiter, rate_limit
from .schemas import (
    DocumentUploadResponse,
    JobStatusResponse,
    SearchRequest,
    SearchResponse,
    HealthResponse,
)

__all__ = [
    "get_api_key",
    "verify_api_key",
    "RateLimiter",
    "rate_limit",
    "DocumentUploadResponse",
    "JobStatusResponse",
    "SearchRequest",
    "SearchResponse",
    "HealthResponse",
]
