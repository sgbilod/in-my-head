#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the Document Processor FastAPI service
.DESCRIPTION
    Launches the document processor service with proper environment configuration
#>

$ErrorActionPreference = "Stop"

Write-Host "`n🚀 Starting Document Processor Service..." -ForegroundColor Cyan

# Set working directory
$ServiceDir = Join-Path $PSScriptRoot "..\services\document-processor"
Set-Location $ServiceDir

# Set environment variables
$env:DATABASE_URL = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
$env:PYTHONPATH = $ServiceDir

Write-Host "✅ Working directory: $ServiceDir" -ForegroundColor Green
Write-Host "✅ Database: localhost:5434/inmyhead_dev" -ForegroundColor Green
Write-Host "`n📡 Starting FastAPI server on http://localhost:8001..." -ForegroundColor Yellow
Write-Host "📖 API docs available at: http://localhost:8001/docs" -ForegroundColor Yellow
Write-Host "📊 Metrics available at: http://localhost:8001/metrics" -ForegroundColor Yellow
Write-Host "`n⚠️  Press CTRL+C to stop the server`n" -ForegroundColor Magenta

# Start uvicorn
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
