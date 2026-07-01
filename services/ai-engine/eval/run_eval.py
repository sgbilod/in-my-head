#!/usr/bin/env python
"""
Retrieval evaluation harness — measure /rag/retrieve quality on a gold set.

Runs each gold query through the retrieval endpoint (no LLM generation, so it's
fast and deterministic) and computes:
  - Hit@k : fraction of queries whose expected document appears in the top-k
            retrieved chunks (for k = 1, 3, 5)
  - MRR   : mean reciprocal rank of the first chunk from the expected document

This is the regression gate for retrieval changes (embedding upgrades,
contextual retrieval, reranker tweaks): run it before and after to prove a
change actually helps rather than guessing.

Usage:
    python eval/run_eval.py                       # uses http://localhost:8001
    AI_ENGINE_URL=http://host:8001 python eval/run_eval.py
    python eval/run_eval.py --top-k 5 --gold eval/gold_set.json
"""

import os
import sys
import json
import argparse
from pathlib import Path

import httpx


def load_gold(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["cases"]


def retrieved_titles(base_url: str, query: str, top_k: int) -> list[str]:
    """Return the ordered list of document titles for the top-k retrieved chunks."""
    r = httpx.post(
        f"{base_url}/rag/retrieve",
        json={"query": query, "top_k": top_k, "use_reranking": True},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    titles = []
    for chunk in data.get("chunks", []):
        t = (chunk.get("metadata") or {}).get("document_title")
        titles.append(t)
    # Fall back to citations if chunk metadata lacks titles.
    if not any(titles):
        titles = [c.get("document_title") for c in data.get("citations", [])]
    return titles


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default=str(Path(__file__).parent / "gold_set.json"))
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--url", default=os.getenv("AI_ENGINE_URL", "http://localhost:8001"))
    args = ap.parse_args()

    cases = load_gold(Path(args.gold))
    ks = [1, 3, 5]
    hits = {k: 0 for k in ks}
    rr_sum = 0.0
    misses = []

    print(f"Evaluating {len(cases)} queries against {args.url} (top_k={args.top_k})\n")
    for c in cases:
        q, expected = c["query"], c["expected_title"]
        try:
            titles = retrieved_titles(args.url, q, args.top_k)
        except Exception as e:
            print(f"  ERROR  {q[:50]!r}: {e}")
            misses.append(q)
            continue

        # first rank (1-based) where the expected title appears
        rank = next((i + 1 for i, t in enumerate(titles) if t == expected), None)
        for k in ks:
            if rank is not None and rank <= k:
                hits[k] += 1
        rr_sum += (1.0 / rank) if rank else 0.0

        mark = f"@{rank}" if rank else "MISS"
        print(f"  [{mark:>4}] {q[:52]:<52} -> {(titles[0] if titles else '-')[:22]}")
        if rank is None:
            misses.append(q)

    n = len(cases)
    print("\n" + "=" * 52)
    print("RETRIEVAL QUALITY")
    for k in ks:
        print(f"  Hit@{k}: {hits[k]}/{n} = {hits[k]/n*100:5.1f}%")
    print(f"  MRR  : {rr_sum/n:.3f}")
    if misses:
        print(f"\n  {len(misses)} miss(es):")
        for m in misses:
            print(f"    - {m}")
    print("=" * 52)

    # Non-zero exit if retrieval is clearly broken (Hit@5 below 50%),
    # so this can gate CI.
    return 0 if hits[5] / n >= 0.5 else 1


if __name__ == "__main__":
    sys.exit(main())
