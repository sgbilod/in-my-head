# ============================================================================
# FLATTEN PROJECT STRUCTURE SCRIPT
# ============================================================================
# Purpose: Move all files from nested "in-my-head\" folder to parent directory
# Author: GitHub Copilot
# Date: October 5, 2025
# ============================================================================

# Enable strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"
$Magenta = "Magenta"

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor $Cyan
Write-Host "║     FLATTEN PROJECT STRUCTURE - In My Head                       ║" -ForegroundColor $Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor $Cyan

# ============================================================================
# STEP 1: VERIFY CURRENT STRUCTURE
# ============================================================================

Write-Host "📋 STEP 1: Verifying current structure..." -ForegroundColor $Yellow

$rootPath = "C:\Users\sgbil\In My Head"
$nestedPath = Join-Path $rootPath "in-my-head"
$backupPath = Join-Path $rootPath "in-my-head-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# Verify paths exist
if (-not (Test-Path $rootPath)) {
    Write-Host "❌ ERROR: Root path not found: $rootPath" -ForegroundColor $Red
    exit 1
}

if (-not (Test-Path $nestedPath)) {
    Write-Host "❌ ERROR: Nested path not found: $nestedPath" -ForegroundColor $Red
    Write-Host "   The structure may already be flattened." -ForegroundColor $Yellow
    exit 1
}

Write-Host "   ✅ Root path exists: $rootPath" -ForegroundColor $Green
Write-Host "   ✅ Nested path exists: $nestedPath" -ForegroundColor $Green

# Display current structure
Write-Host "`n   Current structure:" -ForegroundColor $Cyan
Get-ChildItem -Path $rootPath -Directory | ForEach-Object {
    Write-Host "      📁 $($_.Name)" -ForegroundColor $Magenta
}

# ============================================================================
# STEP 2: CREATE BACKUP
# ============================================================================

Write-Host "`n📦 STEP 2: Creating backup..." -ForegroundColor $Yellow
Write-Host "   Backup location: $backupPath" -ForegroundColor $Cyan

try {
    Copy-Item -Path $nestedPath -Destination $backupPath -Recurse -Force
    Write-Host "   ✅ Backup created successfully" -ForegroundColor $Green
    
    # Verify backup
    $backupItems = Get-ChildItem -Path $backupPath -Recurse | Measure-Object
    Write-Host "   ℹ️  Backup contains $($backupItems.Count) items" -ForegroundColor $Cyan
}
catch {
    Write-Host "   ❌ ERROR: Failed to create backup: $_" -ForegroundColor $Red
    exit 1
}

# ============================================================================
# STEP 3: IDENTIFY FILES AND FOLDERS TO MOVE
# ============================================================================

Write-Host "`n📂 STEP 3: Identifying files and folders to move..." -ForegroundColor $Yellow

$itemsToMove = Get-ChildItem -Path $nestedPath -Force | Where-Object { $_.Name -ne ".git" }
Write-Host "   Found $($itemsToMove.Count) items to move" -ForegroundColor $Cyan

# Check for conflicts
$conflicts = @()
foreach ($item in $itemsToMove) {
    $targetPath = Join-Path $rootPath $item.Name
    if (Test-Path $targetPath) {
        $conflicts += $item.Name
        Write-Host "   ⚠️  Conflict detected: $($item.Name) exists in both locations" -ForegroundColor $Yellow
    }
}

if ($conflicts.Count -gt 0) {
    Write-Host "`n   📋 Conflicts that will be merged:" -ForegroundColor $Yellow
    foreach ($conflict in $conflicts) {
        Write-Host "      • $conflict" -ForegroundColor $Magenta
    }
}

# ============================================================================
# STEP 4: MOVE FILES AND FOLDERS
# ============================================================================

Write-Host "`n🚚 STEP 4: Moving files and folders..." -ForegroundColor $Yellow

$movedCount = 0
$mergedCount = 0
$errorCount = 0

