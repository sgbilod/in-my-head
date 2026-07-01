# In My Head — Next Steps Action Plan & Innovation Roadmap
_Generated 2026-06-29 from a 9-stream parallel audit (5 code audits + 4 innovation research streams)._

> ## ✅ PROGRESS (updated 2026-06-29)
> **Phase 1 (Foundation) — largely DONE & verified:**
> - **1.1 DB single source of truth** ✅ — created canonical `migrations/001_initial_schema.sql` + idempotent runner (`src/db_init.py`); ai-engine lifespan applies all migrations on startup. Verified against live Postgres.
> - **1.2 DSN reconciled** ✅ — conversation_service reads `DATABASE_URL` (`5432/inmyhead`, user `inmyhead_user`); the bogus `5434/inmyhead_dev` default is gone.
> - **1.3 document-processor deploy fixed** ✅ — both Dockerfiles now run `src.app:app` on **8002** (was legacy `src.main` on 8001); added missing `httpx`/`chardet`.
> - **1.4 No-OpenAI enforced + missing deps** ✅ — purged `openai` from ai-engine (code+tests+2 requirements) and document-processor requirements; added `asyncpg`. **158/158 ai-engine unit tests green.**
> - **1.5 port ownership** ◑ — search-service default→8003 fixed; docker-compose swaps + gateway URLs still TODO.
>
> **Phase 2 (Correctness) — P0 DONE:**
> - **2.1 Conversations are REAL now** ✅ — mounted the Postgres router (`src/routes/conversations.py`), unmounted the in-memory fake. **Verified E2E via HTTP:** create → send message → real grounded Ollama answer (596 tok, 5 citations) **persisted to Postgres** → GET returns 2 messages from DB → list shows message_count=2.
> - **2.2 `_retrieve_without_cache` stub** ✅ (resolved by 2.1) — the live conversations path no longer touches `cached_rag_service`; it uses `rag_service.retrieve` directly.
> - **2.4 honest `/ready`** ◑ — ai-engine now probes Qdrant + Postgres for real; other services still TODO.
>
> **Phase 2.3 (scaffolds) — DECIDED: CUT.** api-gateway / search-service / resource-manager removed from the v0.1.0 story (frontend already talks to ai-engine directly). Frontend nav trimmed to the 4 working pages; CLAUDE.md architecture updated. _TODO: de-list them from the compose files during Phase 4.3 consolidation._
>
> **Phase 3 (Frontend) — Dashboard DONE.** Added ai-engine `GET /documents/stats`; Dashboard now shows live counts (verified in-browser: 5 docs / 20 chunks / 1 conversation + recent-docs list). Collections page cut (was a static stub); nav = Dashboard/Documents/Search/Chat. Frontend builds clean.
>
> **Phase 4 (partial) — DONE:**
> - **Single startup script** ✅ — `start.ps1` at repo root brings up infra → Ollama → ai-engine (:8001) → document-processor (:8002) → frontend (:3001) in dependency order, with correct ports + DATABASE_URL. Supersedes the fragmented start-*.ps1.
> - **InMyHead.py launcher fixed** ✅ — uses the root `docker-compose.infrastructure.yml`; health-checks ai-engine (:8001) with the correct label; "Open Web Interface" now opens the real app at **:3001** (was Swagger). (The `3000` the audit flagged was a tray-notification timeout, not a port — left as-is.)
>
> **Phase 0 security + Phase 4 ship — DONE (2026-07-01):**
> - Keys rotated (by owner); loose key file deleted; committed dev `SECRET_KEY`/`JWT_SECRET` regenerated into untracked `.env`.
> - Leaked artifacts **purged from all git history** (`git-filter-repo`, 121 commits rewritten) after a safety mirror (`../in-my-head-PREPURGE-backup.git`); force-pushed.
> - Repo cleanup committed (52 root reports → `docs/archive/`, dead patch scripts + empty Electron scaffold + committed `venv/` removed).
> - GitHub repo renamed **`sgbilod/4` → `sgbilod/in-my-head`**; README badge `[USERNAME]` placeholders fixed.
> - **Tagged and pushed `v0.1.0`.** 🎉
>
> **Remaining (low priority, optional):** prune the ~90 stale dependabot branches; compose-file consolidation; delete the safety mirror once the push is confirmed good.


> **Bottom line:** There is a genuinely good, working core here — and the audit shows the project is **less complete than the sprint checkmarks claim**. This plan separates what truly works from what is scaffolded, then gives a dependency-ordered path to a real, shippable, secure v0.1.0, followed by a tiered innovation roadmap that turns the app into a category-defining "thinking second brain."

---

## PART 1 — VERIFIED STATUS (honest)

