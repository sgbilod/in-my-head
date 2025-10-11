# PowerShell script to start the Document Processing API server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Document Processing API Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check if Redis is running
$redisRunning = Test-NetConnection localhost -Port 6379 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $redisRunning) {
    Write-Host "❌ Redis is not running on localhost:6379" -ForegroundColor Red
    Write-Host "   Please start Redis first" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Redis is running" -ForegroundColor Green

# Check if Qdrant is running
$qdrantRunning = Test-NetConnection localhost -Port 6333 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $qdrantRunning) {
    Write-Host "⚠️  Qdrant is not running on localhost:6333" -ForegroundColor Yellow
    Write-Host "   Vector search will not work" -ForegroundColor Yellow
}
else {
    Write-Host "✅ Qdrant is running" -ForegroundColor Green
}

# Check if Celery workers are running
Write-Host "ℹ️  Make sure Celery workers are running" -ForegroundColor Yellow
Write-Host "   Run: .\start_celery_workers.ps1" -ForegroundColor Yellow
Write-Host ""

# Set environment variables
$env:PYTHONPATH = "c:\Users\sgbil\In My Head\services\document-processor"
$env:API_KEYS = "test-api-key-123"  # Default API key for testing
$env:RATE_LIMIT_REQUESTS = "100"     # Requests per window
$env:RATE_LIMIT_WINDOW = "60"        # Window in seconds
$env:CORS_ORIGINS = "*"              # Allow all origins (change in production)
$env:PORT = "8000"                   # Server port

Write-Host "Starting API server..." -ForegroundColor Cyan
Write-Host "  Port: $env:PORT" -ForegroundColor Gray
Write-Host "  API Key: $env:API_KEYS" -ForegroundColor Gray
Write-Host "  Rate Limit: $env:RATE_LIMIT_REQUESTS requests / $env:RATE_LIMIT_WINDOW seconds" -ForegroundColor Gray
Write-Host ""

# Navigate to document-processor directory
cd "c:\Users\sgbil\In My Head\services\document-processor"

# Start server with uvicorn
Write-Host "🚀 Starting server at http://localhost:$env:PORT" -ForegroundColor Green
Write-Host "📖 API Documentation: http://localhost:$env:PORT/docs" -ForegroundColor Green
Write-Host "🏥 Health Check: http://localhost:$env:PORT/health" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn src.app:app --host 0.0.0.0 --port $env:PORT --reload --log-level info
