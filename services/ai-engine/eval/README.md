# Retrieval Evaluation

Measures the quality of `/rag/retrieve` against a labeled gold set, so retrieval
changes (embedding-model upgrades, contextual retrieval, reranker tweaks) can be
**proven** to help instead of guessed at. Retrieval-only (no LLM generation), so
it's fast and deterministic.

## Run
```bash
# ai-engine must be running with the corpus ingested
python eval/run_eval.py
# or point at a different host:
AI_ENGINE_URL=http://host:8001 python eval/run_eval.py
```

## Metrics
- **Hit@k** — fraction of queries whose expected document appears in the top-k retrieved chunks (k = 1, 3, 5)
- **MRR** — mean reciprocal rank of the first chunk from the expected document

Exits non-zero if Hit@5 < 50% (usable as a CI gate).

## Baseline (2026-07-01, demo corpus, all-MiniLM-L6-v2 + hybrid + cross-encoder rerank)
`Hit@1 = 100% · Hit@3 = 100% · Hit@5 = 100% · MRR = 1.000` (12 queries)

## Gold set
Edit `gold_set.json` — each case is `{ "query": ..., "expected_title": ... }`.
Regenerate for your own corpus; the demo set covers the 5 sample documents.
Run this before **and after** any retrieval change and compare.
