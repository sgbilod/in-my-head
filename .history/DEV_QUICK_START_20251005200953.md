# 🚀 DEVELOPMENT QUICK START

**Your "In My Head" development environment is ready!**

---

## ✅ What's Ready

- ✅ **Database:** PostgreSQL 18 on port 5434
- ✅ **Schema:** 16 tables deployed
- ✅ **Python:** 3.13 with all dependencies
- ✅ **FastAPI:** Document processor service configured
- ✅ **Project Structure:** Flattened and organized

---

## 🎯 Start Development (3 Commands)

### 1. Start Document Processor API

```powershell
cd "C:\Users\sgbil\In My Head"
.\scripts\start-document-processor.ps1
```

This starts the FastAPI backend on **http://localhost:8001**

**Available endpoints:**

- **http://localhost:8001** - API root
- **http://localhost:8001/docs** - Interactive API documentation (Swagger UI)
- **http://localhost:8001/health** - Health check
- **http://localhost:8001/metrics** - Prometheus metrics

### 2. Test the API (in new terminal)

```powershell
# Check health
Invoke-RestMethod http://localhost:8001/health

# View API docs in browser
Start-Process http://localhost:8001/docs
```

### 3. Start Frontend (when ready)

```powershell
cd frontend
npm install
npm run dev
```

---

## 📁 Project Structure

```
C:\Users\sgbil\In My Head\
├── services\
│   ├── document-processor\    ← FastAPI backend (port 8001)
│   ├── api-gateway\            ← API gateway (port 8000)
│   ├── ai-engine\              ← AI processing service
│   ├── search-service\         ← Vector search service
│   └── resource-manager\       ← Resource management service
├── frontend\                   ← React frontend
├── infrastructure\
│   └── docker\                 ← Docker configurations
├── scripts\                    ← Utility scripts
└── docs\                       ← Documentation
```

---

## 🔧 Development Commands

### Database

```powershell
# Connect to database
$env:PGPASSWORD = "inmyhead_dev_pass"
psql -U inmyhead -h localhost -p 5434 -d inmyhead_dev

# Run migrations
cd services\document-processor
$env:DATABASE_URL = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
python -m alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### Testing

```powershell
# Run tests
cd services\document-processor
pytest

# With coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```powershell
# Format code
black src/
flake8 src/
mypy src/
```

---

## 🎨 Next Development Steps

### Phase 1: Core Document Processing (Current)

- [x] Database setup complete
- [x] FastAPI service running
- [ ] Implement document upload endpoint
- [ ] Add PDF processing
- [ ] Add DOCX processing
- [ ] Add text extraction

### Phase 2: AI Integration

- [ ] Integrate Claude/GPT for processing
- [ ] Implement embedding generation
- [ ] Set up vector database (Qdrant)
- [ ] Create semantic search

### Phase 3: Frontend Development

- [ ] Set up React app
- [ ] Create document upload UI
- [ ] Build search interface
- [ ] Add AI chat interface

### Phase 4: Advanced Features

- [ ] Knowledge graph generation
- [ ] Multi-modal processing (audio/video)
- [ ] Resource auto-discovery
- [ ] Advanced analytics

---

## 📖 Key Files to Know

### Backend Configuration

- **`.env`** - Environment variables (database URL, API keys)
- **`services/document-processor/src/main.py`** - FastAPI application entry point
- **`services/document-processor/requirements.txt`** - Python dependencies
- **`services/document-processor/alembic/`** - Database migrations

### Database Models

- **`services/document-processor/src/models/database.py`** - SQLAlchemy ORM models

### API Routes (to be implemented)

- **`services/document-processor/src/routes/`** - API endpoint handlers

---

## 🐛 Troubleshooting

### Server won't start

```powershell
# Check if port is in use
netstat -ano | findstr :8001

# Kill process using port (replace PID)
Stop-Process -Id <PID> -Force
```

### Database connection issues

```powershell
# Verify PostgreSQL is running
Get-Service postgresql-x64-18

# Test connection
$env:PGPASSWORD = "inmyhead_dev_pass"
psql -U inmyhead -h localhost -p 5434 -d inmyhead_dev -c "SELECT version();"
```

### Import errors

```powershell
# Reinstall dependencies
cd services\document-processor
pip install -r requirements.txt --force-reinstall
```

---

## 🎯 Your First Feature: Document Upload

Let's implement your first feature! Here's what you'll build:

### 1. Create Upload Endpoint

**File:** `services/document-processor/src/routes/documents.py`

```python
from fastapi import APIRouter, UploadFile, File
from src.services.document_service import process_document

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    result = await process_document(file)
    return result
```

### 2. Add Document Processing Logic

**File:** `services/document-processor/src/services/document_service.py`

```python
async def process_document(file: UploadFile):
    # Save file
    # Extract content
    # Store in database
    # Return metadata
    pass
```

### 3. Test It

```powershell
# Upload a document
$file = Get-Item "test.pdf"
Invoke-RestMethod -Uri http://localhost:8001/documents/upload `
    -Method Post `
    -Form @{ file = $file }
```

---

## 📚 Resources

### Documentation

- **FastAPI:** https://fastapi.tiangolo.com/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Alembic:** https://alembic.sqlalchemy.org/
- **PostgreSQL:** https://www.postgresql.org/docs/

### Project Documentation

- **`README.md`** - Project overview
- **`MIGRATION_GUIDE.md`** - Setup instructions
- **`DATABASE_SETUP_SUCCESS.md`** - Database details
- **`INSTRUCTIONS.md`** - Development guidelines

---

## 🎉 You're Ready to Code!

Your development environment is fully configured. Start the server and begin building features!

```powershell
# Start coding!
cd "C:\Users\sgbil\In My Head"
.\scripts\start-document-processor.ps1
```

Then open http://localhost:8001/docs in your browser and explore the API!

**Happy coding! 🚀**
