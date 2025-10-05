# Start All Services - In My Head Project

Write-Host "Starting In My Head services..." -ForegroundColor Cyan

# Start Docker containers
Push-Location infrastructure\docker
docker-compose up -d
Pop-Location

# Wait for services to be ready
Start-Sleep -Seconds 5

Write-Host "All services started!" -ForegroundColor Green
Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor Cyan
Write-Host "  - Redis: localhost:6379" -ForegroundColor Cyan
Write-Host "  - Qdrant: localhost:6333" -ForegroundColor Cyan
Write-Host "  - MinIO: localhost:9000" -ForegroundColor Cyan