### ✅ What genuinely works (the real product)
The end-to-end **local-first RAG pipeline** is real and well-built:
> upload a document (text → ai-engine, or PDF/DOCX/PPTX/HTML/MD → document-processor parse → forward) → chunk → local sentence-transformers embed (384-dim) → Qdrant `chunk_embeddings` → `/rag/query` → hybrid search + cross-encoder rerank → grounded **Ollama** answer with citations.

- **ai-engine (:8001)** — the strong core. RAG (~90% real), local ingestion + WebSocket progress, Ollama→Gemini→Claude fallback chain. ~220 passing unit tests.
- **document-processor (:8002)** — real parse-and-forward refactor + 8 genuine parsers (PDF/DOCX/PPTX/HTML/MD/TXT).
- **Web frontend** — builds clean; Documents, Search, Chat pages are functional against the backend.

### ⚠️ What is claimed but NOT real as shipped
| Area | Claimed | Reality |
|---|---|---|
| "5 microservices + gateway" | 5 working services | **~1.7 real services** + 3 scaffolds |
| **Conversations** | multi-turn persistent RAG chat | **Wrong implementation wired** — in-memory (no persistence) + a placeholder that echoes context instead of calling the LLM. The real Postgres version is orphaned/unmounted. |
| **api-gateway (:3000)** | reverse proxy, rate limit, auth | **Zero proxy routes** — decorative; every upstream port map is wrong |
| **search-service (:8003)** | vector/keyword/hybrid search | **~3% — no search endpoint exists at all** |
| **resource-manager (:8004)** | discovery/analytics | **~3% — empty scaffold** |
| **Database** | persistent schema | **No single source of truth** — 3 conflicting defs (Prisma/SQLAlchemy/SQL), empty Alembic migration, tables created manually then patched by `fix_*.py` scripts. If the DB is deleted, it can't be reliably recreated. |
| **No-OpenAI value** | enforced | **Violated in code** — `openai` still imported in ai-engine `llm_service.py`/`embedding_service.py` + document-processor, and in 3 requirements files |

### 🔴 Critical security incident
- **Live API keys committed to git**: `backups/backup_20251014_101721.zip` (on `origin/main`) contains a `.env` with **real Anthropic, OpenAI, and Google keys**.
- Loose plaintext keys at `C:\Users\sgbil\Claude_Desktop\Projects\In-My-Head\In My Head-API.txt`.
- Committed dev creds in `.env` (`SECRET_KEY`, `JWT_SECRET`) and `in-my-head-backup-20251005-124618/`.

---

## PART 2 — NEXT STEPS ACTION PLAN (dependency-ordered)

### ▶ PHASE 0 — SECURITY (do first; nothing else matters until this is done)
0.1 **Rotate/revoke all 3 leaked keys** at the provider consoles (Anthropic, OpenAI, Google AI Studio). _User action — can't be automated._
0.2 `git rm` the committed zip + `in-my-head-backup-20251005-124618/`; purge both from history (git-filter-repo/BFG); force-push.
0.3 Delete `In My Head-API.txt`. Confirm `.env` is gitignored and untracked; move secrets to `.env.local`.
0.4 Rotate committed `SECRET_KEY`/`JWT_SECRET`; replace `dev_password_123` / `minioadmin_CHANGE_ME` before any non-local use.

### ▶ PHASE 1 — FOUNDATION & REPRODUCIBILITY (unblocks everything downstream)
1.1 **Database = single source of truth.** Pick **Alembic** (already configured in document-processor). Implement the empty migration with all 15 tables incl. `users`; delete/relegate Prisma + ad-hoc SQL; call `init_db()`/`alembic upgrade head` on startup; then delete the `fix_*.py` / `check_*.py` patch scripts.
1.2 **Reconcile DB config**: one DSN everywhere (`5432/inmyhead`, user `inmyhead_user`). Fix the `5434/inmyhead_dev` mismatch in `conversation_service.py`.
1.3 **Fix the document-processor deployment**: Dockerfile `CMD` → `src.app:app` (not legacy `src.main`); **add `httpx` to requirements**; set its port to **8002** (currently collides with ai-engine at 8001).
1.4 **Add missing `asyncpg`** to ai-engine requirements; **purge `openai`** from code + all 3 requirements files (enforce the no-OpenAI value). Pin floating deps; document/trim `torch`/`transformers`.
1.5 **Lock port ownership** project-wide: ai-engine 8001, document-processor 8002, search 8003, resource-manager 8004, gateway 3000. Fix the swapped docker-compose, the `search-service PORT=8002` bug, and the `.env` gateway URLs.

