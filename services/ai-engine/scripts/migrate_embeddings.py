"""
Re-embed the corpus after an embedding-model change.

Switching the embedding model (e.g. all-MiniLM-L6-v2 384-dim → gte-base 768-dim)
changes the vector space AND the dimension, so every stored chunk must be
re-embedded and the Qdrant collections recreated at the new dimension. Chunk
text is preserved in each point's payload ("content"), so this re-embeds from
that — no need to re-upload the original files.

Steps:
  1. Read all points (id + payload) from `chunk_embeddings`.
  2. Recreate `chunk_embeddings` at the new dimension.
  3. Re-embed each chunk's content with the configured model, re-insert.
  4. Recreate `query_cache` empty at the new dimension (the cache repopulates).

Run from services/ai-engine:  python scripts/migrate_embeddings.py
Stop the ai-engine first (so it reloads the new model on next start).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

from src.config import settings

CHUNK_COLLECTION = "chunk_embeddings"
CACHE_COLLECTION = "query_cache"


def main() -> int:
    model_name = settings.embedding_model
    dim = settings.embedding_dimension
    qdrant_url = settings.qdrant_url

    print(f"Target model: {model_name} (dim={dim}) @ {qdrant_url}")
    client = QdrantClient(url=qdrant_url)

    # 1. Read all existing points (id + payload) ------------------------------
    try:
        existing = []
        offset = None
        while True:
            recs, offset = client.scroll(
                collection_name=CHUNK_COLLECTION,
                limit=256, offset=offset, with_payload=True, with_vectors=False,
            )
            existing.extend(recs)
            if offset is None:
                break
    except Exception as e:
        print(f"No existing {CHUNK_COLLECTION} to migrate ({e}); will create fresh.")
        existing = []

    print(f"Found {len(existing)} existing chunks to re-embed.")

    # 2. Load the new model ---------------------------------------------------
    print("Loading embedding model (first run downloads it)...")
    model = SentenceTransformer(model_name)
    actual = model.get_sentence_embedding_dimension()
    if actual != dim:
        print(f"WARNING: model dim {actual} != configured {dim}; using {actual}.")
        dim = actual

    # 3. Recreate chunk_embeddings at the new dimension -----------------------
    client.recreate_collection(
        collection_name=CHUNK_COLLECTION,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    # 4. Re-embed + re-insert in batches -------------------------------------
    BATCH = 64
    migrated = 0
    for i in range(0, len(existing), BATCH):
        batch = existing[i:i + BATCH]
        texts = [(r.payload or {}).get("content", "") for r in batch]
        vectors = model.encode(texts, batch_size=BATCH, show_progress_bar=False)
        points = [
            PointStruct(id=r.id, vector=v.tolist(), payload=r.payload)
            for r, v in zip(batch, vectors)
        ]
        client.upsert(collection_name=CHUNK_COLLECTION, points=points)
        migrated += len(points)
        print(f"  re-embedded {migrated}/{len(existing)}")

    # 5. Recreate the (now dimension-mismatched) semantic cache, empty --------
    client.recreate_collection(
        collection_name=CACHE_COLLECTION,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    print(f"Recreated empty {CACHE_COLLECTION} at dim={dim}.")

    print(f"\nDone. Re-embedded {migrated} chunks at dim={dim} with {model_name}.")
    print("Restart the ai-engine so it serves queries with the new model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