foreach ($item in $itemsToMove) {
    $sourcePath = $item.FullName
    $targetPath = Join-Path $rootPath $item.Name
    
    try {
        if (Test-Path $targetPath) {
            # Item exists in target - need to merge
            if ($item.PSIsContainer) {
                Write-Host "   🔀 Merging folder: $($item.Name)" -ForegroundColor $Cyan
                
                # Get all items in source folder
                $sourceItems = Get-ChildItem -Path $sourcePath -Recurse -Force
                
                foreach ($sourceItem in $sourceItems) {
                    $relativePath = $sourceItem.FullName.Substring($sourcePath.Length + 1)
                    $targetItemPath = Join-Path $targetPath $relativePath
                    
                    if (-not (Test-Path $targetItemPath)) {
                        # Create parent directory if needed
                        $targetParent = Split-Path $targetItemPath -Parent
                        if (-not (Test-Path $targetParent)) {
                            New-Item -Path $targetParent -ItemType Directory -Force | Out-Null
                        }
                        
                        # Copy item
                        Copy-Item -Path $sourceItem.FullName -Destination $targetItemPath -Force
                    }
                }
                
                $mergedCount++
            }
            else {
                # File exists - overwrite with newer version
                Write-Host "   ⚠️  Overwriting file: $($item.Name)" -ForegroundColor $Yellow
                Copy-Item -Path $sourcePath -Destination $targetPath -Force
                $movedCount++
            }
        }
        else {
            # No conflict - simply move
            Write-Host "   ➡️  Moving: $($item.Name)" -ForegroundColor $Green
            Move-Item -Path $sourcePath -Destination $targetPath -Force
            $movedCount++
        }
    }
    catch {
        Write-Host "   ❌ ERROR moving $($item.Name): $_" -ForegroundColor $Red
        $errorCount++
    }
}

Write-Host "`n   ✅ Moved: $movedCount items" -ForegroundColor $Green
Write-Host "   🔀 Merged: $mergedCount folders" -ForegroundColor $Cyan
if ($errorCount -gt 0) {
    Write-Host "   ❌ Errors: $errorCount items" -ForegroundColor $Red
}

# ============================================================================
# STEP 5: CLEAN UP EMPTY NESTED FOLDER
# ============================================================================

Write-Host "`n🧹 STEP 5: Cleaning up empty nested folder..." -ForegroundColor $Yellow

# Check if nested folder is empty or only has .git
$remainingItems = Get-ChildItem -Path $nestedPath -Force | Where-Object { $_.Name -ne ".git" }

if ($remainingItems.Count -eq 0) {
    try {
        # Remove .git if it exists in nested folder
        $nestedGit = Join-Path $nestedPath ".git"
        if (Test-Path $nestedGit) {
            Write-Host "   ℹ️  Removing .git from nested folder..." -ForegroundColor $Cyan
            Remove-Item -Path $nestedGit -Recurse -Force
        }
        
        # Remove empty nested folder
        Remove-Item -Path $nestedPath -Force -Recurse
        Write-Host "   ✅ Removed empty nested folder" -ForegroundColor $Green
    }
    catch {
        Write-Host "   ⚠️  Warning: Could not remove nested folder: $_" -ForegroundColor $Yellow
        Write-Host "   ℹ️  You can manually delete it: $nestedPath" -ForegroundColor $Cyan
    }
}
else {
    Write-Host "   ⚠️  Warning: Nested folder still contains items:" -ForegroundColor $Yellow
    $remainingItems | ForEach-Object {
        Write-Host "      • $($_.Name)" -ForegroundColor $Magenta
    }
    Write-Host "   ℹ️  Please review and manually delete if appropriate" -ForegroundColor $Cyan
}

# ============================================================================
# STEP 6: VERIFY MOVE WAS SUCCESSFUL
# ============================================================================

Write-Host "`n✅ STEP 6: Verifying move was successful..." -ForegroundColor $Yellow

# Count items in backup vs new structure
$backupItemCount = (Get-ChildItem -Path $backupPath -Recurse -File | Measure-Object).Count
$rootItemCount = (Get-ChildItem -Path $rootPath -Recurse -File | Where-Object { $_.FullName -notlike "*$backupPath*" -and $_.FullName -notlike "*in-my-head\*" } | Measure-Object).Count

Write-Host "   📊 Backup file count: $backupItemCount" -ForegroundColor $Cyan
Write-Host "   📊 Root file count: $rootItemCount" -ForegroundColor $Cyan

