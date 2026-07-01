# In My Head — MCP Server

Exposes your local knowledge base to any **MCP client** (Claude Code, Cursor,
Claude Desktop, …) as tools, so those AIs can search *your* documents. It's a
thin stdio bridge over the ai-engine HTTP API — **everything stays on your
machine; nothing leaves it.**

## Tools
| Tool | What it does |
|---|---|
| `search_knowledge(query)` | Grounded answer + cited sources (asks your brain) |
| `search_documents(query, top_k)` | Raw relevant passages, no answer generation |
| `list_documents()` | Everything in your knowledge base |
| `related_documents(document_id)` | Semantically related documents |

## Setup
1. Start the In My Head stack so the ai-engine is running (`./start.ps1`, ai-engine on :8001).
2. Install deps: `pip install -r requirements.txt`
3. Register the server with your MCP client:

**Claude Code (CLI):**
```bash
claude mcp add in-my-head -- python "C:/Users/sgbil/In My Head/services/mcp-server/inmyhead_mcp.py"
```

**Cursor / Claude Desktop (JSON config):**
```json
{
  "mcpServers": {
    "in-my-head": {
      "command": "python",
      "args": ["C:/Users/sgbil/In My Head/services/mcp-server/inmyhead_mcp.py"],
      "env": { "AI_ENGINE_URL": "http://127.0.0.1:8001" }
    }
  }
}
```

Then ask the client things like *"search my knowledge base for what I saved about photosynthesis"* and it will call `search_knowledge`.

## Config
- `AI_ENGINE_URL` (default `http://127.0.0.1:8001`) — where the ai-engine is listening.

## Verify
With the ai-engine running:
```bash
python -c "import asyncio; from inmyhead_mcp import mcp; print(len(asyncio.run(mcp.list_tools())), 'tools')"
```
