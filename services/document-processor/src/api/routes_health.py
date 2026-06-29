"""
Health check router for service monitoring.

Provides:
- Overall health status
- Service dependencies status
- Version information
"""

import os
import time
import httpx
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

AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://127.0.0.1:8001")


def check_parser_health() -> ServiceHealth:
    """Verify the parser layer imports and reports its supported formats."""
    try:
        from ..parsers import ParserFactory

        formats = ParserFactory.get_supported_formats()
        return ServiceHealth(
            name="parsers",
            status="healthy",
            details=f"{len(formats)} formats: {', '.join(formats)}",
        )
    except Exception as e:
        return ServiceHealth(
            name="parsers",
            status="unhealthy",
            details=f"Parser layer failed to load: {e}",
        )


def check_ai_engine_health() -> ServiceHealth:
    """Verify the ai-engine (the ingestion target) is reachable."""
    try:
        resp = httpx.get(f"{AI_ENGINE_URL}/documents/health", timeout=3.0)
        if resp.status_code == 200:
            return ServiceHealth(
                name="ai-engine",
                status="healthy",
                details=f"Reachable at {AI_ENGINE_URL}",
            )
        return ServiceHealth(
            name="ai-engine",
            status="degraded",
            details=f"Unexpected status {resp.status_code}",
        )
    except Exception as e:
        return ServiceHealth(
            name="ai-engine",
            status="degraded",
            details=f"Unreachable at {AI_ENGINE_URL}: {e}",
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
        check_parser_health(),
        check_ai_engine_health(),
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
