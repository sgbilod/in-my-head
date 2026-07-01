"""
Tests for the semantic answer cache (mocked Qdrant + embedding model).
"""

import json
import time
import pytest
from unittest.mock import MagicMock, patch

import numpy as np

from src.services.semantic_cache import SemanticCache, cache_enabled


def _mock_services(corpus_size=5, points=None):
    """Return patched (qdrant, rag) service mocks."""
    qmock = MagicMock()
    qmock.client = MagicMock()
    qmock.client.get_collection = MagicMock()  # collection exists → no create
    qmock.client.count.return_value = MagicMock(count=corpus_size)
    qmock.client.query_points.return_value = MagicMock(points=points or [])
    qmock.client.upsert = MagicMock()

    ragmock = MagicMock()
    ragmock.embedding_model = MagicMock()
    ragmock.embedding_model.encode = MagicMock(return_value=np.array([0.1] * 384))
    return qmock, ragmock


def _point(payload, score=0.99):
    p = MagicMock()
    p.score = score
    p.payload = payload
    return p


@pytest.mark.asyncio
async def test_lookup_miss_returns_none():
    q, r = _mock_services(points=[])
    with patch("src.services.semantic_cache.get_qdrant_service", return_value=q), \
         patch("src.services.semantic_cache.get_rag_service", return_value=r):
        cache = SemanticCache()
        assert await cache.lookup("what is ml?", "llama3") is None


@pytest.mark.asyncio
async def test_lookup_hit_returns_answer():
    payload = {
        "model": "llama3", "answer": "ML is a subset of AI.",
        "citations": json.dumps([{"document_id": "d1", "document_title": "AI",
                                  "chunk_id": "c1", "chunk_index": 0,
                                  "relevance_score": 0.9, "excerpt": "..."}]),
        "tokens_used": 42, "corpus_size": 5, "ts": time.time(),
    }
    q, r = _mock_services(corpus_size=5, points=[_point(payload, score=0.985)])
    with patch("src.services.semantic_cache.get_qdrant_service", return_value=q), \
         patch("src.services.semantic_cache.get_rag_service", return_value=r):
        cache = SemanticCache()
        hit = await cache.lookup("what is ML?", "llama3")
    assert hit is not None
    assert hit["answer"] == "ML is a subset of AI."
    assert hit["tokens_used"] == 42
    assert len(hit["citations"]) == 1
    assert hit["similarity"] == pytest.approx(0.985)


@pytest.mark.asyncio
async def test_lookup_stale_corpus_returns_none():
    # cached at corpus_size=5, but corpus is now 6 → stale → miss
    payload = {"model": "llama3", "answer": "x", "citations": "[]",
               "tokens_used": 1, "corpus_size": 5, "ts": time.time()}
    q, r = _mock_services(corpus_size=6, points=[_point(payload)])
    with patch("src.services.semantic_cache.get_qdrant_service", return_value=q), \
         patch("src.services.semantic_cache.get_rag_service", return_value=r):
        assert await SemanticCache().lookup("q", "llama3") is None


@pytest.mark.asyncio
async def test_lookup_wrong_model_returns_none():
    payload = {"model": "qwen3", "answer": "x", "citations": "[]",
               "tokens_used": 1, "corpus_size": 5, "ts": time.time()}
    q, r = _mock_services(corpus_size=5, points=[_point(payload)])
    with patch("src.services.semantic_cache.get_qdrant_service", return_value=q), \
         patch("src.services.semantic_cache.get_rag_service", return_value=r):
        assert await SemanticCache().lookup("q", "llama3") is None


@pytest.mark.asyncio
async def test_lookup_expired_ttl_returns_none():
    payload = {"model": "llama3", "answer": "x", "citations": "[]",
               "tokens_used": 1, "corpus_size": 5, "ts": time.time() - 100_000}
    q, r = _mock_services(corpus_size=5, points=[_point(payload)])
    with patch("src.services.semantic_cache.get_qdrant_service", return_value=q), \
         patch("src.services.semantic_cache.get_rag_service", return_value=r):
        assert await SemanticCache(ttl_seconds=3600).lookup("q", "llama3") is None


@pytest.mark.asyncio
async def test_store_upserts_point():
    q, r = _mock_services(corpus_size=5)
    with patch("src.services.semantic_cache.get_qdrant_service", return_value=q), \
         patch("src.services.semantic_cache.get_rag_service", return_value=r):
        await SemanticCache().store("q", "llama3", "answer", [{"document_id": "d1"}], 10)
    q.client.upsert.assert_called_once()
    kwargs = q.client.upsert.call_args.kwargs
    assert kwargs["collection_name"] == "query_cache"
    assert len(kwargs["points"]) == 1


@pytest.mark.asyncio
async def test_lookup_degrades_on_error():
    q, r = _mock_services()
    q.client.query_points.side_effect = Exception("qdrant down")
    with patch("src.services.semantic_cache.get_qdrant_service", return_value=q), \
         patch("src.services.semantic_cache.get_rag_service", return_value=r):
        assert await SemanticCache().lookup("q", "llama3") is None  # no raise


@pytest.mark.asyncio
async def test_disabled_via_env(monkeypatch):
    monkeypatch.setenv("RAG_CACHE_ENABLED", "false")
    assert cache_enabled() is False
    assert await SemanticCache().lookup("q", "llama3") is None
