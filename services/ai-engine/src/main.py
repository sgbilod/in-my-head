"""
AI Engine Service
Handles LLM inference, embeddings, and multi-model AI operations
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import logging
import os
from datetime import datetime

# Import routes
from src.routes import chunking, rag, documents
from src.routes import conversations as conversations_routes
from src.db_init import run_migrations
from src.services.conversation_service import get_conversation_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bootstrap the database schema and conversation pool on startup."""
    # Single source of truth: apply idempotent SQL migrations.
    try:
        await run_migrations()
    except Exception as e:  # never block startup on DB issues
        logger.warning("Migrations skipped/failed: %s", e)

    # Warm the conversation service connection pool (degrades gracefully).
    try:
        await get_conversation_service().initialize()
    except Exception as e:
        logger.warning("Conversation pool not initialized: %s", e)

    yield

    try:
        await get_conversation_service().close()
    except Exception:
        pass


app = FastAPI(
    title="In My Head - AI Engine",
    description="LLM inference, embeddings, and multi-model AI support",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(chunking.router)
app.include_router(rag.router)
app.include_router(documents.router)
# Postgres-backed conversations (persistent, real RAG+LLM). Replaces the old
# in-memory src/api/conversations.py placeholder.
app.include_router(conversations_routes.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "In My Head - AI Engine",
        "version": "0.1.0",
        "status": "running",
        "supported_models": ["local-llm", "claude", "gemini"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-engine",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check — actually probes dependencies."""
    deps = {}

    # Qdrant
    try:
        from src.services.qdrant_service import get_qdrant_service
        get_qdrant_service().client.get_collections()
        deps["qdrant"] = "connected"
    except Exception as e:
        deps["qdrant"] = f"unavailable: {type(e).__name__}"

    # PostgreSQL (conversation pool)
    try:
        svc = get_conversation_service()
        if svc.pool is not None:
            async with svc.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            deps["postgres"] = "connected"
        else:
            deps["postgres"] = "not initialized"
    except Exception as e:
        deps["postgres"] = f"unavailable: {type(e).__name__}"

    ready = all(v == "connected" for v in deps.values())
    return {
        "status": "ready" if ready else "degraded",
        "service": "ai-engine",
        "dependencies": deps,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
