#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start Celery workers for background job processing.

.DESCRIPTION
    This script starts Celery workers with optimized settings for
    document processing. It creates multiple workers for different
    task queues.

.PARAMETER Workers
    Number of worker processes (default: 4)

.PARAMETER Concurrency
    Number of concurrent tasks per worker (default: 4)

.PARAMETER LogLevel
    Celery log level (default: info)

.EXAMPLE
    .\start_celery_workers.ps1
    
.EXAMPLE
    .\start_celery_workers.ps1 -Workers 8 -Concurrency 8 -LogLevel debug
#>

param(
    [int]$Workers = 4,
    [int]$Concurrency = 4,
    [string]$LogLevel = "info"
)

Write-Host "=================================" -ForegroundColor Cyan
Write-Host " Starting Celery Workers" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Set Python path
$env:PYTHONPATH = "$PSScriptRoot\src"

# Change to document-processor directory
Set-Location $PSScriptRoot

# Start main worker (all queues)
Write-Host "Starting main worker..." -ForegroundColor Green
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "celery -A jobs.celery_app worker -Q document_processing,parsing,preprocessing,embeddings,metadata,storage -n main@%h -c $Concurrency -l $LogLevel"
)

Start-Sleep -Seconds 2

# Start specialized workers for heavy tasks
Write-Host "Starting embedding worker..." -ForegroundColor Green
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "celery -A jobs.celery_app worker -Q embeddings -n embeddings@%h -c 2 -l $LogLevel"
)

Start-Sleep -Seconds 2

Write-Host "Starting metadata worker..." -ForegroundColor Green
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "celery -A jobs.celery_app worker -Q metadata -n metadata@%h -c 2 -l $LogLevel"
)

Write-Host ""
Write-Host "=================================" -ForegroundColor Green
Write-Host " Celery Workers Started!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""
Write-Host "Workers: $Workers" -ForegroundColor Yellow
Write-Host "Concurrency: $Concurrency" -ForegroundColor Yellow
Write-Host "Log Level: $LogLevel" -ForegroundColor Yellow
Write-Host ""
Write-Host "To monitor workers, run:" -ForegroundColor Cyan
Write-Host "  celery -A jobs.celery_app inspect active" -ForegroundColor White
Write-Host ""
Write-Host "To start Flower dashboard, run:" -ForegroundColor Cyan
Write-Host "  celery -A jobs.celery_app flower" -ForegroundColor White
Write-Host "  Then visit: http://localhost:5555" -ForegroundColor White
Write-Host ""
