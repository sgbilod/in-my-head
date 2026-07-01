"""
Document ingestion API routes (local-first).

Full pipeline, no external APIs:
    text/file -> chunk -> embed (local sentence-transformers) -> store in Qdrant

Endpoints:
- POST /documents/ingest  - ingest raw text
- POST /documents/upload  - ingest an uploaded text/markdown file
- GET  /documents         - list ingested documents
- DELETE /documents/{id}  - remove a document's chunks

Embeddings use the same model and collection (`chunk_embeddings`, 384-dim)
that the RAG retrieval path reads from, so ingested documents are immediately
searchable via /rag/query and /rag/retrieve.
"""

import uuid
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Form,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, ConfigDict, Field

from src.services.chunker_service import ChunkerService, ChunkingStrategy
from src.services.rag_service import get_rag_service
from src.services.qdrant_service import get_qdrant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

CHUNK_COLLECTION = "chunk_embeddings"

# Text formats we can read directly without a heavy parser
TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".text", ".csv", ".json"}


# ==================== Schemas ====================

class IngestRequest(BaseModel):
    """Request to ingest raw document text."""
    content: str = Field(..., description="Document text content", min_length=1)
    title: str = Field(default="Untitled", description="Document title")
    document_id: Optional[str] = Field(
        default=None, description="Optional document ID (generated if omitted)"
    )
    strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.SENTENCE, description="Chunking strategy"
    )
    chunk_size: int = Field(default=500, ge=50, le=5000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "content": "Photosynthesis converts light into chemical energy...",
            "title": "Photosynthesis Basics",
            "strategy": "sentence",
            "chunk_size": 500,
            "chunk_overlap": 50,
        }
    })


class IngestResponse(BaseModel):
    """Response from ingestion."""
    document_id: str
    title: str
    chunks_created: int
    collection: str
    embedding_dimension: int


class DocumentSummary(BaseModel):
    """A summary of an ingested document."""
    document_id: str
    title: str
    chunk_count: int


# ==================== Core ingestion ====================

async def _ingest_text(
    content: str,
    title: str,
    document_id: Optional[str],
    strategy: ChunkingStrategy,
    chunk_size: int,
    chunk_overlap: int,
) -> IngestResponse:
    """Chunk, embed locally, and store a document's text in Qdrant."""
    rag = get_rag_service()
    if rag.embedding_model is None:
        raise HTTPException(
            status_code=503,
            detail="Embedding model not available (install sentence-transformers)",
        )

    qdrant = get_qdrant_service()
    await qdrant.initialize()  # idempotent; ensures chunk_embeddings exists

    document_id = document_id or str(uuid.uuid4())

    chunker = ChunkerService(
        default_chunk_size=chunk_size, default_chunk_overlap=chunk_overlap
    )
    chunks = chunker.chunk_document(
        document_id=document_id,
        content=content,
        strategy=strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if not chunks:
        raise HTTPException(status_code=400, detail="Document produced no chunks")

    points: List[Dict[str, Any]] = []
    for chunk in chunks:
        vector = rag.embedding_model.encode(chunk.content).tolist()
        points.append({
            "id": str(uuid.uuid4()),
            "vector": vector,
            "payload": {
                "document_id": document_id,
                "document_title": title,
                "content": chunk.content,
                "chunk_index": chunk.metadata.chunk_index,
            },
        })

    await qdrant.upsert_vectors(CHUNK_COLLECTION, points)
    logger.info(f"Ingested document {document_id} ('{title}'): {len(points)} chunks")

    return IngestResponse(
        document_id=document_id,
        title=title,
        chunks_created=len(points),
        collection=CHUNK_COLLECTION,
        embedding_dimension=len(points[0]["vector"]),
    )


# ==================== Endpoints ====================

@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest) -> IngestResponse:
    """Ingest raw text: chunk -> embed -> store. Immediately searchable."""
    return await _ingest_text(
        content=request.content,
        title=request.title,
        document_id=request.document_id,
        strategy=request.strategy,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
    )


