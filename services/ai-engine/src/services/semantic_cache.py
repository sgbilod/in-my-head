"""
Semantic answer cache for RAG queries.

Caches final RAG answers keyed by the *query embedding*. When a new query is
near-identical (cosine >= threshold) to one already answered, the stored answer
is returned in ~milliseconds instead of re-running retrieval + local-LLM
generation (which takes 30-120s with Ollama). Uses the existing Qdrant instance
(a dedicated `query_cache` collection), so no new infrastructure.

Correctness / invalidation:
- Each entry records the corpus size (number of chunks in `chunk_embeddings`)
  at write time. If the corpus changes (documents added/removed), cached
  entries are treated as stale and ignored — answers never go out of date after
  ingestion.
- Entries carry a TTL and are scoped to the model that produced them.
- All operations fail open: any cache error degrades to a normal (uncached)
  RAG query rather than erroring.
"""

import os
import json
import time
import uuid
import logging
from typing import Optional, Dict, Any, List

from qdrant_client.models import Distance, VectorParams, PointStruct

from src.services.qdrant_service import get_qdrant_service
from src.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

CACHE_COLLECTION = "query_cache"
CHUNK_COLLECTION = "chunk_embeddings"


def cache_enabled() -> bool:
    return os.getenv("RAG_CACHE_ENABLED", "true").lower() not in ("0", "false", "no")


class SemanticCache:
    """Embedding-keyed cache of RAG answers backed by Qdrant."""

    def __init__(
        self,
        threshold: float = 0.97,
        ttl_seconds: int = 86_400,
        embedding_dim: int = 384,
    ):
        self.threshold = float(os.getenv("RAG_CACHE_THRESHOLD", threshold))
        self.ttl = int(os.getenv("RAG_CACHE_TTL", ttl_seconds))
        self.dim = embedding_dim
        self._ready = False

    async def ensure(self) -> None:
        if self._ready:
            return
        client = get_qdrant_service().client
        try:
            client.get_collection(CACHE_COLLECTION)
        except Exception:
            client.create_collection(
                collection_name=CACHE_COLLECTION,
                vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
            )
            logger.info("Created semantic query_cache collection")
        self._ready = True

    def _corpus_size(self) -> int:
        try:
            return get_qdrant_service().client.count(
                collection_name=CHUNK_COLLECTION, exact=False
            ).count
        except Exception:
            return -1

    def _embed(self, query: str) -> Optional[List[float]]:
        rag = get_rag_service()
        if getattr(rag, "embedding_model", None) is None:
            return None
        return rag.embedding_model.encode(query).tolist()

    async def lookup(self, query: str, model: str) -> Optional[Dict[str, Any]]:
        """Return a cached answer dict for a near-identical query, else None."""
        if not cache_enabled():
            return None
        try:
            await self.ensure()
            vec = self._embed(query)
            if vec is None:
                return None
            resp = get_qdrant_service().client.query_points(
                collection_name=CACHE_COLLECTION,
                query=vec,
                limit=1,
                score_threshold=self.threshold,
                with_payload=True,
            )
            pts = resp.points
            if not pts:
                return None
            p = pts[0]
            pl = p.payload or {}
            if pl.get("model") != model:
                return None
            if time.time() - float(pl.get("ts", 0)) > self.ttl:
                return None
            if pl.get("corpus_size", -2) != self._corpus_size():
                return None  # corpus changed → stale
            logger.info(f"Semantic cache HIT (sim={p.score:.3f}) for: {query[:60]}")
            return {
                "answer": pl.get("answer", ""),
                "citations": json.loads(pl.get("citations", "[]")),
                "tokens_used": int(pl.get("tokens_used", 0)),
                "model": pl.get("model", model),
                "similarity": float(p.score),
            }
        except Exception as e:
            logger.warning(f"Semantic cache lookup failed (degrading): {e}")
            return None

    async def store(
        self,
        query: str,
        model: str,
        answer: str,
        citations: List[Dict[str, Any]],
        tokens_used: int,
    ) -> None:
        if not cache_enabled():
            return
        try:
            await self.ensure()
            vec = self._embed(query)
            if vec is None:
                return
            get_qdrant_service().client.upsert(
                collection_name=CACHE_COLLECTION,
                points=[
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vec,
                        payload={
                            "query": query,
                            "model": model,
                            "answer": answer,
                            "citations": json.dumps(citations),
                            "tokens_used": tokens_used,
                            "corpus_size": self._corpus_size(),
                            "ts": time.time(),
                        },
                    )
                ],
            )
            logger.info(f"Semantic cache STORE for: {query[:60]}")
        except Exception as e:
            logger.warning(f"Semantic cache store failed (ignored): {e}")


_semantic_cache: Optional[SemanticCache] = None


def get_semantic_cache() -> SemanticCache:
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    return _semantic_cache
