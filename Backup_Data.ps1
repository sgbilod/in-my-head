# In My Head - Data Backup Script
# =================================
# Backs up all critical Docker volumes and configuration

param(
  [string]$BackupPath = ".\backups",
  [switch]$IncludeAIModels = $false
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🔒 In My Head - Data Backup Utility              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Create backup directory
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $BackupPath "backup_$timestamp"

Write-Host "📁 Creating backup directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host "   ✅ Created: $backupDir" -ForegroundColor Green
Write-Host ""

# Check if Docker is running
Write-Host "🔍 Checking Docker status..." -ForegroundColor Yellow
try {
  docker ps | Out-Null
  Write-Host "   ✅ Docker is running" -ForegroundColor Green
}
catch {
  Write-Host "   ❌ Docker is not running!" -ForegroundColor Red
  Write-Host ""
  Write-Host "Please start Docker Desktop first." -ForegroundColor Yellow
  Read-Host "Press Enter to exit"
  exit 1
}
Write-Host ""

# Volumes to backup
$criticalVolumes = @(
  @{Name = "inmyhead_postgres_data"; Description = "PostgreSQL Database" },
  @{Name = "inmyhead_qdrant_data"; Description = "Vector Embeddings" },
  @{Name = "inmyhead_minio_data"; Description = "Document Files" },
  @{Name = "inmyhead_redis_data"; Description = "Cache Data" }
)

if ($IncludeAIModels) {
  $criticalVolumes += @{Name = "inmyhead_ai_models"; Description = "AI Models" }
}

# Backup each volume
Write-Host "💾 Backing up Docker volumes..." -ForegroundColor Cyan
Write-Host ""

$totalVolumes = $criticalVolumes.Count
$current = 0

foreach ($vol in $criticalVolumes) {
  $current++
  $volumeName = $vol.Name
  $description = $vol.Description

  Write-Host "[$current/$totalVolumes] Backing up: $description" -ForegroundColor Yellow
  Write-Host "           Volume: $volumeName" -ForegroundColor Gray

  # Check if volume exists
  $volumeExists = docker volume ls --format "{{.Name}}" | Select-String -Pattern "^$volumeName$" -Quiet

  if (-not $volumeExists) {
    Write-Host "           ⚠️  Volume not found (skipping)" -ForegroundColor Yellow
    Write-Host ""
    continue
  }

  # Backup volume using tar
  $backupFile = Join-Path $backupDir "$volumeName.tar.gz"

  try {
    docker run --rm `
      -v "${volumeName}:/data" `
      -v "${backupDir}:/backup" `
      alpine `
      tar czf "/backup/$volumeName.tar.gz" -C /data . 2>&1 | Out-Null

    if (Test-Path $backupFile) {
      $fileSize = (Get-Item $backupFile).Length / 1MB
      Write-Host "           ✅ Backed up ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
    }
    else {
      Write-Host "           ❌ Backup failed" -ForegroundColor Red
    }
  }
  catch {
    Write-Host "           ❌ Error: $_" -ForegroundColor Red
  }

  Write-Host ""
}

# Backup configuration files (EXCLUDING SENSITIVE DATA)
Write-Host "📄 Backing up configuration files..." -ForegroundColor Cyan
Write-Host "   🔒 Security: Skipping .env files (contains API keys)" -ForegroundColor Yellow

# Safe files to backup (NO SECRETS!)
$configFiles = @(
  @{Path = "infrastructure\docker\docker-compose.dev.yml"; Safe = $true }
)

# Files to SKIP (contain secrets)
$excludedFiles = @(
  "infrastructure\docker\.env",
  ".env",
  "config.json",  # May contain sensitive paths
  "*.key",
  "*.pem",
  "credentials.json",
  "secrets.json"
)

Write-Host "   ⚠️  Excluded files (contain secrets):" -ForegroundColor Red
foreach ($excluded in $excludedFiles) {
  Write-Host "      ❌ $excluded" -ForegroundColor DarkGray
}
Write-Host ""

foreach ($configFile in $configFiles) {
  if ($configFile.Safe -and (Test-Path $configFile.Path)) {
    $fileName = Split-Path $configFile.Path -Leaf
    Copy-Item $configFile.Path -Destination (Join-Path $backupDir $fileName)
    Write-Host "   ✅ $fileName (safe)" -ForegroundColor Green
  }
  elseif (-not (Test-Path $configFile.Path)) {
    Write-Host "   ⚠️  $($configFile.Path) not found" -ForegroundColor Yellow
  }
}

Write-Host ""

# Create .env template for restoration
$envTemplate = @"
# ⚠️  IMPORTANT: This is a template file
# ========================================
# The actual .env file was NOT backed up for security reasons.
# It contains sensitive API keys and credentials.
#
# To restore this backup, you need to:
# 1. Copy your original .env file, OR
# 2. Create a new .env with your API keys
#
# Required environment variables:
# - OPENAI_API_KEY=sk-...
# - ANTHROPIC_API_KEY=sk-ant-...
# - POSTGRES_PASSWORD=...
# - Other service credentials
#
# See infrastructure/docker/.env.example for reference
"@

$envTemplate | Out-File -FilePath (Join-Path $backupDir ".env.TEMPLATE") -Encoding UTF8
Write-Host "   📝 Created .env.TEMPLATE (restoration guide)" -ForegroundColor Cyan

Write-Host ""

# Create backup manifest
$manifest = @{
  timestamp       = $timestamp
  date            = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  volumes         = $criticalVolumes | ForEach-Object { $_.Name }
  backup_location = $backupDir
  machine         = $env:COMPUTERNAME
  user            = $env:USERNAME
}

$manifest | ConvertTo-Json | Out-File -FilePath (Join-Path $backupDir "manifest.json") -Encoding UTF8

# Create README
$readme = @"
# In My Head Backup
Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Machine: $env:COMPUTERNAME
User: $env:USERNAME

## ⚠️  SECURITY NOTICE

For your protection, this backup does NOT include:
- .env files (contain API keys and passwords)
- credentials.json or secrets.json
- Private keys or certificates

You will need your original .env file to restore this backup!
See .env.TEMPLATE in this folder for required variables.

## Contents

This backup contains the following volumes:
- PostgreSQL Database (document metadata)
- Vector Embeddings (search data)
- Document Files (uploaded files)
- Cache Data (temporary data)

## How to Restore

1. Stop In My Head services:
   docker-compose down

2. Restore each volume:
   docker run --rm -v <volume-name>:/data -v <backup-path>:/backup alpine sh -c "cd /data && tar xzf /backup/<volume-name>.tar.gz"

3. ⚠️  IMPORTANT: Restore your .env file:
   Copy your original .env to infrastructure/docker/.env

4. Restart services:
   docker-compose up -d

## Notes

- Keep this backup in a safe location
- Test restores periodically
- Update backups regularly
"@

$readme | Out-File -FilePath (Join-Path $backupDir "README.txt") -Encoding UTF8

Write-Host "✅ Backup manifest created" -ForegroundColor Green
Write-Host ""

# Calculate total backup size
$totalSize = (Get-ChildItem $backupDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB

# Summary
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║           Backup Complete!                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "   Location: $backupDir" -ForegroundColor White
Write-Host "   Total Size: $([math]::Round($totalSize, 2)) MB" -ForegroundColor White
Write-Host "   Volumes Backed Up: $($criticalVolumes.Count)" -ForegroundColor White
Write-Host ""

# Offer to create archive
$createZip = Read-Host "Create ZIP archive? (y/n)"
if ($createZip -eq "y" -or $createZip -eq "Y") {
  Write-Host ""
  Write-Host "📦 Creating ZIP archive..." -ForegroundColor Yellow

  $zipPath = "$backupDir.zip"

  try {
    Compress-Archive -Path $backupDir -DestinationPath $zipPath -Force
    $zipSize = (Get-Item $zipPath).Length / 1MB

    Write-Host "   ✅ Archive created!" -ForegroundColor Green
    Write-Host "   Location: $zipPath" -ForegroundColor Cyan
    Write-Host "   Size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor White

    # Ask to delete uncompressed backup
    Write-Host ""
    $deleteDir = Read-Host "Delete uncompressed backup folder? (y/n)"
    if ($deleteDir -eq "y" -or $deleteDir -eq "Y") {
      Remove-Item -Path $backupDir -Recurse -Force
      Write-Host "   ✅ Uncompressed backup deleted" -ForegroundColor Green
    }
  }
  catch {
    Write-Host "   ❌ Failed to create ZIP: $_" -ForegroundColor Red
  }
}

Write-Host ""
Write-Host "🎉 Backup completed successfully!" -ForegroundColor Magenta
Write-Host ""
Write-Host "� SECURITY REMINDER:" -ForegroundColor Red -BackgroundColor Yellow
Write-Host "   ⚠️  .env file NOT included (contains API keys)" -ForegroundColor Yellow
Write-Host "   ⚠️  Keep your .env file separate and secure!" -ForegroundColor Yellow
Write-Host "   ⚠️  NEVER upload backups to GitHub or public places!" -ForegroundColor Yellow
Write-Host ""
Write-Host "�� Recommendations:" -ForegroundColor Cyan
Write-Host "   1. Copy backup to external drive (not cloud!)" -ForegroundColor White
Write-Host "   2. Store securely (offline storage preferred)" -ForegroundColor White
Write-Host "   3. Keep .env file in a password manager" -ForegroundColor White
Write-Host "   4. Test restore periodically" -ForegroundColor White
Write-Host "   5. Schedule regular backups (weekly recommended)" -ForegroundColor White
Write-Host ""
Write-Host "🚫 DO NOT:" -ForegroundColor Red
Write-Host "   ❌ Upload to GitHub" -ForegroundColor Red
Write-Host "   ❌ Share via email or cloud storage" -ForegroundColor Red
Write-Host "   ❌ Post in public forums" -ForegroundColor Red
Write-Host ""

Read-Host "Press Enter to exit"
