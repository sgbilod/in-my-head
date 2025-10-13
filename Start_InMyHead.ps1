# In My Head - PowerShell Launcher
# =================================
# Modern launcher with visual feedback

$Host.UI.RawUI.WindowTitle = "In My Head - Starting..."

# Colors
$ColorSuccess = "Green"
$ColorError = "Red"
$ColorInfo = "Cyan"
$ColorWarning = "Yellow"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White",
        [string]$Prefix = ""
    )

    if ($Prefix) {
        Write-Host "$Prefix " -NoNewline -ForegroundColor $Color
        Write-Host $Message
    }
    else {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Show-Banner {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║                                        ║" -ForegroundColor Magenta
    Write-Host "║     🧠  IN MY HEAD  🧠                 ║" -ForegroundColor Magenta
    Write-Host "║                                        ║" -ForegroundColor Magenta
    Write-Host "║   AI-Powered Knowledge Management      ║" -ForegroundColor Magenta
    Write-Host "║                                        ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
}

function Test-Prerequisite {
    param(
        [string]$Name,
        [scriptblock]$Test
    )

    Write-Host "Checking $Name... " -NoNewline

    try {
        $result = & $Test
        if ($result) {
            Write-ColorOutput "✓" $ColorSuccess
            return $true
        }
        else {
            Write-ColorOutput "✗" $ColorError
            return $false
        }
    }
    catch {
        Write-ColorOutput "✗" $ColorError
        return $false
    }
}

# Show banner
Show-Banner

# Check prerequisites
Write-ColorOutput "🔍 Checking Prerequisites..." $ColorInfo
Write-Host ""

# Check Python
$pythonOk = Test-Prerequisite "Python 3.11+" {
    $version = python --version 2>&1
    if ($version -match "Python 3\.(\d+)") {
        $minor = [int]$matches[1]
        return $minor -ge 11
    }
    return $false
}

if (-not $pythonOk) {
    Write-ColorOutput "❌ Python 3.11+ is required" $ColorError
    Write-Host "   Download from: https://www.python.org/downloads/"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Docker
$dockerOk = Test-Prerequisite "Docker Desktop" {
    try {
        docker ps 2>&1 | Out-Null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

if (-not $dockerOk) {
    Write-ColorOutput "❌ Docker Desktop is not running" $ColorError
    Write-Host "   Please start Docker Desktop and try again"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-ColorOutput "✅ All prerequisites met!" $ColorSuccess
Write-Host ""

# Setup virtual environment
if (-not (Test-Path "venv")) {
    Write-ColorOutput "📦 Creating virtual environment..." $ColorInfo
    python -m venv venv
}

# Activate virtual environment
Write-ColorOutput "🔌 Activating virtual environment..." $ColorInfo
& "venv\Scripts\Activate.ps1"

# Install dependencies
Write-ColorOutput "📥 Installing dependencies..." $ColorInfo
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null
pip install PyQt6 requests --quiet 2>&1 | Out-Null

Write-Host ""
Write-ColorOutput "🚀 Launching In My Head..." $ColorSuccess
Write-Host ""

# Launch application
try {
    python InMyHead.py
}
catch {
    Write-ColorOutput "❌ Application error: $_" $ColorError
    Read-Host "Press Enter to exit"
    exit 1
}

# Cleanup
deactivate
