#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start Flower monitoring dashboard for Celery.

.DESCRIPTION
    This script starts the Flower web dashboard for monitoring
    Celery workers and tasks in real-time.

.PARAMETER Port
    Port to run Flower on (default: 5555)

.EXAMPLE
    .\start_flower.ps1
    
.EXAMPLE
    .\start_flower.ps1 -Port 8080
#>

param(
    [int]$Port = 5555
)

Write-Host "=================================" -ForegroundColor Cyan
Write-Host " Starting Flower Dashboard" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Set Python path
$env:PYTHONPATH = "$PSScriptRoot\src"

# Change to document-processor directory
Set-Location $PSScriptRoot

# Start Flower
Write-Host "Starting Flower on port $Port..." -ForegroundColor Green
Write-Host ""

celery -A jobs.celery_app flower --port=$Port

Write-Host ""
Write-Host "Flower dashboard: http://localhost:$Port" -ForegroundColor Cyan
Write-Host ""
