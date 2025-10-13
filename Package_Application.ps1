# In My Head - Application Packager
# ==================================
# Creates a portable package of the application

param(
    [string]$OutputPath = ".\InMyHead_Package",
    [switch]$IncludeVenv
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔═══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  In My Head - Application Packager        ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Get source directory
$SourcePath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Create output directory
Write-Host "📦 Creating package directory..." -ForegroundColor Yellow
if (Test-Path $OutputPath) {
    Write-Host "   Removing existing package..." -ForegroundColor Gray
    Remove-Item -Path $OutputPath -Recurse -Force
}
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null

# Files and folders to include
$ItemsToInclude = @(
    "InMyHead.py",
    "Start_InMyHead.bat",
    "Start_InMyHead.ps1",
    "Create_Desktop_Shortcut.ps1",
    "DESKTOP_APP_README.md",
    "infrastructure",
    "services",
    "docs"
)

# Copy files
Write-Host "📁 Copying application files..." -ForegroundColor Yellow
foreach ($item in $ItemsToInclude) {
    $sourcePath = Join-Path $SourcePath $item
    $destPath = Join-Path $OutputPath $item

    if (Test-Path $sourcePath) {
        Write-Host "   ✓ $item" -ForegroundColor Green

        if (Test-Path $sourcePath -PathType Container) {
            # It's a directory
            Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
        }
        else {
            # It's a file
            Copy-Item -Path $sourcePath -Destination $destPath -Force
        }
    }
    else {
        Write-Host "   ⚠ $item (not found)" -ForegroundColor Yellow
    }
}

# Copy virtual environment if requested
if ($IncludeVenv -and (Test-Path (Join-Path $SourcePath "venv"))) {
    Write-Host "📦 Including virtual environment..." -ForegroundColor Yellow
    Copy-Item -Path (Join-Path $SourcePath "venv") -Destination (Join-Path $OutputPath "venv") -Recurse -Force
    Write-Host "   ✓ venv included" -ForegroundColor Green
}

# Create requirements.txt for the application
Write-Host "📝 Creating requirements.txt..." -ForegroundColor Yellow
$requirements = @"
# In My Head Desktop Application Dependencies
PyQt6>=6.6.0
requests>=2.31.0
"@
Set-Content -Path (Join-Path $OutputPath "requirements.txt") -Value $requirements
Write-Host "   ✓ requirements.txt created" -ForegroundColor Green

# Create installation guide
Write-Host "📄 Creating installation guide..." -ForegroundColor Yellow
$installGuide = @"
# In My Head - Installation Guide

## Quick Installation (Windows)

1. Extract this package to your desired location
2. Ensure Docker Desktop is installed and running
3. Double-click: Start_InMyHead.bat
4. Wait for services to start (first time takes 2-3 minutes)
5. Start uploading documents!

## Prerequisites

### 1. Docker Desktop
- Download: https://www.docker.com/products/docker-desktop
- Install and start Docker Desktop
- Verify: Open terminal and run 'docker --version'

### 2. Python 3.11 or higher
- Download: https://www.python.org/downloads/
- During installation, CHECK "Add Python to PATH"
- Verify: Open terminal and run 'python --version'

## First Launch

1. Navigate to the extracted folder
2. Right-click 'Start_InMyHead.bat'
3. Select "Run as administrator" (first time only)
4. Wait for automatic setup to complete
5. Application window will appear

## Creating Desktop Shortcut

1. Right-click 'Create_Desktop_Shortcut.ps1'
2. Select "Run with PowerShell"
3. Shortcut will appear on your desktop

## What Gets Installed

- Python virtual environment (in 'venv' folder)
- PyQt6 GUI framework
- Required Python packages
- Docker containers (downloaded on first run)

## Disk Space Requirements

- Application: ~100 MB
- Docker Images: ~5 GB (first time)
- Total: ~5.1 GB

## Firewall & Antivirus

The application uses these ports locally:
- 5432 (PostgreSQL)
- 6333 (Qdrant)
- 6379 (Redis)
- 8000 (Document Processor)

If your firewall blocks these, create exceptions for localhost connections.

## Troubleshooting

### "Python is not recognized"
- Reinstall Python and CHECK "Add to PATH"
- Or manually add Python to system PATH

### "Docker is not running"
- Start Docker Desktop
- Wait for it to fully initialize (whale icon in system tray)

### Services won't start
- Check Docker Desktop is running
- Restart Docker Desktop
- View logs with "View Logs" button

### Port conflicts
- Check if ports 5432, 6333, 6379, 8000 are free
- Close other applications using these ports
- Or modify ports in docker-compose.dev.yml

## Configuration

### API Keys (Optional)
Edit: infrastructure/docker/.env

```env
# For AI features (optional)
ANTHROPIC_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here

# Local embeddings work without API keys
EMBEDDING_PROVIDER=local
```

## Uninstallation

1. Stop the application (Right-click tray icon → Quit)
2. Stop Docker containers:
   ```
   cd infrastructure/docker
   docker-compose -f docker-compose.dev.yml down -v
   ```
3. Delete the application folder
4. Delete Docker images (optional):
   ```
   docker system prune -a
   ```

## Support

For issues, feature requests, or questions:
- Check DESKTOP_APP_README.md
- View application logs (View Logs button)
- Check Docker Desktop logs

## Version Information

Package Date: $(Get-Date -Format "yyyy-MM-dd")
Application Version: 1.0.0

---

🧠 In My Head - Your Private AI Knowledge Management System
"@
Set-Content -Path (Join-Path $OutputPath "INSTALLATION_GUIDE.md") -Value $installGuide
Write-Host "   ✓ INSTALLATION_GUIDE.md created" -ForegroundColor Green

# Create README
Write-Host "📄 Creating README..." -ForegroundColor Yellow
$readme = @"
# 🧠 In My Head

**AI-Powered Personal Knowledge Management System**

## What is This?

In My Head is a privacy-first, AI-powered knowledge management system that helps you:

- 📄 **Organize Documents**: Upload PDFs, Word docs, text files, markdown, and more
- 🔍 **Semantic Search**: Find information using natural language queries
- 💬 **AI Chat**: Ask questions about your documents and get intelligent answers
- 🔒 **100% Private**: All processing happens on your machine
- 🚀 **Zero Configuration**: Just double-click and start

## Quick Start

1. **Extract this package** to any folder
2. **Start Docker Desktop** (download from docker.com if needed)
3. **Double-click** `Start_InMyHead.bat`
4. **Wait** for services to start (2-3 minutes first time)
5. **Upload documents** via drag-and-drop
6. **Start searching** and chatting with your knowledge base!

## Features

### 🎯 Core Features
- ✅ Drag-and-drop file upload
- ✅ Automatic text extraction and processing
- ✅ AI-powered embeddings (100% local, free)
- ✅ Vector search with Qdrant
- ✅ Multiple document formats (PDF, DOCX, TXT, MD, HTML)
- ✅ Real-time service monitoring
- ✅ System tray integration

### 🤖 AI Capabilities
- ✅ Semantic document search
- ✅ Natural language queries
- ✅ Document summarization
- ✅ Multi-provider LLM support (Claude, Gemini, GPT)
- ✅ Local embeddings (no API keys needed)
- ✅ Privacy-first architecture

### 🎨 User Interface
- ✅ Modern, clean GUI
- ✅ Dark theme support
- ✅ Responsive design
- ✅ Live service status
- ✅ Integrated log viewer

## System Requirements

### Minimum
- Windows 10/11, macOS 10.15+, or Ubuntu 20.04+
- 8 GB RAM
- 20 GB disk space
- 4-core CPU
- Docker Desktop 20.10+
- Python 3.11+

### Recommended
- 16 GB RAM
- 50 GB SSD
- 8-core CPU
- GPU (optional, for faster AI processing)

## What's Included

```
In My Head/
├── InMyHead.py                 Main application
├── Start_InMyHead.bat          One-click launcher (Windows)
├── Start_InMyHead.ps1          PowerShell launcher
├── Create_Desktop_Shortcut.ps1 Creates desktop shortcut
├── requirements.txt            Python dependencies
├── DESKTOP_APP_README.md       Detailed documentation
├── INSTALLATION_GUIDE.md       Setup instructions
│
├── infrastructure/
│   └── docker/                 Docker configuration
│       ├── docker-compose.dev.yml
│       └── .env                API keys and settings
│
├── services/                   Microservices
│   ├── document-processor/     Document upload & processing
│   ├── ai-engine/              AI/ML services
│   ├── search-service/         Search functionality
│   └── resource-manager/       Resource management
│
└── docs/                       Documentation
```

## Privacy & Security

### 🔒 Privacy-First
- ✅ All document processing happens locally
- ✅ No data sent to external servers (by default)
- ✅ Local embeddings = zero API calls
- ✅ Your files never leave your machine
- ✅ No telemetry or tracking

### 🔑 Optional AI Features
- Claude, Gemini, or GPT can be used for enhanced AI chat
- API keys are optional (local mode works without them)
- You control which AI providers to use
- Keys stored securely in .env file (never in code)

## Documentation

- **DESKTOP_APP_README.md** - Complete user guide
- **INSTALLATION_GUIDE.md** - Detailed setup instructions
- **API Docs** - http://localhost:8000/docs (when running)

## Support

### Getting Help
- Read INSTALLATION_GUIDE.md for setup issues
- Check DESKTOP_APP_README.md for usage questions
- View logs: Click "View Logs" in application
- Check Docker Desktop logs for service issues

### Common Issues

**"Docker is not running"**
→ Start Docker Desktop before launching

**"Services won't start"**
→ Restart Docker Desktop and try again

**"Upload failed"**
→ Wait for all services to show green checkmark

## Version

**Version**: 1.0.0
**Package Date**: $(Get-Date -Format "yyyy-MM-dd")
**License**: [Your License]

## Credits

Built with:
- PyQt6 (GUI framework)
- Docker (containerization)
- FastAPI (backend API)
- PostgreSQL (database)
- Qdrant (vector search)
- sentence-transformers (local AI)

---

**🧠 In My Head**
*Your Knowledge, Infinitely Connected, Eternally Private, Boundlessly Intelligent*

Made with ❤️ for privacy-conscious knowledge workers
"@
Set-Content -Path (Join-Path $OutputPath "README.md") -Value $readme
Write-Host "   ✓ README.md created" -ForegroundColor Green

# Create version file
$version = @{
    version      = "1.0.0"
    build_date   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    package_type = if ($IncludeVenv) { "full" } else { "standard" }
}
$version | ConvertTo-Json | Set-Content -Path (Join-Path $OutputPath "version.json")

# Summary
Write-Host ""
Write-Host "✅ Package created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Package location: $OutputPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "📦 Package contents:" -ForegroundColor Yellow
Write-Host "   ✓ Application files" -ForegroundColor Green
Write-Host "   ✓ Docker configuration" -ForegroundColor Green
Write-Host "   ✓ All services" -ForegroundColor Green
Write-Host "   ✓ Documentation" -ForegroundColor Green
if ($IncludeVenv) {
    Write-Host "   ✓ Virtual environment" -ForegroundColor Green
}
Write-Host ""
Write-Host "🎁 Ready to distribute!" -ForegroundColor Magenta
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the package in the output folder"
Write-Host "2. Create a ZIP file for distribution"
Write-Host "3. Share with users!"
Write-Host ""

# Ask if user wants to create ZIP
$createZip = Read-Host "Create ZIP file for distribution? (y/n)"
if ($createZip -eq "y" -or $createZip -eq "Y") {
    $zipPath = "$OutputPath.zip"

    Write-Host ""
    Write-Host "🗜️ Creating ZIP file..." -ForegroundColor Yellow

    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }

    Compress-Archive -Path $OutputPath -DestinationPath $zipPath -Force

    $zipSize = (Get-Item $zipPath).Length / 1MB

    Write-Host ""
    Write-Host "✅ ZIP file created!" -ForegroundColor Green
    Write-Host "   Location: $zipPath" -ForegroundColor Cyan
    Write-Host "   Size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
}

Read-Host "Press Enter to close"