@router.post("/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(..., description="Text/markdown file to ingest"),
    title: Optional[str] = Form(default=None),
    chunk_size: int = Form(default=500),
    chunk_overlap: int = Form(default=50),
) -> IngestResponse:
    """Upload a text/markdown file and ingest it through the full pipeline."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in TEXT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {sorted(TEXT_EXTENSIONS)}",
        )

    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("latin-1")

    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    return await _ingest_text(
        content=content,
        title=title or file.filename or "Untitled",
        document_id=None,
        strategy=ChunkingStrategy.SENTENCE,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


@router.get("", response_model=List[DocumentSummary])
async def list_documents() -> List[DocumentSummary]:
    """List ingested documents (grouped from chunk payloads)."""
    qdrant = get_qdrant_service()
    await qdrant.initialize()

    docs: Dict[str, DocumentSummary] = {}
    try:
        # Scroll through all points in the collection
        offset = None
        while True:
            records, offset = qdrant.client.scroll(
                collection_name=CHUNK_COLLECTION,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for rec in records:
                p = rec.payload or {}
                did = p.get("document_id", "unknown")
                if did not in docs:
                    docs[did] = DocumentSummary(
                        document_id=did,
                        title=p.get("document_title", "Untitled"),
                        chunk_count=0,
                    )
                docs[did].chunk_count += 1
            if offset is None:
                break
    except Exception as e:
        msg = str(e).lower()
        if "doesn't exist" in msg or "not found" in msg or "404" in msg:
            return []
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {e}")

    return list(docs.values())


class RelatedDocument(BaseModel):
    """A document semantically related to another."""
    document_id: str
    title: str
    score: float


@router.get("/{document_id}/related", response_model=List[RelatedDocument])
async def related_documents(document_id: str, limit: int = 5) -> List[RelatedDocument]:
    """
    Find documents semantically related to this one.

    Averages the target document's chunk embeddings into a centroid, finds the
    nearest chunks across the corpus, and aggregates by document (best chunk
    score per document, excluding the target). Pure vector similarity — no LLM.
    """
    from qdrant_client import models as qmodels
    import numpy as np

    qdrant = get_qdrant_service()
    await qdrant.initialize()
    client = qdrant.client

    # 1. Collect this document's chunk vectors
    vectors: List[List[float]] = []
    offset = None
    try:
        while True:
            recs, offset = client.scroll(
                collection_name=CHUNK_COLLECTION,
                scroll_filter=qmodels.Filter(
                    must=[qmodels.FieldCondition(
                        key="document_id",
                        match=qmodels.MatchValue(value=document_id),
                    )]
                ),
                limit=256, offset=offset, with_payload=False, with_vectors=True,
            )
            for r in recs:
                if r.vector is not None:
                    vectors.append(r.vector)
            if offset is None:
                break
    except Exception as e:
        msg = str(e).lower()
        if "doesn't exist" in msg or "not found" in msg or "404" in msg:
            return []
        raise HTTPException(status_code=500, detail=f"Failed to load document: {e}")

    if not vectors:
        raise HTTPException(status_code=404, detail="Document not found or has no chunks")

    # 2. Centroid → nearest chunks across the corpus
    centroid = np.mean(np.array(vectors, dtype=float), axis=0).tolist()
    resp = client.query_points(
        collection_name=CHUNK_COLLECTION,
        query=centroid,
        limit=60,
        with_payload=True,
    )

    # 3. Aggregate by document (best score per doc, excluding self)
    best: Dict[str, Any] = {}
    for p in resp.points:
        pl = p.payload or {}
        did = pl.get("document_id")
        if not did or did == document_id:
            continue
        title = pl.get("document_title", "Untitled")
        if did not in best or p.score > best[did][1]:
            best[did] = (title, float(p.score))

    ranked = sorted(best.items(), key=lambda kv: kv[1][1], reverse=True)[:limit]
    return [
        RelatedDocument(document_id=did, title=t, score=round(s, 3))
        for did, (t, s) in ranked
    ]


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> Dict[str, Any]:
    """Delete all chunks belonging to a document."""
    from qdrant_client import models as qmodels

    qdrant = get_qdrant_service()
    await qdrant.initialize()

    try:
        qdrant.client.delete(
            collection_name=CHUNK_COLLECTION,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {e}")

    return {"status": "deleted", "document_id": document_id}


@router.websocket("/ws/ingest")
async def ws_ingest(websocket: WebSocket):
    """
    WebSocket ingestion with real-time per-chunk progress.

    Client sends one JSON message:
        {"content": "...", "title": "...", "chunk_size": 500, "chunk_overlap": 50}

    Server streams:
        {"type": "started", "total_chunks": N, "document_id": "..."}
        {"type": "progress", "current": i, "total": N, "percentage": p}   (per chunk)
        {"type": "complete", "document_id": "...", "chunks_created": N}
        {"type": "error", "detail": "..."}
    """
    await websocket.accept()
    try:
        request = await websocket.receive_json()
        content = request.get("content", "")
        title = request.get("title", "Untitled")
        chunk_size = int(request.get("chunk_size", 500))
        chunk_overlap = int(request.get("chunk_overlap", 50))

        if not content or not content.strip():
            await websocket.send_json({"type": "error", "detail": "content is empty"})
            await websocket.close()
            return

        rag = get_rag_service()
        if rag.embedding_model is None:
            await websocket.send_json(
                {"type": "error", "detail": "embedding model not available"}
            )
            await websocket.close()
            return

        qdrant = get_qdrant_service()
        await qdrant.initialize()

        document_id = request.get("document_id") or str(uuid.uuid4())
        chunker = ChunkerService(
            default_chunk_size=chunk_size, default_chunk_overlap=chunk_overlap
        )
        chunks = chunker.chunk_document(
            document_id=document_id,
            content=content,
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        total = len(chunks)
        await websocket.send_json(
            {"type": "started", "total_chunks": total, "document_id": document_id}
        )

        for i, chunk in enumerate(chunks, 1):
            vector = rag.embedding_model.encode(chunk.content).tolist()
            await qdrant.upsert_vectors(CHUNK_COLLECTION, [{
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "document_id": document_id,
                    "document_title": title,
                    "content": chunk.content,
                    "chunk_index": chunk.metadata.chunk_index,
                },
            }])
            await websocket.send_json({
                "type": "progress",
                "current": i,
                "total": total,
                "percentage": round(i / total * 100, 1),
            })

        await websocket.send_json({
            "type": "complete",
            "document_id": document_id,
            "chunks_created": total,
        })
        await websocket.close()

    except WebSocketDisconnect:
        logger.info("WebSocket ingestion client disconnected")
    except Exception as e:
        logger.error(f"WebSocket ingestion error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "detail": str(e)})
            await websocket.close()
        except Exception:
            pass


@router.get("/stats")
async def stats() -> Dict[str, Any]:
    """Aggregate knowledge-base stats for the dashboard."""
    docs = await list_documents()
    total_chunks = sum(d.chunk_count for d in docs)

    conversation_count = 0
    try:
        from src.services.conversation_service import get_conversation_service
        svc = get_conversation_service()
        if svc.pool is not None:
            async with svc.pool.acquire() as conn:
                conversation_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM conversations"
                ) or 0
    except Exception as e:
        logger.warning(f"conversation count unavailable: {e}")

    return {
        "document_count": len(docs),
        "chunk_count": total_chunks,
        "conversation_count": conversation_count,
    }


@router.get("/health")
async def health() -> Dict[str, Any]:
    """Ingestion service health."""
    rag = get_rag_service()
    return {
        "status": "healthy" if rag.embedding_model is not None else "degraded",
        "service": "documents",
        "embeddings_available": rag.embedding_model is not None,
        "collection": CHUNK_COLLECTION,
    }
