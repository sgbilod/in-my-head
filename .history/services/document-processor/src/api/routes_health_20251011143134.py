"""
Health check router for service monitoring.

Provides:
- Overall health status
- Service dependencies status
- Version information
"""

import time
import redis
from typing import List
from fastapi import APIRouter, status as http_status
from fastapi.responses import JSONResponse

from ..api.schemas import HealthResponse, ServiceHealth

# Create router
router = APIRouter(tags=["health"])

# Service start time
START_TIME = time.time()

# Version
VERSION = "1.0.0"


def check_redis_health() -> ServiceHealth:
    """
    Check Redis health.
    
    Returns:
        Health status
    """
    try:
        client = redis.Redis(host="localhost", port=6379, db=0)
        client.ping()
        return ServiceHealth(
            name="redis",
            status="healthy",
            details="Connected"
        )
    except Exception as e:
        return ServiceHealth(
            name="redis",
            status="unhealthy",
            details=f"Connection failed: {str(e)}"
        )


def check_qdrant_health() -> ServiceHealth:
    """
    Check Qdrant health.
    
    Returns:
        Health status
    """
    try:
        from qdrant_client import QdrantClient
        
        client = QdrantClient(host="localhost", port=6333)
        # Try to get collections (will fail if not connected)
        client.get_collections()
        
        return ServiceHealth(
            name="qdrant",
            status="healthy",
            details="Connected"
        )
    except Exception as e:
        return ServiceHealth(
            name="qdrant",
            status="unhealthy",
            details=f"Connection failed: {str(e)}"
        )


def check_celery_health() -> ServiceHealth:
    """
    Check Celery health.
    
    Returns:
        Health status
    """
    try:
        from ..jobs import celery_app
        
        # Check if workers are active
        stats = celery_app.control.inspect().stats()
        
        if stats:
            worker_count = len(stats)
            return ServiceHealth(
                name="celery",
                status="healthy",
                details=f"{worker_count} workers active"
            )
        else:
            return ServiceHealth(
                name="celery",
                status="degraded",
                details="No workers active"
            )
    except Exception as e:
        return ServiceHealth(
            name="celery",
            status="unhealthy",
            details=f"Check failed: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check service health and dependencies",
)
async def health_check():
    """
    Check service health.
    
    Returns:
        Overall health status and service statuses
        
    Example:
        ```python
        import requests
        
        response = requests.get("http://localhost:8000/health")
        
        if response.json()["status"] == "healthy":
            print("Service is healthy")
        ```
    """
    # Calculate uptime
    uptime = time.time() - START_TIME
    
    # Check services
    services: List[ServiceHealth] = [
        check_redis_health(),
        check_qdrant_health(),
        check_celery_health(),
    ]
    
    # Determine overall status
    unhealthy_count = sum(1 for s in services if s.status == "unhealthy")
    degraded_count = sum(1 for s in services if s.status == "degraded")
    
    if unhealthy_count > 0:
        overall_status = "unhealthy"
        status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE
    elif degraded_count > 0:
        overall_status = "degraded"
        status_code = http_status.HTTP_200_OK
    else:
        overall_status = "healthy"
        status_code = http_status.HTTP_200_OK
    
    response = HealthResponse(
        status=overall_status,
        version=VERSION,
        uptime=uptime,
        services=services,
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump()
    )


@router.get(
    "/",
    summary="Root endpoint",
    description="Service information",
)
async def root():
    """
    Root endpoint with service information.
    
    Returns:
        Service information
    """
    return {
        "service": "Document Processing API",
        "version": VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }
