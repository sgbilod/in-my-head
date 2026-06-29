"""
Parse-and-ingest router (local-first, single architecture).

The document-processor's role is **parsing heavy formats** (PDF, DOCX, PPTX,
HTML, Markdown, TXT). It does NOT embed or store vectors itself — that is the
ai-engine's canonical responsibility. After parsing, the extracted text is
forwarded to the ai-engine's /documents/ingest endpoint, which chunks, embeds
locally (sentence-transformers, 384-dim), and stores to the `chunk_embeddings`
Qdrant collection that RAG retrieval reads from.

This replaces the old Celery pipeline, which used OpenAI embeddings (3072-dim,
wrong collection, violates the No-OpenAI rule) and required a Celery worker.
"""

import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from ..parsers import ParserFactory
from ..parsers.base_parser import UnsupportedFormatError, ParsingError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ingest"])

# ai-engine canonical ingestion endpoint (IPv4 to avoid Windows IPv6 refusal)
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://127.0.0.1:8001")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@router.post("/ingest", summary="Parse a document and ingest it into the knowledge base")
async def parse_and_ingest(
    file: UploadFile = File(..., description="Document to parse and ingest"),
    title: Optional[str] = Form(default=None),
):
    """
    Parse an uploaded document (PDF/DOCX/PPTX/HTML/MD/TXT) and forward the
    extracted text to the ai-engine for chunking, local embedding, and storage.

    Returns the ai-engine ingestion result plus parsing metadata.
    """
    filename = file.filename or "document"
    suffix = Path(filename).suffix.lower()

    # Persist to a temp path so file-based parsers can read it
    tmp_path = UPLOAD_DIR / f"{uuid.uuid4()}{suffix}"
    try:
        with open(tmp_path, "wb") as out:
            shutil.copyfileobj(file.file, out)

        if tmp_path.stat().st_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 100MB)")

        if not ParserFactory.is_supported(tmp_path):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported format '{suffix}'. Supported: "
                    f"{', '.join(ParserFactory.get_supported_formats())}"
                ),
            )

        # Parse to text
        try:
            parser = ParserFactory.get_parser(tmp_path)
            parsed = await parser.parse(tmp_path)
        except (UnsupportedFormatError, ParsingError) as e:
            raise HTTPException(status_code=422, detail=f"Failed to parse document: {e}")

        text = (parsed.text or "").strip()
        if not text:
            raise HTTPException(
                status_code=422, detail="Document contained no extractable text"
            )

        # Forward to the ai-engine canonical ingestion path
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{AI_ENGINE_URL}/documents/ingest",
                    json={"content": text, "title": title or filename},
                )
                resp.raise_for_status()
                ingest_result = resp.json()
        except httpx.HTTPStatusError as e:
            detail = e.response.text
            raise HTTPException(
                status_code=502,
                detail=f"ai-engine ingestion failed ({e.response.status_code}): {detail}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Could not reach ai-engine at {AI_ENGINE_URL}: {e}",
            )

        logger.info(
            f"Parsed '{filename}' with {parsed.parser_used} "
            f"({parsed.text_length} chars) -> ingested as "
            f"{ingest_result.get('document_id')}"
        )

        return {
            "status": "ingested",
            "filename": filename,
            "parser_used": parsed.parser_used,
            "text_length": parsed.text_length,
            **ingest_result,
        }

    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


@router.get("/supported-formats", summary="List supported document formats")
async def supported_formats():
    """Return the file extensions the parser layer can handle."""
    return {"formats": ParserFactory.get_supported_formats()}
