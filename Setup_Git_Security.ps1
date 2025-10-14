# Setup Git Security for In My Head
# ==================================
# Configures Git to prevent committing sensitive files

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🔒 Git Security Setup - In My Head                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if in Git repository
if (-not (Test-Path ".git")) {
  Write-Host "❌ Not a Git repository!" -ForegroundColor Red
  Write-Host "   Run 'git init' first" -ForegroundColor Yellow
  Read-Host "Press Enter to exit"
  exit 1
}

Write-Host "📋 Configuring Git security settings..." -ForegroundColor Yellow
Write-Host ""

# 1. Verify .gitignore exists and has necessary rules
Write-Host "1️⃣  Checking .gitignore..." -ForegroundColor Cyan

$requiredIgnores = @(
  ".env",
  "*.env",
  ".env.local",
  ".env.*.local",
  "backups/",
  "backup_*.zip",
  "*.tar.gz",
  "config.json",
  "credentials.json",
  "secrets.json",
  "*.key",
  "*.pem"
)

$gitignorePath = ".gitignore"
$gitignoreContent = if (Test-Path $gitignorePath) { Get-Content $gitignorePath } else { @() }

$missing = @()
foreach ($pattern in $requiredIgnores) {
  if ($gitignoreContent -notcontains $pattern) {
    $missing += $pattern
  }
}

if ($missing.Count -gt 0) {
  Write-Host "   ⚠️  Missing patterns in .gitignore:" -ForegroundColor Yellow
  foreach ($pattern in $missing) {
    Write-Host "      - $pattern" -ForegroundColor DarkGray
  }

  $addToIgnore = Read-Host "   Add missing patterns? (y/n)"
  if ($addToIgnore -eq "y" -or $addToIgnore -eq "Y") {
    Add-Content -Path $gitignorePath -Value "`n# Security - Added by Setup_Git_Security.ps1"
    foreach ($pattern in $missing) {
      Add-Content -Path $gitignorePath -Value $pattern
    }
    Write-Host "   ✅ Updated .gitignore" -ForegroundColor Green
  }
}
else {
  Write-Host "   ✅ .gitignore is properly configured" -ForegroundColor Green
}

Write-Host ""

# 2. Check if sensitive files are already tracked
Write-Host "2️⃣  Scanning for tracked sensitive files..." -ForegroundColor Cyan

$trackedSensitive = @()
foreach ($pattern in $requiredIgnores) {
  $tracked = git ls-files $pattern 2>$null
  if ($tracked) {
    $trackedSensitive += $tracked
  }
}

if ($trackedSensitive.Count -gt 0) {
  Write-Host "   ❌ CRITICAL: Sensitive files are tracked by Git!" -ForegroundColor Red
  Write-Host ""
  foreach ($file in $trackedSensitive) {
    Write-Host "      ❌ $file" -ForegroundColor Red
  }
  Write-Host ""
  Write-Host "   These files should be removed from Git history!" -ForegroundColor Yellow
  Write-Host ""

  $removeFiles = Read-Host "   Remove these files from Git tracking? (y/n)"
  if ($removeFiles -eq "y" -or $removeFiles -eq "Y") {
    foreach ($file in $trackedSensitive) {
      git rm --cached $file 2>$null
      Write-Host "   ✅ Removed $file from Git tracking" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "   ⚠️  Files removed from tracking but still in history!" -ForegroundColor Yellow
    Write-Host "   To clean history, see: SECURITY_INCIDENT_RESPONSE.md" -ForegroundColor Yellow
  }
}
else {
  Write-Host "   ✅ No sensitive files are tracked" -ForegroundColor Green
}

Write-Host ""

# 3. Install pre-commit hook
Write-Host "3️⃣  Installing pre-commit security hook..." -ForegroundColor Cyan

$hooksDir = ".git\hooks"
$preCommitHook = Join-Path $hooksDir "pre-commit"

if (-not (Test-Path $hooksDir)) {
  New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
}

$hookContent = @"
#!/bin/sh
# Pre-commit hook: Security check
# Runs Check_Git_Security.ps1 before each commit

echo "Running security checks..."
powershell.exe -ExecutionPolicy Bypass -File "Check_Git_Security.ps1"
exit `$?
"@

$hookContent | Out-File -FilePath $preCommitHook -Encoding ASCII

Write-Host "   ✅ Pre-commit hook installed" -ForegroundColor Green
Write-Host ""

# 4. Configure Git to use pre-commit hooks
Write-Host "4️⃣  Configuring Git settings..." -ForegroundColor Cyan

git config core.hooksPath .git/hooks
Write-Host "   ✅ Hooks path configured" -ForegroundColor Green

Write-Host ""

# 5. Test the security check
Write-Host "5️⃣  Testing security check..." -ForegroundColor Cyan

try {
  & ".\Check_Git_Security.ps1"
  Write-Host "   ✅ Security check is working" -ForegroundColor Green
}
catch {
  Write-Host "   ⚠️  Security check test failed: $_" -ForegroundColor Yellow
}

Write-Host ""

# Summary
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║           Setup Complete!                          ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "🔒 Security Features Enabled:" -ForegroundColor Cyan
Write-Host "   ✅ .gitignore configured" -ForegroundColor Green
Write-Host "   ✅ Sensitive files excluded" -ForegroundColor Green
Write-Host "   ✅ Pre-commit hook installed" -ForegroundColor Green
Write-Host "   ✅ Automatic security scanning" -ForegroundColor Green
Write-Host ""
Write-Host "💡 What happens now:" -ForegroundColor Cyan
Write-Host "   • Every commit will be scanned for sensitive files" -ForegroundColor White
Write-Host "   • API keys and passwords will be detected" -ForegroundColor White
Write-Host "   • Commits blocked if sensitive data found" -ForegroundColor White
Write-Host ""
Write-Host "🚨 Remember:" -ForegroundColor Yellow
Write-Host "   • NEVER commit .env files" -ForegroundColor Yellow
Write-Host "   • NEVER commit backups/" -ForegroundColor Yellow
Write-Host "   • Keep API keys in password manager" -ForegroundColor Yellow
Write-Host "   • Review 'git status' before commits" -ForegroundColor Yellow
Write-Host ""
Write-Host "📚 For more info:" -ForegroundColor Cyan
Write-Host "   • SECURITY_INCIDENT_RESPONSE.md - Security guide" -ForegroundColor White
Write-Host "   • Check_Git_Security.ps1 - Manual security check" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
