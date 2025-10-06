"""
AI Engine Service
Handles LLM inference, embeddings, and multi-model AI operations
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import os
from datetime import datetime

# Import routes
from src.routes import chunking

app = FastAPI(
    title="In My Head - AI Engine",
    description="LLM inference, embeddings, and multi-model AI support",
    version="0.1.0"
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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "In My Head - AI Engine",
        "version": "0.1.0",
        "status": "running",
        "supported_models": ["claude", "gpt-4", "gemini", "local-llm"]
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
    """Readiness check endpoint"""
    return {
        "status": "ready",
        "service": "ai-engine",
        "dependencies": {
            "qdrant": "connected",
            "redis": "connected"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
