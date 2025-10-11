#!/usr/bin/env pwsh
# Start Search Service

Write-Host "🔍 Starting Search Service..." -ForegroundColor Cyan

# Change to Search Service directory
Set-Location "c:\Users\sgbil\In My Head\services\search-service"

# Add the service directory to PYTHONPATH
$env:PYTHONPATH = "c:\Users\sgbil\In My Head\services\search-service"

# Load environment variables from .ENV file
if (Test-Path ".ENV") {
    Get-Content ".ENV" | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

# Start the service
Write-Host "Starting uvicorn on port 8002..." -ForegroundColor Green
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002
