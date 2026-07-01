"""
In My Head — MCP server.

Exposes the user's local knowledge base to any MCP client (Claude Code, Cursor,
Claude Desktop, …) as tools. It's a thin, stdio bridge over the ai-engine HTTP
API (default http://127.0.0.1:8001) — everything stays local; nothing leaves the
machine. Start the In My Head stack (start.ps1) first so the ai-engine is up.

Tools:
  - search_knowledge(query)          → grounded answer + sources (asks the brain)
  - search_documents(query, top_k)   → raw relevant passages (no LLM generation)
  - list_documents()                 → what's in the knowledge base
  - related_documents(document_id)   → semantically related documents

Run:  python inmyhead_mcp.py     (stdio transport, for an MCP client to launch)
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://127.0.0.1:8001")

mcp = FastMCP("In My Head")


async def _get(path: str, params: dict | None = None):
    async with httpx.AsyncClient(timeout=180.0) as c:
        r = await c.get(f"{AI_ENGINE_URL}{path}", params=params or {})
        r.raise_for_status()
        return r.json()


async def _post(path: str, payload: dict):
    async with httpx.AsyncClient(timeout=180.0) as c:
        r = await c.post(f"{AI_ENGINE_URL}{path}", json=payload)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def search_knowledge(query: str) -> str:
    """Ask a question and get an answer grounded in the user's personal knowledge
    base, with the source documents cited. Use this to look up anything the user
    has saved (notes, documents, references)."""
    try:
        d = await _post(
            "/rag/query",
            {"query": query, "model": "llama3", "top_k": 5, "max_tokens": 400},
        )
    except Exception as e:
        return f"Could not reach the knowledge base ({AI_ENGINE_URL}): {e}"
    lines = [d.get("answer", "(no answer)")]
    cites = d.get("citations", [])
    if cites:
        lines.append("\nSources:")
        for c in cites:
            excerpt = (c.get("excerpt") or "")[:140]
            lines.append(f"  • {c.get('document_title', '?')} — {excerpt}")
    if d.get("cached"):
        lines.append("\n(served from semantic cache)")
    return "\n".join(lines)


@mcp.tool()
async def search_documents(query: str, top_k: int = 5) -> str:
    """Retrieve the most relevant passages from the knowledge base for a query,
    without generating an answer. Returns the raw matching chunks and their source
    documents — useful when you want the evidence yourself."""
    try:
        d = await _post(
            "/rag/retrieve",
            {"query": query, "top_k": top_k, "use_reranking": True},
        )
    except Exception as e:
        return f"Could not reach the knowledge base ({AI_ENGINE_URL}): {e}"
    chunks = d.get("chunks", [])
    if not chunks:
        return "No relevant passages found."
    out = []
    for i, ch in enumerate(chunks, 1):
        title = (ch.get("metadata") or {}).get("document_title", "?")
        out.append(f"{i}. [{title}] (score {ch.get('score', 0):.2f})\n   {ch.get('content', '')[:300]}")
    return "\n".join(out)


@mcp.tool()
async def list_documents() -> str:
    """List every document in the user's knowledge base, with chunk counts."""
    try:
        docs = await _get("/documents")
    except Exception as e:
        return f"Could not reach the knowledge base ({AI_ENGINE_URL}): {e}"
    if not docs:
        return "The knowledge base is empty."
    return "\n".join(
        f"  • {d.get('title', '?')} ({d.get('chunk_count', 0)} chunks) [id: {d.get('document_id')}]"
        for d in docs
    )


@mcp.tool()
async def related_documents(document_id: str) -> str:
    """Given a document id (from list_documents), find other documents in the
    knowledge base that are semantically related to it."""
    try:
        rel = await _get(f"/documents/{document_id}/related", {"limit": 5})
    except Exception as e:
        return f"Could not reach the knowledge base ({AI_ENGINE_URL}): {e}"
    if not rel:
        return "No related documents found."
    return "\n".join(
        f"  • {r.get('title', '?')} ({max(0, r.get('score', 0) * 100):.0f}% match)"
        for r in rel
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
