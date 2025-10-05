# Stop All Services - In My Head Project

Write-Host "Stopping In My Head services..." -ForegroundColor Yellow

Push-Location infrastructure\docker
docker-compose down
Pop-Location

Write-Host "All services stopped!" -ForegroundColor Green
