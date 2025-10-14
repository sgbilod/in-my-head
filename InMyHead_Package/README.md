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
3. **Double-click** Start_InMyHead.bat
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

`
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
`

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
**Package Date**: 2025-10-14
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
