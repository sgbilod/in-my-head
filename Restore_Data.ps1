# In My Head - Data Restore Script
# ==================================
# Restores Docker volumes from backup

param(
    [string]$BackupPath = "",
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🔄 In My Head - Data Restore Utility             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
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

# Find available backups
if ($BackupPath -eq "") {
    Write-Host "📁 Scanning for backups..." -ForegroundColor Yellow

    $backupLocations = @(
        ".\backups",
        ".\backup",
        "$env:USERPROFILE\Downloads"
    )

    $availableBackups = @()

    foreach ($location in $backupLocations) {
        if (Test-Path $location) {
            # Find backup folders
            $folders = Get-ChildItem -Path $location -Directory -Filter "backup_*" -ErrorAction SilentlyContinue
            foreach ($folder in $folders) {
                $manifestPath = Join-Path $folder.FullName "manifest.json"
                if (Test-Path $manifestPath) {
                    $manifest = Get-Content $manifestPath | ConvertFrom-Json
                    $availableBackups += @{
                        Path = $folder.FullName
                        Name = $folder.Name
                        Date = $manifest.date
                        Size = [math]::Round((Get-ChildItem $folder.FullName -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
                    }
                }
            }

            # Find backup ZIPs
            $zips = Get-ChildItem -Path $location -File -Filter "backup_*.zip" -ErrorAction SilentlyContinue
            foreach ($zip in $zips) {
                $availableBackups += @{
                    Path  = $zip.FullName
                    Name  = $zip.Name
                    Date  = $zip.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
                    Size  = [math]::Round($zip.Length / 1MB, 2)
                    IsZip = $true
                }
            }
        }
    }

    if ($availableBackups.Count -eq 0) {
        Write-Host "   ❌ No backups found!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please run .\Backup_Data.ps1 first to create a backup." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }

    Write-Host "   ✅ Found $($availableBackups.Count) backup(s)" -ForegroundColor Green
    Write-Host ""

    # Display available backups
    Write-Host "📋 Available Backups:" -ForegroundColor Cyan
    Write-Host ""

    for ($i = 0; $i -lt $availableBackups.Count; $i++) {
        $backup = $availableBackups[$i]
        $isZip = $backup.ContainsKey("IsZip") -and $backup.IsZip
        $type = if ($isZip) { "📦 ZIP" } else { "📁 Folder" }

        Write-Host "  [$($i + 1)] $type" -ForegroundColor Yellow
        Write-Host "      Name: $($backup.Name)" -ForegroundColor White
        Write-Host "      Date: $($backup.Date)" -ForegroundColor Gray
        Write-Host "      Size: $($backup.Size) MB" -ForegroundColor Gray
        Write-Host "      Path: $($backup.Path)" -ForegroundColor DarkGray
        Write-Host ""
    }

    # Let user choose backup
    $selection = Read-Host "Select backup to restore (1-$($availableBackups.Count)) or 'q' to quit"

    if ($selection -eq 'q' -or $selection -eq 'Q') {
        Write-Host "Restore cancelled." -ForegroundColor Yellow
        exit 0
    }

    try {
        $index = [int]$selection - 1
        if ($index -lt 0 -or $index -ge $availableBackups.Count) {
            throw "Invalid selection"
        }
        $selectedBackup = $availableBackups[$index]
        $BackupPath = $selectedBackup.Path
    }
    catch {
        Write-Host "   ❌ Invalid selection!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Validate backup path
if (-not (Test-Path $BackupPath)) {
    Write-Host "   ❌ Backup not found: $BackupPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "🎯 Selected backup: $BackupPath" -ForegroundColor Cyan
Write-Host ""

# If ZIP file, extract it first
$isZipFile = $BackupPath -like "*.zip"
$workingDir = $BackupPath

if ($isZipFile) {
    Write-Host "📦 Extracting ZIP archive..." -ForegroundColor Yellow

    $extractPath = Join-Path $env:TEMP "inmyhead_restore_$(Get-Date -Format 'yyyyMMddHHmmss')"

    try {
        Expand-Archive -Path $BackupPath -DestinationPath $extractPath -Force

        # Find the backup folder inside
        $extractedFolders = Get-ChildItem -Path $extractPath -Directory
        if ($extractedFolders.Count -eq 1) {
            $workingDir = $extractedFolders[0].FullName
        }
        else {
            $workingDir = $extractPath
        }

        Write-Host "   ✅ Extracted to: $workingDir" -ForegroundColor Green
    }
    catch {
        Write-Host "   ❌ Failed to extract: $_" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host ""
}

# Read manifest
$manifestPath = Join-Path $workingDir "manifest.json"
if (Test-Path $manifestPath) {
    $manifest = Get-Content $manifestPath | ConvertFrom-Json
    Write-Host "📄 Backup Information:" -ForegroundColor Cyan
    Write-Host "   Created: $($manifest.date)" -ForegroundColor White
    Write-Host "   Machine: $($manifest.machine)" -ForegroundColor White
    Write-Host "   User: $($manifest.user)" -ForegroundColor White
    Write-Host ""
}

# Warning
if (-not $Force) {
    Write-Host "⚠️  WARNING: DATA LOSS RISK!" -ForegroundColor Red -BackgroundColor Yellow
    Write-Host ""
    Write-Host "This will REPLACE ALL current data with the backup." -ForegroundColor Yellow
    Write-Host "Any documents uploaded after the backup will be LOST!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Recommendation: Create a backup of current data first:" -ForegroundColor Cyan
    Write-Host "   .\Backup_Data.ps1" -ForegroundColor White
    Write-Host ""

    $confirm = Read-Host "Type 'RESTORE' to continue or anything else to cancel"

    if ($confirm -ne "RESTORE") {
        Write-Host ""
        Write-Host "Restore cancelled. Your data is safe." -ForegroundColor Green

        # Cleanup temp extraction
        if ($isZipFile -and (Test-Path $extractPath)) {
            Remove-Item -Path $extractPath -Recurse -Force
        }

        Read-Host "Press Enter to exit"
        exit 0
    }
}

Write-Host ""

# Stop services
Write-Host "🛑 Stopping In My Head services..." -ForegroundColor Yellow

$composeFile = "infrastructure\docker\docker-compose.dev.yml"

if (Test-Path $composeFile) {
    try {
        Push-Location "infrastructure\docker"
        docker-compose -f docker-compose.dev.yml down 2>&1 | Out-Null
        Write-Host "   ✅ Services stopped" -ForegroundColor Green
        Pop-Location
    }
    catch {
        Write-Host "   ⚠️  Failed to stop services (may not be running)" -ForegroundColor Yellow
        Pop-Location
    }
}
else {
    Write-Host "   ⚠️  docker-compose.dev.yml not found" -ForegroundColor Yellow
}

Write-Host ""

# Find backup files
$backupFiles = Get-ChildItem -Path $workingDir -Filter "*.tar.gz"

if ($backupFiles.Count -eq 0) {
    Write-Host "   ❌ No backup files found in $workingDir" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "💾 Restoring Docker volumes..." -ForegroundColor Cyan
Write-Host ""

$totalFiles = $backupFiles.Count
$current = 0
$restored = 0
$failed = 0

foreach ($backupFile in $backupFiles) {
    $current++
    $volumeName = $backupFile.Name -replace '\.tar\.gz$', ''

    Write-Host "[$current/$totalFiles] Restoring: $volumeName" -ForegroundColor Yellow

    # Check if volume exists
    $volumeExists = docker volume ls --format "{{.Name}}" | Select-String -Pattern "^$volumeName$" -Quiet

    if (-not $volumeExists) {
        Write-Host "             Creating volume..." -ForegroundColor Gray
        docker volume create $volumeName | Out-Null
    }

    try {
        # Clear existing volume data
        docker run --rm -v "${volumeName}:/data" alpine sh -c "rm -rf /data/*" 2>&1 | Out-Null

        # Restore from backup
        docker run --rm `
            -v "${volumeName}:/data" `
            -v "${workingDir}:/backup" `
            alpine `
            sh -c "cd /data && tar xzf /backup/$($backupFile.Name)" 2>&1 | Out-Null

        Write-Host "             ✅ Restored successfully" -ForegroundColor Green
        $restored++
    }
    catch {
        Write-Host "             ❌ Failed: $_" -ForegroundColor Red
        $failed++
    }

    Write-Host ""
}

# Restore configuration files
Write-Host "📄 Restoring configuration files..." -ForegroundColor Cyan

$configFiles = @(
    @{Source = "docker-compose.dev.yml"; Dest = "infrastructure\docker\docker-compose.dev.yml" },
    @{Source = ".env"; Dest = "infrastructure\docker\.env" }
)

foreach ($config in $configFiles) {
    $sourcePath = Join-Path $workingDir $config.Source
    $destPath = $config.Dest

    if (Test-Path $sourcePath) {
        $fileName = Split-Path $destPath -Leaf

        # Backup existing file
        if (Test-Path $destPath) {
            $backupName = "$fileName.backup_$(Get-Date -Format 'yyyyMMddHHmmss')"
            $backupDest = Join-Path (Split-Path $destPath -Parent) $backupName
            Copy-Item $destPath -Destination $backupDest
            Write-Host "   📋 Backed up existing $fileName to $backupName" -ForegroundColor Gray
        }

        Copy-Item $sourcePath -Destination $destPath -Force
        Write-Host "   ✅ Restored $fileName" -ForegroundColor Green
    }
    else {
        Write-Host "   ⚠️  $($config.Source) not found in backup" -ForegroundColor Yellow
    }
}

Write-Host ""

# Cleanup temp extraction
if ($isZipFile -and (Test-Path $extractPath)) {
    Write-Host "🧹 Cleaning up temporary files..." -ForegroundColor Yellow
    Remove-Item -Path $extractPath -Recurse -Force
    Write-Host "   ✅ Cleanup complete" -ForegroundColor Green
    Write-Host ""
}

# Summary
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║           Restore Complete!                        ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "   Volumes Restored: $restored" -ForegroundColor Green
if ($failed -gt 0) {
    Write-Host "   Failed: $failed" -ForegroundColor Red
}
Write-Host ""

# Start services
Write-Host "🚀 Starting In My Head services..." -ForegroundColor Cyan
Write-Host ""

if (Test-Path $composeFile) {
    try {
        Push-Location "infrastructure\docker"

        Write-Host "   Starting containers..." -ForegroundColor Yellow
        docker-compose -f docker-compose.dev.yml up -d 2>&1 | Out-Null

        Write-Host "   ✅ Services started!" -ForegroundColor Green
        Write-Host ""
        Write-Host "   Waiting for services to initialize (30 seconds)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30

        # Check service health
        Write-Host ""
        Write-Host "   Checking service health:" -ForegroundColor Cyan

        $services = @(
            @{Name = "Document Processor"; Port = 8001 },
            @{Name = "AI Engine"; Port = 8002 },
            @{Name = "Search Service"; Port = 8003 }
        )

        foreach ($service in $services) {
            $isRunning = Test-NetConnection localhost -Port $service.Port -InformationLevel Quiet -WarningAction SilentlyContinue
            if ($isRunning) {
                Write-Host "   ✅ $($service.Name) is running" -ForegroundColor Green
            }
            else {
                Write-Host "   ⚠️  $($service.Name) is not responding" -ForegroundColor Yellow
            }
        }

        Pop-Location
    }
    catch {
        Write-Host "   ❌ Failed to start services: $_" -ForegroundColor Red
        Pop-Location
    }
}
else {
    Write-Host "   ⚠️  docker-compose.dev.yml not found" -ForegroundColor Yellow
    Write-Host "   Please start services manually" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Restore completed successfully!" -ForegroundColor Magenta
Write-Host ""
Write-Host "💡 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Open desktop app: .\Start_InMyHead.ps1" -ForegroundColor White
Write-Host "   2. Verify your documents are restored" -ForegroundColor White
Write-Host "   3. Test search functionality" -ForegroundColor White
Write-Host "   4. Create a new backup if needed" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
