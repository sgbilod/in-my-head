#!/usr/bin/env pwsh
# Start Resource Manager Service

Write-Host "⚙️ Starting Resource Manager Service..." -ForegroundColor Cyan

# Change to Resource Manager directory
Set-Location "c:\Users\sgbil\In My Head\services\resource-manager"

# Add the service directory to PYTHONPATH
$env:PYTHONPATH = "c:\Users\sgbil\In My Head\services\resource-manager"

# Load environment variables from .env file (if exists)
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

# Start the service
Write-Host "Starting uvicorn on port 8003..." -ForegroundColor Green
python -m uvicorn src.main:app --host 0.0.0.0 --port 8003
