# CLAUDE.md — In My Head

> **AI-powered personal knowledge management — "Your Knowledge, Infinitely Connected"**

## Project Identity
- **Repo:** `sgbilod/4` (GitHub remote — needs renaming)
- **Local path:** `C:\Users\sgbil\In My Head\`
- **Stack:** Python (FastAPI) + TypeScript (Express) + React + PyQt6
- **Castle Layer:** Standalone personal project (not in Sigma ecosystem)
- **Version:** v0.1.0 (pre-release)
- **Replaces:** Notion, Obsidian, Evernote (local-first, AI-native)

---

## Architecture (v0.1.0 — post-audit, scaffolds cut)

> See [ACTION_PLAN.md](ACTION_PLAN.md) for the full audit, progress, and roadmap.
> **Cut from v0.1.0** (were non-functional scaffolds): `api-gateway` (proxied nothing),
> `search-service` (no search endpoint), `resource-manager` (empty). The frontend talks
> to the ai-engine directly; document stats are served by ai-engine `/documents/stats`.

```
┌────────────────────────────────────────────────────┐
│              InMyHead.py (PyQt6 Launcher)          │
│  Desktop GUI — starts services, drag-drop uploads  │
├────────────────────────────────────────────────────┤
│        frontend/web-interface (React+Vite :3001)   │
│  Dashboard · Documents · Search · Chat             │
│  Vite dev proxy /api → ai-engine :8001             │
├──────────────────────────┬─────────────────────────┤
│ ai-engine :8001          │ document-processor :8002 │
│ FastAPI                  │ FastAPI                  │
│ RAG, LLM (Ollama),       │ Parse PDF/DOCX/PPTX/…    │
│ chunk, embed, ingest,    │ → forward text to        │
│ conversations (Postgres) │   ai-engine /documents   │
├──────────────────────────┴─────────────────────────┤
│  PostgreSQL :5432 │ Redis :6379 │ Qdrant :6333     │
│  Ollama :11434 (local LLM + embeddings)            │
└────────────────────────────────────────────────────┘
```

---

## Key File Map

| What | File |
|------|------|
| Desktop launcher | `InMyHead.py` |
| AI engine entry | `services/ai-engine/src/main.py` |
| RAG routes | `services/ai-engine/src/routes/rag.py` |
| Chunking routes | `services/ai-engine/src/routes/chunking.py` |
| Conversations API | `services/ai-engine/src/api/conversations.py` |
| LLM service | `services/ai-engine/src/services/llm_service.py` |
| Qdrant service | `services/ai-engine/src/services/qdrant_service.py` |
| RAG service | `services/ai-engine/src/services/rag_service.py` |
| Document processor | `services/document-processor/src/app.py` |
| Search service | `services/search-service/src/main.py` |
| Resource manager | `services/resource-manager/src/main.py` |
| API gateway | `services/api-gateway/src/index.ts` |
| Web frontend | `frontend/web-interface/` |
| Desktop frontend | `frontend/desktop-app/src/` |
| Infrastructure | `docker-compose.infrastructure.yml` |
| AI engine tests | `services/ai-engine/tests/` |
| Integration tests | `tests/integration/test_services.py` |
| Requirements | `services/ai-engine/requirements.txt` |
| Config (.env) | `.env` (DATABASE_URL, REDIS_URL, QDRANT_URL, OLLAMA_*, MINIO_*) |

---

## Sprint Plan

### Sprint 1: Test Suite Green (Unit Tests) ✅
148/148 unit tests pass, 55% coverage baseline.

- [x] **S1-A**: Fix `tests/test_conversation_service.py` import error
- [x] **S1-B**: Fix `tests/test_llm_service.py` import error
- [x] **S1-C**: Fix Pydantic v2 deprecation warnings
- [x] **S1-D**: 148 unit tests green (`-m "not integration and not ml"`)
- [x] **S1-E**: Coverage baseline: 55% (llm_service 100%, rag_service 93%, chunker 92%)

### Sprint 2: Service Startup + Integration
All services running locally.

- [x] **S2-A**: Docker infra up (PostgreSQL :5432, Redis :6379, Qdrant :6333, MinIO :9000)
- [x] **S2-B**: ai-engine :8001 — healthy
- [x] **S2-C**: document-processor :8002 — degraded (no Celery worker, expected)
- [x] **S2-D**: search-service :8003 — healthy
- [x] **S2-E**: resource-manager :8004 — healthy
- [x] **S2-F**: api-gateway :3000 — healthy (port 3000, not 8000)
- [x] **S2-G**: Integration tests: 6 pass, 4 skipped (E2E placeholders)

### Sprint 3: Ollama LLM Integration (Local-First AI)
The RAG pipeline references LLM but may be stubbed. Wire to Ollama.

- [x] **S3-A**: Ollama client added to `llm_service.py` — `generate_ollama()` + streaming, connects to 4 local models (llama3, llama3.1, qwen3, gemma4)
- [x] **S3-B**: `POST /rag/query` calls Ollama (verified: "What is ML?" → grounded answer, 176 tokens)
- [x] **S3-C**: Real doc E2E — ingested photosynthesis doc (5 chunks → embed → Qdrant → query → Ollama answer with [Doc 3] citation)
- [x] **S3-D**: Default chain = local Ollama → Gemini (fallback) → Claude. Configurable via OLLAMA_HOST/OLLAMA_MODEL env. RAG route default model = `llama3`.

**S3 fixes:** sentence-transformers installed (embeddings); qdrant-client `.search()`→`.query_points()` (1.18 API); graceful empty-result on missing collection; OLLAMA_MODELS env → F:\Dev\ollama\models (S:\ drive offline).

### Sprint 4: Document Pipeline End-to-End
Upload a file and get it searchable, all the way through.

**Decision:** document-processor's Celery pipeline uses OpenAI embeddings (3072-dim,
violates No-OpenAI rule), stores to wrong collection (`documents` vs `chunk_embeddings`),
and dimension-mismatches the 384-dim Qdrant collections. Built a **local-first ingestion
route on ai-engine** instead (`src/routes/documents.py`) — reuses the Sprint 3 chunker +
sentence-transformers + Qdrant path, no external APIs. document-processor async path left
as-is (separate concern; needs Celery worker + values reconciliation).

**RECONCILED (post-Sprint 4):** document-processor refactored from a Celery/OpenAI
pipeline into a **pure parsing front-end**. It now parses heavy formats (PDF/DOCX/
PPTX/HTML/MD/TXT) and forwards extracted text to the ai-engine's `/documents/ingest`
— one ingestion architecture, one collection, no OpenAI/Celery/Anthropic.
- New: `services/document-processor/src/api/routes_ingest.py` — `POST /api/v1/ingest`
- `app.py` now mounts only `routes_health` + `routes_ingest`; legacy Celery/OpenAI
  routers (`routes_documents`, `routes_search`, `routes_websocket`) unmounted; `jobs/tasks.py` marked DEPRECATED
- `routes_health.py`: Celery/Redis checks → parser-layer + ai-engine reachability (now reports **healthy**, not degraded)
- `parser_factory.py`: `import magic` made optional (Windows has no libmagic)
- Deps installed: python-docx, python-pptx, chardet
- Verified E2E: volcanoes.pdf (PdfParser→2 chunks) + aqueducts.docx (DocxParser→2 chunks)
  → chunk_embeddings (384-dim) → RAG query "Where are most volcanoes found?" → correct
  answer citing volcanoes.pdf
- Pre-existing tech debt (NOT addressed): 3 entry points in document-processor
  (`app.py` runs; `main.py` + `tests/test_main.py` target a stale src.routes path needing psycopg2)

- [x] **S4-A**: `POST /documents/upload` (file) + `POST /documents/ingest` (raw text) — uploaded quantum.md → 6 chunks
- [x] **S4-B**: Chunking runs automatically in ingest pipeline (ChunkerService, sentence strategy)
- [x] **S4-C**: Local embeddings (384-dim) generated + stored in `chunk_embeddings` Qdrant collection
- [x] **S4-D**: Semantic search returns chunks — verified via `/rag/query` ("event horizon" → correct [Doc 2] from Black Holes)
- [x] **S4-E**: WebSocket `/documents/ws/ingest` streams real per-chunk progress (20%→100%), verified with live client
- [x] **Extra**: `GET /documents` (list), `DELETE /documents/{id}` (remove chunks), `GET /documents/health`; 9 unit tests added

### Sprint 5: Web Frontend ✅
React + Vite + TS + Tailwind SPA, builds clean, wired to ai-engine via proxy.

**State found:** scaffolded but never built — 30+ TS errors, two parallel API-client
systems, two layout systems, wrong import paths, components importing non-existent
exports. Removed orphaned broken clusters (`components/documents/`, `components/layout/`,
`contexts/`, `lib/api/`, `types/api.ts`) and standardized on `lib/api-client.ts`
(baseURL `/api`, proxied to ai-engine).

- [x] **S5-A**: Builds clean — `npm run build` → 0 TS errors, 252 kB bundle (82 kB gzip)
- [x] **S5-B**: Connects to backend — Documents page lists/uploads/deletes via `/api/documents/*` (verified live: 3 docs render with chunk counts)
- [N/A] **S5-C**: Knowledge graph viz — not implemented in codebase (plan said "if implemented")
- [x] **S5-D**: Multi-turn RAG chat — Chat + Search pages call `/api/rag/query`, render grounded answers + citations (verified live via browser: "photosynthesis" query → answer citing [Doc 2,3,5], 7 sources)

**Rewrote:** `pages/Chat.tsx` (client-side multi-turn RAG, no DB dependency),
`pages/Documents.tsx` (upload/list/delete), `pages/Search.tsx` (RAG search + sources),
`lib/api-client.ts` (typed `api.*` helpers).
**Fixes:** Vite proxy `localhost`→`127.0.0.1:8001` (Node IPv6 ECONNREFUSED); ragQuery
axios timeout 30s→180s (local Ollama is slow). Dev server: `npm run dev` → :3001.

### Sprint 6: Polish + Ship
- [ ] **S6-A**: Fix GitHub remote (currently `sgbilod/4` — rename to `in-my-head`)
- [ ] **S6-B**: Clean up root directory — move loose scripts/reports to `docs/archive/`
- [ ] **S6-C**: Delete `.history/` directory (VS Code local history, 200+ stale copies)
- [ ] **S6-D**: Delete exposed API keys: `C:\Users\sgbil\Claude_Desktop\Projects\In-My-Head\In My Head-API.txt`
- [ ] **S6-E**: Ensure `.env` is gitignored (contains secrets)
- [ ] **S6-F**: Test InMyHead.py desktop launcher — starts services + opens browser
- [ ] **S6-G**: Tag v0.1.0

---

## Done Criteria
- [ ] AI engine unit tests all pass
- [ ] All 5 services start and respond to health checks
- [ ] Upload a PDF → chunk → embed → RAG query returns relevant answer
- [ ] Web frontend accessible and functional
- [ ] No secrets committed to git
- [ ] GitHub remote correctly named

## Completion Signal
```bash
git tag v0.1.0 && git push origin v0.1.0
```

---

## External Dependencies

| Service | Required For | How to Start |
|---------|-------------|--------------|
| PostgreSQL 15 | Document metadata, conversations | `docker compose -f docker-compose.infrastructure.yml up -d` |
| Redis 7 | Cache, sessions | Same compose file |
| Qdrant | Vector embeddings | Same compose file |
| MinIO | File storage | Same compose file |
| Ollama | Local LLM inference | System service (already running on Debian) |

## Critical Rules
1. **No cloud LLM calls by default** — Ollama first, Gemini API only as explicit fallback
2. **No OpenAI** — values-driven decision (see global CLAUDE.md)
3. **Never commit .env** — contains DB passwords, API keys, JWT secrets
4. **Local-first always** — all processing on user's machine, no data leaves device
5. **Don't break InMyHead.py** — the PyQt6 launcher is the user-facing entry point
