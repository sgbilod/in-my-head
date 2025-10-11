"""
FastAPI application for document processing API.

Provides:
- Document upload endpoints
- Job status tracking
- Search functionality
- WebSocket real-time updates
- Health monitoring
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .api import routes_documents, routes_search, routes_websocket, routes_health


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles:
    - Startup initialization
    - Shutdown cleanup
    """
    # Startup
    print("🚀 Starting Document Processing API...")

    # Create upload directory
    os.makedirs("uploads", exist_ok=True)

    # Initialize services
    # (Already initialized in route modules)

    print("✅ Document Processing API started successfully")

    yield

    # Shutdown
    print("🛑 Shutting down Document Processing API...")
    print("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Document Processing API",
    description="""
    API for document processing with AI-powered metadata extraction and search.

    ## Features

    - **Document Upload**: Upload single or multiple documents
    - **Background Processing**: Async processing with job tracking
    - **AI Metadata**: Automatic metadata extraction using Claude
    - **Vector Search**: Semantic search with embeddings
    - **Real-time Updates**: WebSocket for job progress
    - **Rate Limiting**: Protect against abuse
    - **Authentication**: API key-based security

    ## Authentication

    All endpoints require API key authentication via `X-API-Key` header.

    Example:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/documents" \\
      -H "X-API-Key: your-api-key" \\
      -F "file=@document.pdf"
    ```

    ## Rate Limits

    - Upload single: 5 requests per minute
    - Upload batch: 10 requests per minute
    - Search: 2 requests per minute
    - Other endpoints: 1 request per minute

    ## WebSocket

    Connect to `/api/v1/ws/jobs/{job_id}` for real-time updates.

    Example (JavaScript):
    ```javascript
    const ws = new WebSocket("ws://localhost:8000/api/v1/ws/jobs/abc123");
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data);
    };
    ```
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Gzip middleware for response compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(routes_health.router)
app.include_router(routes_documents.router)
app.include_router(routes_search.router)
app.include_router(routes_websocket.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler.

    Returns:
        Error response
    """
    import traceback

    # Log error
    print(f"❌ Error: {exc}")
    print(traceback.format_exc())

    # Return error response
    return {
        "error": "Internal server error",
        "detail": str(exc),
    }


if __name__ == "__main__":
    import uvicorn

    # Run server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
        log_level="info",
    )
