"""
Tests for the local-first document ingestion routes.

Covers the chunk -> embed -> store pipeline with mocked embedding model and
Qdrant client (no infrastructure required).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

import numpy as np


@pytest.fixture
def mock_rag_service():
    """RAG service with a deterministic mock embedding model."""
    mock = MagicMock()
    mock.embedding_model = MagicMock()
    mock.embedding_model.encode = MagicMock(return_value=np.array([0.1] * 384))
    return mock


@pytest.fixture
def mock_qdrant_service():
    """Qdrant service with async upsert/initialize mocked."""
    mock = MagicMock()
    mock.initialize = AsyncMock()
    mock.upsert_vectors = AsyncMock()
    mock.client = MagicMock()
    return mock


@pytest.fixture
def client(mock_rag_service, mock_qdrant_service):
    """Test client with document-route dependencies patched."""
    with patch("src.routes.documents.get_rag_service", return_value=mock_rag_service), \
         patch("src.routes.documents.get_qdrant_service", return_value=mock_qdrant_service):
        from src.main import app
        yield TestClient(app)


class TestIngest:
    def test_ingest_text_creates_chunks(self, client, mock_qdrant_service):
        resp = client.post("/documents/ingest", json={
            "content": "This is the first sentence. This is the second sentence. "
                       "Here is a third one for good measure.",
            "title": "Test Doc",
            "chunk_size": 50,
            "chunk_overlap": 10,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Test Doc"
        assert data["chunks_created"] >= 1
        assert data["collection"] == "chunk_embeddings"
        assert data["embedding_dimension"] == 384
        mock_qdrant_service.upsert_vectors.assert_called()

    def test_ingest_empty_content_rejected(self, client):
        resp = client.post("/documents/ingest", json={"content": "", "title": "X"})
        assert resp.status_code == 422  # min_length=1 validation

    def test_ingest_uses_provided_document_id(self, client):
        resp = client.post("/documents/ingest", json={
            "content": "A sentence here.",
            "title": "Doc",
            "document_id": "fixed-id-123",
        })
        assert resp.status_code == 200
        assert resp.json()["document_id"] == "fixed-id-123"


class TestUpload:
    def test_upload_text_file(self, client):
        resp = client.post(
            "/documents/upload",
            files={"file": ("notes.txt", b"Sentence one. Sentence two.", "text/plain")},
            data={"title": "Notes"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Notes"

    def test_upload_rejects_unsupported_extension(self, client):
        resp = client.post(
            "/documents/upload",
            files={"file": ("image.png", b"\x89PNG", "image/png")},
        )
        assert resp.status_code == 400

    def test_upload_rejects_empty_file(self, client):
        resp = client.post(
            "/documents/upload",
            files={"file": ("empty.txt", b"   ", "text/plain")},
        )
        assert resp.status_code == 400


class TestHealth:
    def test_health_reports_embeddings_available(self, client):
        resp = client.get("/documents/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["embeddings_available"] is True
        assert data["status"] == "healthy"

    def test_health_degraded_without_embeddings(self, mock_qdrant_service):
        rag = MagicMock()
        rag.embedding_model = None
        with patch("src.routes.documents.get_rag_service", return_value=rag), \
             patch("src.routes.documents.get_qdrant_service", return_value=mock_qdrant_service):
            from src.main import app
            c = TestClient(app)
            resp = c.get("/documents/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "degraded"


class TestListDocuments:
    def test_list_groups_chunks_by_document(self, client, mock_qdrant_service):
        rec1 = MagicMock()
        rec1.payload = {"document_id": "d1", "document_title": "Doc One"}
        rec2 = MagicMock()
        rec2.payload = {"document_id": "d1", "document_title": "Doc One"}
        rec3 = MagicMock()
        rec3.payload = {"document_id": "d2", "document_title": "Doc Two"}
        # scroll returns (records, next_offset); stop after first page
        mock_qdrant_service.client.scroll = MagicMock(
            return_value=([rec1, rec2, rec3], None)
        )

        resp = client.get("/documents")
        assert resp.status_code == 200
        data = resp.json()
        by_id = {d["document_id"]: d for d in data}
        assert by_id["d1"]["chunk_count"] == 2
        assert by_id["d2"]["chunk_count"] == 1
