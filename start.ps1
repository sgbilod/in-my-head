<#
.SYNOPSIS
    One-command startup for the In My Head v0.1.0 stack.

.DESCRIPTION
    Brings up the whole local-first system in dependency order:
      1. Docker infrastructure (PostgreSQL, Redis, Qdrant, MinIO)
      2. Ollama (local LLM + embeddings) — started if installed and not running
      3. ai-engine            (FastAPI)  -> http://localhost:8001
      4. document-processor   (FastAPI)  -> http://localhost:8002
      5. web frontend         (Vite)     -> http://localhost:3001

    Each backend service and the frontend launch in their own window so you can
    watch logs. Supersedes the fragmented start-*.ps1 scripts.

.NOTES
    Ports are fixed: ai-engine 8001, document-processor 8002, frontend 3001.
    Run from the repo root:  ./start.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$DatabaseUrl = "postgresql://inmyhead_user:dev_password_123@localhost:5432/inmyhead"
$AiEngineUrl = "http://127.0.0.1:8001"

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

# 1. Infrastructure -----------------------------------------------------------
Write-Step "Starting Docker infrastructure (Postgres, Redis, Qdrant, MinIO)..."
docker compose -f "$root/docker-compose.infrastructure.yml" up -d | Out-Null

Write-Step "Waiting for PostgreSQL to be healthy..."
$deadline = (Get-Date).AddSeconds(60)
do {
    Start-Sleep -Seconds 2
    $health = (docker inspect --format '{{.State.Health.Status}}' inmyhead-postgres 2>$null)
} until ($health -eq "healthy" -or (Get-Date) -gt $deadline)
if ($health -ne "healthy") { Write-Host "WARNING: Postgres not healthy yet; continuing." -ForegroundColor Yellow }

# 2. Ollama -------------------------------------------------------------------
Write-Step "Checking Ollama (local LLM)..."
$ollamaUp = $false
try { Invoke-RestMethod "http://localhost:11434/api/tags" -TimeoutSec 3 | Out-Null; $ollamaUp = $true } catch {}
if (-not $ollamaUp) {
    $ollamaApp = "$env:LOCALAPPDATA\Programs\Ollama\ollama app.exe"
    if (Test-Path $ollamaApp) {
        Write-Host "    Starting Ollama..." -ForegroundColor DarkGray
        Start-Process $ollamaApp -WindowStyle Hidden
    } else {
        Write-Host "    Ollama not found; RAG answers will fall back/degrade." -ForegroundColor Yellow
    }
}

# 3. ai-engine ----------------------------------------------------------------
Write-Step "Starting ai-engine on :8001..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root/services/ai-engine'; `$env:PYTHONPATH='.'; `$env:DATABASE_URL='$DatabaseUrl'; " +
    "python -m uvicorn src.main:app --port 8001"
)

# 4. document-processor -------------------------------------------------------
Write-Step "Starting document-processor on :8002..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root/services/document-processor'; `$env:PYTHONPATH='.'; `$env:AI_ENGINE_URL='$AiEngineUrl'; " +
    "python -m uvicorn src.app:app --port 8002"
)

# 5. Frontend -----------------------------------------------------------------
Write-Step "Starting web frontend on :3001..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root/frontend/web-interface'; npm run dev"
)

Write-Host ""
Write-Step "In My Head is starting. Give the backends ~20s to load models, then open:"
Write-Host "    Web app:        http://localhost:3001" -ForegroundColor Green
Write-Host "    ai-engine API:  http://localhost:8001/docs" -ForegroundColor Green
Write-Host "    doc-processor:  http://localhost:8002/docs" -ForegroundColor Green