# Display new structure
Write-Host "`n   New structure:" -ForegroundColor $Cyan
Get-ChildItem -Path $rootPath -Directory | Where-Object { $_.Name -notlike "*backup*" -and $_.Name -ne "in-my-head" } | ForEach-Object {
    Write-Host "      📁 $($_.Name)" -ForegroundColor $Magenta
}

# Check for key directories
$keyDirs = @("services", "docs", "infrastructure", "frontend", "scripts", "tests")
$missingDirs = @()

foreach ($dir in $keyDirs) {
    $dirPath = Join-Path $rootPath $dir
    if (Test-Path $dirPath) {
        Write-Host "   ✅ Found: $dir\" -ForegroundColor $Green
    }
    else {
        Write-Host "   ⚠️  Missing: $dir\" -ForegroundColor $Yellow
        $missingDirs += $dir
    }
}

# Check for key files
$keyFiles = @("README.md", "package.json", "PHASE_2_COMPLETE.md")
foreach ($file in $keyFiles) {
    $filePath = Join-Path $rootPath $file
    if (Test-Path $filePath) {
        Write-Host "   ✅ Found: $file" -ForegroundColor $Green
    }
    else {
        Write-Host "   ⚠️  Missing: $file" -ForegroundColor $Yellow
    }
}

# ============================================================================
# STEP 7: UPDATE GIT CONFIGURATION (if needed)
# ============================================================================

Write-Host "`n🔧 STEP 7: Checking Git configuration..." -ForegroundColor $Yellow

$gitPath = Join-Path $rootPath ".git"
if (Test-Path $gitPath) {
    Write-Host "   ✅ Git repository found at root level" -ForegroundColor $Green
    
    # Check Git status
    Push-Location $rootPath
    try {
        $gitStatus = git status --short 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ℹ️  Git status:" -ForegroundColor $Cyan
            Write-Host "      $gitStatus" -ForegroundColor $Magenta
        }
    }
    catch {
        Write-Host "   ℹ️  Could not check Git status" -ForegroundColor $Cyan
    }
    Pop-Location
}
else {
    Write-Host "   ⚠️  No Git repository found at root" -ForegroundColor $Yellow
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor $Green
Write-Host "║                 FLATTENING COMPLETE ✅                            ║" -ForegroundColor $Green
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor $Green

Write-Host "📊 SUMMARY:" -ForegroundColor $Yellow
Write-Host "   ✅ Backup created: $backupPath" -ForegroundColor $Green
Write-Host "   ✅ Moved: $movedCount items" -ForegroundColor $Green
Write-Host "   ✅ Merged: $mergedCount folders" -ForegroundColor $Green
if ($errorCount -gt 0) {
    Write-Host "   ⚠️  Errors: $errorCount items (check details above)" -ForegroundColor $Yellow
}

Write-Host "`n📝 NEXT STEPS:" -ForegroundColor $Yellow
Write-Host "   1. Review the new structure in: $rootPath" -ForegroundColor $Cyan
Write-Host "   2. Test your project to ensure everything works" -ForegroundColor $Cyan
Write-Host "   3. If everything works, you can delete the backup:" -ForegroundColor $Cyan
Write-Host "      Remove-Item '$backupPath' -Recurse -Force" -ForegroundColor $Magenta
Write-Host "   4. Run the environment setup script:" -ForegroundColor $Cyan
Write-Host "      .\setup-environment.ps1" -ForegroundColor $Magenta
Write-Host "   5. Commit the changes to Git:" -ForegroundColor $Cyan
Write-Host "      git add ." -ForegroundColor $Magenta
Write-Host "      git commit -m 'Flatten project structure - remove nested in-my-head folder'" -ForegroundColor $Magenta

Write-Host "`n⚠️  IMPORTANT:" -ForegroundColor $Yellow
Write-Host "   • Update any IDE workspace paths" -ForegroundColor $Cyan
Write-Host "   • Update any scripts that reference the old path" -ForegroundColor $Cyan
Write-Host "   • Update environment variables if they point to nested folder" -ForegroundColor $Cyan

Write-Host "`n════════════════════════════════════════════════════════════════════`n" -ForegroundColor $Cyan

# Pause to let user review
Write-Host "Press any key to exit..." -ForegroundColor $Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