### ▶ PHASE 2 — CLOSE THE CORRECTNESS GAPS (make claims true)
2.1 **Conversations (P0):** mount the real PostgreSQL router (`src/routes/conversations.py`), wire it to `conversation_service.py`, ship the migration + `users` table. Result: conversations persist **and** return real grounded LLM answers.
2.2 **Replace the `_retrieve_without_cache` TODO stub** in `cached_rag_service.py` (it returns empty context on the live path).
2.3 **Decide the scaffolds' fate** (recommend: collapse, don't fake breadth):
   - **api-gateway:** implement real proxying (`http-proxy-middleware`) with correct ports — OR drop it for v0.1.0 and have the frontend call ai-engine directly (already works).
   - **search-service:** implement by wrapping ai-engine's existing `/rag/retrieve` — OR remove from the architecture/README.
   - **resource-manager:** implement basic stats (doc/collection counts, storage) to back the Dashboard — OR remove.
2.4 **Make `/ready` honest** in all 4 services (actually probe deps, not hardcoded "connected").

### ▶ PHASE 3 — FRONTEND COMPLETION (usable v0.1.0)
3.1 **Dashboard:** real stats from backend (doc/collection counts, storage) — pairs with resource-manager (2.3) or a simple ai-engine stats endpoint.
3.2 **Collections:** real CRUD wired to backend, or cut from nav for v0.1.0.
3.3 **Scoped chat:** add a document/collection scope selector to Chat (cheap, high-value — "chat with this document").
3.4 Remove the dead `/login` 401-redirect (no auth pages exist) or add minimal auth.

### ▶ PHASE 4 — SHIP v0.1.0
4.1 **Repo hygiene:** archive 57 loose root `.md` reports into `docs/`; remove root debug/fix scripts + committed `venv/`; delete the empty `frontend/desktop-app/` Electron scaffold.
4.2 **GitHub:** rename `sgbilod/4` → `sgbilod/in-my-head`; fix README badge `[USERNAME]` placeholders; prune 90+ stale dependabot branches.
4.3 **One-command startup**: single script (infra + all services + frontend) replacing the 3 competing compose files.
4.4 **Fix `InMyHead.py`** launcher: open the real web UI (`:3001`) not Swagger; fix the 8001 ai-engine/doc-processor labeling; reconcile compose path.
4.5 **Tests:** add coverage for `routes_ingest`/parsers and the mounted conversations path; fix the non-loading api-gateway test; turn root integration `skip()` placeholders into real E2E.
4.6 **Tag v0.1.0.**

### Honest scoping recommendation for v0.1.0
Ship the thing that's real: **local-first document RAG with a clean web UI + persistent chat.** Either make the gateway/search/resource-manager real (Phase 2.3) or **cut them from the v0.1.0 story** so the README stops over-claiming. A focused, honest 1-service-core product that works beats "5 services" that mostly don't.

---

## PART 3 — INNOVATION ROADMAP

_Tiered by leverage. All chosen to run **fully local** (privacy is the moat). Effort: S=days, M=1-2wk, L=multi-week._

