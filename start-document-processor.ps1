#!/usr/bin/env pwsh
# Start Document Processor Service

Write-Host "📄 Starting Document Processor Service..." -ForegroundColor Cyan

# Change to Document Processor directory
Set-Location "c:\Users\sgbil\In My Head\services\document-processor"

# Add the service directory to PYTHONPATH
$env:PYTHONPATH = "c:\Users\sgbil\In My Head\services\document-processor"

# Load environment variables from .env file
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

# Start the service
Write-Host "Starting uvicorn on port 8000..." -ForegroundColor Green
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
