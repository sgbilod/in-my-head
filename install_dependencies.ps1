# Install Dependencies for All Services
# Optimized installation strategy with error handling

param(
  [string]$Service = "all",
  [switch]$SkipErrors = $false
)

# Ensure SSL fix is applied
$env:CURL_CA_BUNDLE = ""
$env:SSL_CERT_FILE = python -c "import certifi; print(certifi.where())" 2>$null
$env:REQUESTS_CA_BUNDLE = $env:SSL_CERT_FILE

Write-Host "`n=== INSTALLING SERVICE DEPENDENCIES ===" -ForegroundColor Cyan
Write-Host "Service: $Service" -ForegroundColor Gray
Write-Host "SSL Certificate Bundle: $env:SSL_CERT_FILE" -ForegroundColor Gray

$services = @{
  "document-processor" = "services/document-processor/requirements.txt"
  "ai-engine"          = "services/ai-engine/requirements.txt"
  "search-service"     = "services/search-service/requirements.txt"
  "api-gateway"        = "services/api-gateway/requirements.txt"
  "resource-manager"   = "services/resource-manager/requirements.txt"
}

function Install-ServiceDependencies {
  param($ServiceName, $RequirementsFile)

  Write-Host "`n📦 Installing $ServiceName dependencies..." -ForegroundColor Cyan

  if (-not (Test-Path $RequirementsFile)) {
    Write-Host "   ❌ Requirements file not found: $RequirementsFile" -ForegroundColor Red
    return $false
  }

  Write-Host "   Reading requirements from: $RequirementsFile" -ForegroundColor Gray

  # Install with progress
  $startTime = Get-Date
  pip install -r $RequirementsFile 2>&1 | Tee-Object -Variable output | Out-Null
  $endTime = Get-Date
  $duration = ($endTime - $startTime).TotalSeconds

  if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ $ServiceName dependencies installed successfully!" -ForegroundColor Green
    Write-Host "   ⏱️  Time: $([math]::Round($duration, 1)) seconds" -ForegroundColor Gray
    return $true
  }
  else {
    Write-Host "   ❌ Installation failed for $ServiceName" -ForegroundColor Red
    Write-Host "   Errors:" -ForegroundColor Yellow
    $output | Select-Object -Last 10 | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }

    if (-not $SkipErrors) {
      Write-Host "`n   Stopping installation. Use -SkipErrors to continue." -ForegroundColor Yellow
      return $false
    }
    return $false
  }
}

# Install services
$installed = @()
$failed = @()

if ($Service -eq "all") {
  Write-Host "`nInstalling ALL services..." -ForegroundColor Yellow

  foreach ($svc in $services.Keys) {
    $result = Install-ServiceDependencies -ServiceName $svc -RequirementsFile $services[$svc]
    if ($result) {
      $installed += $svc
    }
    else {
      $failed += $svc
      if (-not $SkipErrors) {
        break
      }
    }
  }
}
else {
  if ($services.ContainsKey($Service)) {
    $result = Install-ServiceDependencies -ServiceName $Service -RequirementsFile $services[$Service]
    if ($result) {
      $installed += $Service
    }
    else {
      $failed += $Service
    }
  }
  else {
    Write-Host "❌ Unknown service: $Service" -ForegroundColor Red
    Write-Host "Available services: $($services.Keys -join ', ')" -ForegroundColor Gray
    exit 1
  }
}

# Summary
Write-Host "`n" -NoNewline
Write-Host "="*70 -ForegroundColor Cyan
Write-Host "INSTALLATION SUMMARY" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan

if ($installed.Count -gt 0) {
  Write-Host "`n✅ Successfully installed ($($installed.Count)):" -ForegroundColor Green
  $installed | ForEach-Object { Write-Host "   - $_" -ForegroundColor Green }
}

if ($failed.Count -gt 0) {
  Write-Host "`n❌ Failed installations ($($failed.Count)):" -ForegroundColor Red
  $failed | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
}

Write-Host "`n" -NoNewline
Write-Host "="*70 -ForegroundColor Cyan

if ($failed.Count -eq 0) {
  Write-Host "🎉 All dependencies installed successfully!" -ForegroundColor Green
  exit 0
}
else {
  Write-Host "⚠️  Some installations failed. Check errors above." -ForegroundColor Yellow
  exit 1
}