### ⚡ TIER 1 — Quick Wins (high leverage on existing stack)
| # | Innovation | Why | Effort |
|---|---|---|---|
| 1 | **Semantic answer cache over Qdrant** (GPTCache-style, key on query-embedding + retrieved-doc-id hash) | Turns repeat 30-120s RAG queries into **~50ms**; you already run Qdrant | S–M |
| 2 | **Streaming-first UX** (SSE token stream + show citations during TTFT) | Makes the app *feel* instant regardless of total latency | S |
| 3 | **Right-size the generator** → Qwen3 8–14B Q5/Q6 default, 70B on-demand | **4–8x faster**, ~same grounded-answer quality; Qwen also enables KV-cache reuse (Gemma doesn't) | S |
| 4 | **Contextual Retrieval** (Anthropic method, run with local Ollama) | **−35% to −67% retrieval failures**; slots into your existing chunk+BM25+rerank pipeline | S–M |
| 5 | **Parent-document retrieval** (embed child chunks, return parent section) | Near-free precision win via a `parent_id` Qdrant payload | S |
| 6 | ✅ **"Related Documents"** — SHIPPED 2026-07-01 (branch `feat/related-documents`). `GET /documents/{id}/related` (centroid of a doc's chunk vectors → nearest chunks across corpus → aggregate by doc, exclude self; pure vector similarity, no LLM); frontend sparkle toggle on each Documents row shows related docs + % match. Verified in-browser (volcanoes.pdf → Black Holes 19%, Photosynthesis 16%). Fast — sidesteps the CPU-inference latency wall. _Future: add the 1-Ollama-call "why related" rationale._ | S |
| 7 | **Retrieval metrics + RAGAS gold set** (Hit@k/MRR, local Ollama judge) | Measurement *first* so every change below is provable; CI regression gate | S–M |
| 8 | **Official Qdrant MCP server** (local path) | Expose your brain as a tool to Claude Code/Cursor/any MCP client — interoperability, fully local | S |

### 🚀 TIER 2 — Flagship Bets (define the product identity)
| # | Innovation | Why | Effort |
|---|---|---|---|
| 9 | **Upgrade embeddings** → EmbeddingGemma-300M or nomic-embed-text-v1.5 (Matryoshka) | all-MiniLM is the weakest link; big quality jump, keep storage flat via Matryoshka truncation | M |
| 10 | **"Knowledge Radio" — local Audio Overviews** (Ollama script + Kokoro/Piper TTS) | NotebookLM's #1 viral feature, but **fully private** — a marketing magnet nobody offers on-device | M |
| 11 | **Auto-knowledge-graph** (LightRAG / nano-graphrag on Ollama) | The AI-generated Obsidian graph + multi-hop "how does X relate to Y" retrieval | M |
| 12 | **Smart Inbox + auto-tagging/auto-collections** (Ollama classify on ingest) | Most-requested AI-PKM behavior; free/unmetered locally | S–M |
| 13 | **Multimodal capture** — voice notes (whisper.cpp), web clipper, screenshot OCR | Private voice transcription is a story cloud apps can't match | L (suite) |
| 14 | **Writing assistant grounded in YOUR notes** (existing RAG+citations in an editor) | NotebookLM's value prop, offline, every claim cited from your sources | M |
| 15 | **JSON-Schema/GBNF constrained output** for KG/entity extraction | Guarantees valid structured output from small local models | S |
| 16 | **KV/prefix prompt-cache + speculative decoding** (llama-server slots, draft model) | Up to **93% TTFT cut** on the fixed RAG prefix + ~2x decode on the 70B tier | M |

### 🌙 TIER 3 — Moonshots (category-defining — the "thinking second brain")
| # | Innovation | Why | Effort |
|---|---|---|---|
| 17 | **"Dreaming" = sleep-time compute** (Letta pattern + LightMem offline consolidation) | **The literal implementation of your sub-linear/dreaming vision.** Nightly idle-GPU pass: summarize, link, dedup, pre-answer. **32–177x token efficiency** makes full-corpus nightly passes free | M |
| 18 | **A-MEM Zettelkasten agentic memory** (self-linking, self-evolving notes) | Best architectural fit — a PKM *is* a Zettelkasten; notes that auto-tag, auto-link, and revise themselves | M |
| 19 | **Hierarchical summary tree (TiMem)** for genuine **sub-linear** retrieval | note → topic → domain → root; queries hit the right subtree, scales to 1M notes | M–L |
| 20 | **Ambient Proactive Agent** (scheduled `/dream` job → morning digest, resurfacing, draft suggestions) | "A second brain that thinks while you sleep" — creepy in the cloud, magical on-device. **The moat.** | L |
| 21 | **Graphiti temporal KG** → contradiction & belief-over-time detection | "Your March note says X; Tuesday's says not-X" — a genuinely novel PKM feature | M–L |
| 22 | **SSGM memory governance** | Safety rail once notes self-modify — prevents the brain corrupting itself | M |

### 🏆 Headline recommendation
**Lead the marketing with "Knowledge Radio" (private Audio Overviews) as the viral hook; build toward the Ambient Proactive "dreaming" Agent as the durable moat.** The entire industry is converging on "an agent that proactively works your knowledge base" — and that feature is *only trustworthy when it physically cannot phone home.* Local-first isn't a constraint here; it's the one thing Notion/NotebookLM/Mem structurally cannot copy.

**Suggested innovation sequence:** Tier-1 #7 (metrics) → #4 (contextual retrieval) → #1 (semantic cache) + #3 (Qwen default) + #2 (streaming) for a fast, measurably-better RAG → #9 (embeddings) → then pick a flagship (#10 Knowledge Radio or #11 knowledge-graph) → then the moonshot dreaming loop (#17/#18/#20).

---

## APPENDIX — Source audits
9 parallel agents produced: backend-completeness, frontend/desktop/infra/secrets, test-coverage, config/CI, data-model/schema, dependency-health (audits); RAG/knowledge-graph, local-inference, PKM-product, agentic-memory (innovation). Full findings summarized above; key citations include Anthropic Contextual Retrieval, LightRAG/nano-graphrag, EmbeddingGemma, GPTCache, Letta sleep-time-compute (arXiv 2504.13171), LightMem (2510.18866), TiMem (2601.02845), A-MEM (2502.12110), official Qdrant MCP.
