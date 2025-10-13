# 🧠 In My Head - Desktop Application

**One-Click AI-Powered Knowledge Management System**

## 🚀 Quick Start

### Prerequisites

1. **Docker Desktop** - Must be running

   - Download: https://www.docker.com/products/docker-desktop

2. **Python 3.11+**
   - Download: https://www.python.org/downloads/

### Installation

1. **Download the Application**

   - Clone this repository or download the ZIP file
   - Extract to your desired location

2. **Launch the Application**

   **Option A: Double-Click (Windows)**

   ```
   Double-click: Start_InMyHead.bat
   ```

   **Option B: PowerShell (Windows)**

   ```powershell
   .\Start_InMyHead.ps1
   ```

   **Option C: Direct Python (All Platforms)**

   ```bash
   python InMyHead.py
   ```

## ✨ Features

### 🖱️ Drag-and-Drop File Upload

- Simply drag files into the application window
- Supports all document types (PDF, DOCX, TXT, MD, etc.)
- Batch upload multiple files at once
- Visual upload progress

### 📊 Real-Time Service Monitoring

- See the status of all services at a glance
- PostgreSQL Database status
- Redis Cache status
- Qdrant Vector Database status
- Document Processor API status

### 🌐 Integrated Web Interface

- One-click access to the web API
- Full-featured document management
- AI-powered search and chat
- OpenAPI documentation

### 📝 System Tray Integration

- Minimize to system tray
- Quick access menu
- Background service monitoring
- No need to keep window open

### 🎨 Modern UI

- Clean, intuitive interface
- Dark/light theme support
- Responsive design
- Professional styling

## 📁 Application Structure

```
In My Head/
│
├── InMyHead.py              # Main desktop application
├── Start_InMyHead.bat       # Windows batch launcher
├── Start_InMyHead.ps1       # PowerShell launcher
│
├── infrastructure/
│   └── docker/
│       ├── docker-compose.dev.yml
│       └── .env             # Configuration (API keys)
│
├── services/
│   ├── document-processor/  # Document upload & processing
│   ├── ai-engine/          # AI/ML services
│   ├── search-service/     # Search functionality
│   └── resource-manager/   # Resource management
│
└── venv/                   # Python virtual environment (auto-created)
```

## 🎯 Usage Guide

### First Time Setup

1. **Start Docker Desktop**

   - Ensure Docker Desktop is running before launching the app

2. **Launch the Application**

   - Use any of the launch methods above
   - Wait for all services to start (30-60 seconds)
   - Green checkmarks indicate services are ready

3. **Upload Documents**

   - Drag files into the drop zone, OR
   - Click "Browse Files" to select files
   - Click "Upload Files" to process

4. **Access Web Interface**
   - Click "Open Web Interface" button
   - Opens in your default browser
   - Full API documentation available

### Daily Usage

1. **Quick Start**

   - Double-click `Start_InMyHead.bat`
   - Application starts automatically
   - All services launch in background

2. **Upload Documents**

   - Drag & drop files anytime
   - No file size limits
   - Automatic processing

3. **Minimize to Tray**

   - Close window to minimize
   - Right-click tray icon for menu
   - Services keep running

4. **Shutdown**
   - Right-click tray icon → "Quit"
   - Or click X and confirm shutdown
   - All services stop gracefully

## 🔧 Configuration

### API Keys

Edit `infrastructure/docker/.env`:

```env
# Embedding Provider (local = free, private)
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-MiniLM-L6-v2

# LLM Provider (optional)
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your-claude-api-key
GOOGLE_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key

# Privacy Settings
PRIVACY_MODE=false
LOG_API_CALLS=true
```

### Service Ports

Default ports (change in `docker-compose.dev.yml` if needed):

- **PostgreSQL**: 5432
- **Redis**: 6379
- **Qdrant**: 6333 (HTTP), 6334 (gRPC)
- **Document Processor**: 8000
- **AI Engine**: 8001
- **Search Service**: 8002

## 🐛 Troubleshooting

### "Docker is not running"

**Solution**: Start Docker Desktop before launching the app

### "Services won't start"

**Solutions**:

1. Check Docker Desktop is running
2. Ensure ports are not in use
3. View logs: Click "View Logs" button
4. Restart Docker Desktop

### "Upload failed"

**Solutions**:

1. Wait for all services to show green checkmark
2. Check file permissions
3. Verify Document Processor status (should be "Running")

### "Application won't start"

**Solutions**:

1. Verify Python 3.11+ is installed: `python --version`
2. Delete `venv` folder and try again
3. Run as administrator (Windows)

### View Detailed Logs

```powershell
# View Docker logs
cd infrastructure/docker
docker-compose -f docker-compose.dev.yml logs

# View specific service logs
docker logs inmyhead-document-processor
```

## 📊 System Requirements

### Minimum

- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **RAM**: 8 GB
- **Disk**: 20 GB free space
- **CPU**: 4 cores
- **Docker**: 20.10+
- **Python**: 3.11+

### Recommended

- **RAM**: 16 GB
- **Disk**: 50 GB SSD
- **CPU**: 8 cores
- **GPU**: Optional (for faster AI processing)

## 🎨 Customization

### Change Theme Colors

Edit `InMyHead.py` and modify the color values:

```python
# Header gradient
stop:0 #667eea, stop:1 #764ba2

# Button colors
background-color: #4a90e2  # Primary blue
background-color: #28a745  # Success green
background-color: #dc3545  # Danger red
```

### Add Custom Services

1. Add service to `docker-compose.dev.yml`
2. Add status label in `InMyHeadApp.__init__`
3. Add health check in `ServiceManager.monitor_services`

## 🔒 Security & Privacy

### Local-First Architecture

- All document processing happens locally
- No data sent to external servers (unless configured)
- Embeddings generated on your machine
- Full control over your data

### API Keys

- Stored in `.env` file (git-ignored)
- Never hardcoded in application
- Optional - local mode works without them

### Network

- Services only accessible on localhost
- No external connections by default
- Firewall-friendly

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs
- **Architecture**: See `docs/` folder
- **GitHub**: [Your Repository URL]

## 🆘 Support

### Get Help

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check `docs/` folder
- **Logs**: Use "View Logs" button in app

### Common Issues

See "Troubleshooting" section above

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

Built with:

- **PyQt6** - Modern GUI framework
- **Docker** - Container platform
- **FastAPI** - High-performance API framework
- **Qdrant** - Vector search engine
- **PostgreSQL** - Reliable database

---

**Made with ❤️ for privacy-conscious knowledge management**

🧠 **In My Head** - Your Knowledge, Infinitely Connected, Eternally Private, Boundlessly Intelligent
