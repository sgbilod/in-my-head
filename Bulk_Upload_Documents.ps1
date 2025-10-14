# Bulk Document Upload Script for In My Head
# ===========================================
# Scans directories and uploads documents to your knowledge base

param(
    [Parameter(Mandatory = $false)]
    [string]$SourcePath = "",

    [Parameter(Mandatory = $false)]
    [switch]$Recursive = $true,

    [Parameter(Mandatory = $false)]
    [string[]]$FileTypes = @("*.pdf", "*.docx", "*.doc", "*.txt", "*.md", "*.html", "*.htm", "*.rtf", "*.odt", "*.epub"),

    [Parameter(Mandatory = $false)]
    [int]$BatchSize = 5,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun = $false,

    [Parameter(Mandatory = $false)]
    [int]$MaxFileSizeMB = 50
)

$ErrorActionPreference = "Continue"

# Banner
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🧠 In My Head - Bulk Document Upload             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if service is running
Write-Host "🔍 Checking Document Processor service..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8001/health" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   ✅ Service is running!" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "   ❌ Document Processor is not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start the application first:" -ForegroundColor Yellow
    Write-Host "   .\Start_InMyHead.ps1" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Get source path if not provided
if ([string]::IsNullOrEmpty($SourcePath)) {
    Write-Host "📁 Select folder to scan for documents" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Common locations:" -ForegroundColor Yellow
    Write-Host "   1. Documents folder: $env:USERPROFILE\Documents" -ForegroundColor Gray
    Write-Host "   2. Downloads folder: $env:USERPROFILE\Downloads" -ForegroundColor Gray
    Write-Host "   3. Desktop: $env:USERPROFILE\Desktop" -ForegroundColor Gray
    Write-Host "   4. Custom path (you specify)" -ForegroundColor Gray
    Write-Host ""

    $choice = Read-Host "Enter choice (1-4)"

    switch ($choice) {
        "1" { $SourcePath = "$env:USERPROFILE\Documents" }
        "2" { $SourcePath = "$env:USERPROFILE\Downloads" }
        "3" { $SourcePath = "$env:USERPROFILE\Desktop" }
        "4" {
            $SourcePath = Read-Host "Enter full path to folder"
        }
        default {
            Write-Host "Invalid choice. Using Documents folder." -ForegroundColor Yellow
            $SourcePath = "$env:USERPROFILE\Documents"
        }
    }
}

