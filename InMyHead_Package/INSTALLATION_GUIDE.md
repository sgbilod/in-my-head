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

`nv
# For AI features (optional)
ANTHROPIC_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here

# Local embeddings work without API keys
EMBEDDING_PROVIDER=local
`

## Uninstallation

1. Stop the application (Right-click tray icon → Quit)
2. Stop Docker containers:
   `
   cd infrastructure/docker
   docker-compose -f docker-compose.dev.yml down -v
   `
3. Delete the application folder
4. Delete Docker images (optional):
   `
   docker system prune -a
   `

## Support

For issues, feature requests, or questions:
- Check DESKTOP_APP_README.md
- View application logs (View Logs button)
- Check Docker Desktop logs

## Version Information

Package Date: 2025-10-14
Application Version: 1.0.0

---

🧠 In My Head - Your Private AI Knowledge Management System
