#!/usr/bin/env pwsh
# Start AI Engine Service

Write-Host "🚀 Starting AI Engine Service..." -ForegroundColor Cyan

# Change to AI Engine directory
Set-Location "c:\Users\sgbil\In My Head\services\ai-engine"

# Add the service directory to PYTHONPATH
$env:PYTHONPATH = "c:\Users\sgbil\In My Head\services\ai-engine"

# Load environment variables from .env file
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

# Start the service
Write-Host "Starting uvicorn on port 8001..." -ForegroundColor Green
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