# Validate source path
if (-not (Test-Path $SourcePath)) {
    Write-Host "❌ Path does not exist: $SourcePath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "📊 Scan Configuration:" -ForegroundColor Cyan
Write-Host "   Source: $SourcePath" -ForegroundColor White
Write-Host "   Recursive: $Recursive" -ForegroundColor White
Write-Host "   File Types: $($FileTypes -join ', ')" -ForegroundColor White
Write-Host "   Max Size: $MaxFileSizeMB MB" -ForegroundColor White
Write-Host "   Batch Size: $BatchSize files at a time" -ForegroundColor White
if ($DryRun) {
    Write-Host "   Mode: DRY RUN (no actual uploads)" -ForegroundColor Yellow
}
else {
    Write-Host "   Mode: LIVE UPLOAD" -ForegroundColor Green
}
Write-Host ""

# Scan for files
Write-Host "🔍 Scanning for documents..." -ForegroundColor Yellow

$allFiles = @()
foreach ($fileType in $FileTypes) {
    if ($Recursive) {
        $files = Get-ChildItem -Path $SourcePath -Filter $fileType -Recurse -File -ErrorAction SilentlyContinue
    }
    else {
        $files = Get-ChildItem -Path $SourcePath -Filter $fileType -File -ErrorAction SilentlyContinue
    }
    $allFiles += $files
}

# Filter by size
$maxSizeBytes = $MaxFileSizeMB * 1MB
$filteredFiles = $allFiles | Where-Object { $_.Length -le $maxSizeBytes }
$oversizedFiles = $allFiles | Where-Object { $_.Length -gt $maxSizeBytes }

Write-Host ""
Write-Host "📋 Scan Results:" -ForegroundColor Cyan
Write-Host "   Total files found: $($allFiles.Count)" -ForegroundColor White
Write-Host "   Files to upload: $($filteredFiles.Count)" -ForegroundColor Green
Write-Host "   Files too large: $($oversizedFiles.Count)" -ForegroundColor Yellow
Write-Host ""

if ($oversizedFiles.Count -gt 0) {
    Write-Host "⚠️  Skipping oversized files (>$MaxFileSizeMB MB):" -ForegroundColor Yellow
    $oversizedFiles | Select-Object -First 5 | ForEach-Object {
        $sizeMB = [math]::Round($_.Length / 1MB, 2)
        Write-Host "      $($_.Name) ($sizeMB MB)" -ForegroundColor Gray
    }
    if ($oversizedFiles.Count -gt 5) {
        Write-Host "      ... and $($oversizedFiles.Count - 5) more" -ForegroundColor Gray
    }
    Write-Host ""
}

if ($filteredFiles.Count -eq 0) {
    Write-Host "❌ No files found to upload!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 0
}

# Show file type breakdown
Write-Host "📊 File Types:" -ForegroundColor Cyan
$filteredFiles | Group-Object Extension | Sort-Object Count -Descending | ForEach-Object {
    Write-Host "   $($_.Name): $($_.Count) files" -ForegroundColor White
}
Write-Host ""

# Confirm upload
if (-not $DryRun) {
    Write-Host "⚠️  Ready to upload $($filteredFiles.Count) files" -ForegroundColor Yellow
    Write-Host ""
    $confirm = Read-Host "Continue with upload? (yes/no)"

    if ($confirm -ne "yes" -and $confirm -ne "y") {
        Write-Host "❌ Upload cancelled" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 0
    }
    Write-Host ""
}

# Upload files
$successful = 0
$failed = 0
$skipped = 0
$totalSize = 0
$failedFiles = @()

Write-Host "🚀 Starting upload..." -ForegroundColor Green
Write-Host ""

$startTime = Get-Date

for ($i = 0; $i -lt $filteredFiles.Count; $i++) {
    $file = $filteredFiles[$i]
    $progress = [math]::Round(($i / $filteredFiles.Count) * 100, 1)

    Write-Host "[$progress%] " -NoNewline -ForegroundColor Cyan
    Write-Host "Uploading: " -NoNewline -ForegroundColor White
    Write-Host $file.Name -ForegroundColor Yellow

    if ($DryRun) {
        Write-Host "         [DRY RUN] Would upload: $($file.FullName)" -ForegroundColor Gray
        $successful++
        Start-Sleep -Milliseconds 100
        continue
    }

    try {
        # Upload file
        $fileStream = [System.IO.File]::OpenRead($file.FullName)
        $fileContent = New-Object System.Net.Http.StreamContent($fileStream)
        $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/octet-stream")

        $multipartContent = New-Object System.Net.Http.MultipartFormDataContent
        $multipartContent.Add($fileContent, "file", $file.Name)

        $httpClient = New-Object System.Net.Http.HttpClient
        $httpClient.Timeout = [TimeSpan]::FromSeconds(120)

        $response = $httpClient.PostAsync("http://localhost:8001/documents/upload", $multipartContent).Result

        $fileStream.Close()
        $httpClient.Dispose()

        if ($response.IsSuccessStatusCode) {
            $successful++
            $totalSize += $file.Length
            Write-Host "         ✅ Success" -ForegroundColor Green
        }
        else {
            $failed++
            $failedFiles += $file.FullName
            Write-Host "         ❌ Failed: HTTP $($response.StatusCode)" -ForegroundColor Red
        }

    }
    catch {
        $failed++
        $failedFiles += $file.FullName
        Write-Host "         ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }

    # Brief pause between uploads
    Start-Sleep -Milliseconds 500
}

$endTime = Get-Date
$duration = $endTime - $startTime

# Summary
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              Upload Complete!                      ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "   ✅ Successful: $successful files" -ForegroundColor Green
Write-Host "   ❌ Failed: $failed files" -ForegroundColor Red
Write-Host "   ⏱️  Duration: $($duration.TotalSeconds.ToString('0.0')) seconds" -ForegroundColor White
if (-not $DryRun) {
    $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
    Write-Host "   📦 Total Uploaded: $totalSizeMB MB" -ForegroundColor White

    if ($duration.TotalSeconds -gt 0) {
        $throughput = [math]::Round($successful / $duration.TotalSeconds, 2)
        Write-Host "   ⚡ Throughput: $throughput files/sec" -ForegroundColor White
    }
}
Write-Host ""

# Show failed files
if ($failed -gt 0) {
    Write-Host "❌ Failed Files:" -ForegroundColor Red
    $failedFiles | ForEach-Object {
        Write-Host "   $_" -ForegroundColor Gray
    }
    Write-Host ""

    # Offer to save failed files list
    $saveList = Read-Host "Save failed files list to file? (yes/no)"
    if ($saveList -eq "yes" -or $saveList -eq "y") {
        $failedListPath = "failed_uploads_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
        $failedFiles | Out-File -FilePath $failedListPath -Encoding UTF8
        Write-Host "   💾 Saved to: $failedListPath" -ForegroundColor Green
        Write-Host ""
    }
}

# Generate embeddings
if (-not $DryRun -and $successful -gt 0) {
    Write-Host "🤖 Generating embeddings for uploaded documents..." -ForegroundColor Yellow
    try {
        $embedResponse = Invoke-RestMethod -Uri "http://localhost:8001/search/generate-embeddings" -Method Post -TimeoutSec 300
        Write-Host "   ✅ Embeddings generated successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "   ⚠️  Embeddings generation queued (will process in background)" -ForegroundColor Yellow
    }
    Write-Host ""
}

Write-Host "🎉 Bulk upload completed!" -ForegroundColor Magenta
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "   1. Open the desktop app to view your documents" -ForegroundColor White
Write-Host "   2. Click 'Open Web Interface' to search and query" -ForegroundColor White
Write-Host "   3. Try semantic search across all uploaded documents" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
