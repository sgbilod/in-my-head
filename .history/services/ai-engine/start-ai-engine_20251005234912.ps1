#!/usr/bin/env pwsh
# PowerShell script to start the AI Engine service locally

Write-Host "🚀 Starting AI Engine Service..." -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:DATABASE_URL = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
$env:QDRANT_URL = "http://localhost:6333"
$env:SERVICE_PORT = "8002"
$env:LOG_LEVEL = "DEBUG"

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "   Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    
    Write-Host "   Activating virtual environment..." -ForegroundColor Yellow
    .\venv\Scripts\Activate.ps1
    
    Write-Host "   Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "✓ Activating virtual environment..." -ForegroundColor Green
    .\venv\Scripts\Activate.ps1
}

# Check if Qdrant is running
Write-Host "🔍 Checking Qdrant connection..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:6333/health" -Method Get -TimeoutSec 2
    Write-Host "✓ Qdrant is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Qdrant not accessible at http://localhost:6333" -ForegroundColor Yellow
    Write-Host "   Make sure Qdrant is running (docker-compose up qdrant)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Engine Service" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "URL:      http://localhost:8002" -ForegroundColor White
Write-Host "Docs:     http://localhost:8002/docs" -ForegroundColor White
Write-Host "Health:   http://localhost:8002/health" -ForegroundColor White
Write-Host "Qdrant:   http://localhost:6333" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start the service
Write-Host "🚀 Starting server on port 8002..." -ForegroundColor Cyan
Write-Host ""

python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8002
