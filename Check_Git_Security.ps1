# Pre-Commit Security Check for In My Head
# =========================================
# Prevents committing sensitive files to Git

Write-Host ""
Write-Host "🔒 Security Check: Scanning for sensitive files..." -ForegroundColor Cyan
Write-Host ""

# Files that should NEVER be committed
$forbiddenPatterns = @(
  "*.env",
  ".env",
  ".env.local",
  ".env.*.local",
  "config.json",
  "backups/",
  "backup_*.zip",
  "*.tar.gz",
  "credentials.json",
  "secrets.json",
  "*.key",
  "*.pem"
)

# Check staged files
$stagedFiles = git diff --cached --name-only

$violations = @()

foreach ($file in $stagedFiles) {
  foreach ($pattern in $forbiddenPatterns) {
    if ($file -like $pattern) {
      $violations += $file
    }
  }
}

if ($violations.Count -gt 0) {
  Write-Host "❌ SECURITY VIOLATION: Sensitive files detected!" -ForegroundColor Red -BackgroundColor Yellow
  Write-Host ""
  Write-Host "The following files should NOT be committed:" -ForegroundColor Red
  foreach ($violation in $violations) {
    Write-Host "   ❌ $violation" -ForegroundColor Red
  }
  Write-Host ""
  Write-Host "These files may contain:" -ForegroundColor Yellow
  Write-Host "   • API keys and passwords" -ForegroundColor Yellow
  Write-Host "   • Database credentials" -ForegroundColor Yellow
  Write-Host "   • Personal data" -ForegroundColor Yellow
  Write-Host ""
  Write-Host "To fix:" -ForegroundColor Cyan
  Write-Host "   1. Unstage files: git reset HEAD <file>" -ForegroundColor White
  Write-Host "   2. Add to .gitignore if not already there" -ForegroundColor White
  Write-Host "   3. Verify .gitignore is working: git status" -ForegroundColor White
  Write-Host ""

  $override = Read-Host "Type 'OVERRIDE' to commit anyway (NOT RECOMMENDED)"

  if ($override -ne "OVERRIDE") {
    Write-Host ""
    Write-Host "✅ Commit blocked for your safety!" -ForegroundColor Green
    Write-Host ""
    exit 1
  }
  else {
    Write-Host ""
    Write-Host "⚠️  WARNING: Proceeding with commit (you chose to override)" -ForegroundColor Red
    Write-Host ""
  }
}
else {
  Write-Host "✅ No sensitive files detected" -ForegroundColor Green
  Write-Host ""
}

# Check for potential API keys in staged content
Write-Host "🔍 Scanning file contents for API keys..." -ForegroundColor Cyan

$suspiciousPatterns = @(
  "sk-ant-api03-",  # Anthropic
  "sk-proj-",        # OpenAI (project keys)
  "sk-[a-zA-Z0-9]{20,}",  # Generic OpenAI-style keys
  "ghp_",            # GitHub Personal Access Token
  "gho_",            # GitHub OAuth token
  "Bearer [a-zA-Z0-9_-]+",  # Bearer tokens
  "password\s*=\s*['\"][^'\"]{8,}",  # Passwords
    "api_key\s*=\s*['\"][^'\"]{ 8, }"    # API keys
)

$contentViolations = @()

foreach ($file in $stagedFiles) {
    if (Test-Path $file) {
        $content = Get-Content $file -Raw -ErrorAction SilentlyContinue

        if ($content) {
            foreach ($pattern in $suspiciousPatterns) {
                if ($content -match $pattern) {
                    $contentViolations += @{
                        File = $file
                        Pattern = $pattern
                    }
                }
            }
        }
    }
}

if ($contentViolations.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️  POTENTIAL SECRETS DETECTED IN FILE CONTENTS!" -ForegroundColor Red -BackgroundColor Yellow
    Write-Host ""

    foreach ($violation in $contentViolations) {
        Write-Host "   ⚠️  $($violation.File)" -ForegroundColor Red
        Write-Host "      Pattern: $($violation.Pattern)" -ForegroundColor DarkGray
    }

    Write-Host ""
    Write-Host "These files may contain API keys or passwords!" -ForegroundColor Yellow
    Write-Host "Please review carefully before committing." -ForegroundColor Yellow
    Write-Host ""

    $proceed = Read-Host "Type 'YES' to proceed anyway (review required)"

    if ($proceed -ne "YES") {
        Write-Host ""
        Write-Host "✅ Commit cancelled for security review" -ForegroundColor Green
        Write-Host ""
        exit 1
    }
}
else {
    Write-Host "✅ No API keys detected in file contents" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ Security check passed!" -ForegroundColor Green
Write-Host ""

exit 0
