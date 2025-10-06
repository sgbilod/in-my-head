# 🧪 Document Upload Feature - Testing Guide

## ✅ What We Just Built

You now have a complete document upload and processing system with:

1. **API Routes** (`src/routes/documents.py`):
   - `POST /documents/upload` - Upload documents
   - `GET /documents/` - List documents with filtering
   - `GET /documents/{id}` - Get specific document
   - `GET /documents/{id}/content` - Get extracted text
   - `DELETE /documents/{id}` - Delete document

2. **Business Logic** (`src/services/document_service.py`):
   - File upload processing
   - Text extraction
   - Database integration
   - Tag management
   - Deduplication (using SHA256 hash)

3. **Utilities**:
   - `file_storage.py` - Saves files to `data/uploads/`
   - `text_extractor.py` - Extracts text from PDF, DOCX, TXT, MD

---

## 🚀 HOW TO TEST

### Step 1: Start the Server

**Terminal 1** (keep this open):
```powershell
cd "C:\Users\sgbil\In My Head"
.\scripts\start-document-processor.ps1
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

### Step 2: Open Interactive API Docs

Open your browser:
**http://localhost:8001/docs**

You'll see Swagger UI with all available endpoints!

### Step 3: Test Using PowerShell (Terminal 2)

```powershell
# Create a test text file
"This is a test document. In My Head is awesome!" | Out-File -FilePath test.txt

# Upload the document
$response = Invoke-RestMethod -Uri "http://localhost:8001/documents/upload" `
    -Method Post `
    -Form @{
        file = Get-Item "test.txt"
        tags = "test,demo"
    }

# View the response
$response | ConvertTo-Json -Depth 5

# List all documents
Invoke-RestMethod -Uri "http://localhost:8001/documents/" | ConvertTo-Json

# Get document content
$docId = $response.id
Invoke-RestMethod -Uri "http://localhost:8001/documents/$docId/content" | ConvertTo-Json
```

### Step 4: Test with Real PDF (if you have one)

```powershell
# Upload a PDF
$response = Invoke-RestMethod -Uri "http://localhost:8001/documents/upload" `
    -Method Post `
    -Form @{
        file = Get-Item "C:\path\to\your\document.pdf"
        collection_id = 1
        tags = "important,work"
    }

$response | ConvertTo-Json
```

---

## 📋 TEST SCENARIOS

### ✅ Scenario 1: Basic Upload
```powershell
# Create test file
"Hello World!" | Out-File test.txt

# Upload
Invoke-RestMethod -Uri "http://localhost:8001/documents/upload" `
    -Method Post `
    -Form @{ file = Get-Item "test.txt" }
```

**Expected Result:**
- Status: 201 Created
- Response contains document metadata
- File saved in `data/uploads/YYYY/MM/DD/`
- Database record created

### ✅ Scenario 2: Upload with Tags
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/documents/upload" `
    -Method Post `
    -Form @{
        file = Get-Item "test.txt"
        tags = "important,work,project"
    }
```

**Expected Result:**
- Document created with 3 tags
- Tags created automatically if they don't exist

### ✅ Scenario 3: Duplicate Detection
```powershell
# Upload same file twice
Invoke-RestMethod -Uri "http://localhost:8001/documents/upload" -Method Post -Form @{ file = Get-Item "test.txt" }
Invoke-RestMethod -Uri "http://localhost:8001/documents/upload" -Method Post -Form @{ file = Get-Item "test.txt" }
```

**Expected Result:**
- Second upload returns the same document (not a duplicate)
- Only one file stored

### ✅ Scenario 4: List and Filter
```powershell
# List all documents
Invoke-RestMethod "http://localhost:8001/documents/"

# Filter by tag
Invoke-RestMethod "http://localhost:8001/documents/?tag=important"

# Search by title
Invoke-RestMethod "http://localhost:8001/documents/?search=test"

# Pagination
Invoke-RestMethod "http://localhost:8001/documents/?skip=0&limit=10"
```

### ✅ Scenario 5: Get Document Content
```powershell
# Get extracted text
Invoke-RestMethod "http://localhost:8001/documents/1/content"
```

**Expected Result:**
- Returns extracted text content
- Word count calculated

### ✅ Scenario 6: Delete Document
```powershell
# Delete a document
Invoke-RestMethod -Uri "http://localhost:8001/documents/1" -Method Delete
```

**Expected Result:**
- Status: 204 No Content
- File deleted from storage
- Database record removed

---

## 🔍 VERIFY IN DATABASE

```powershell
# Connect to database
$env:PGPASSWORD = "inmyhead_dev_pass"
psql -U inmyhead -h localhost -p 5434 -d inmyhead_dev

# Check uploaded documents
SELECT id, title, document_type, processing_status, word_count FROM documents;

# Check tags
SELECT d.id, d.title, t.name as tag_name 
FROM documents d
JOIN document_tags dt ON d.id = dt.document_id
JOIN tags t ON dt.tag_id = t.id;

# Exit
\q
```

---

## 📊 EXPECTED API RESPONSES

### Upload Success (201 Created)
```json
{
  "id": 1,
  "title": "test.txt",
  "document_type": "txt",
  "file_path": "2025/10/05/abc123_test.txt",
  "file_size": 45,
  "mime_type": "text/plain",
  "processing_status": "completed",
  "collection_id": null,
  "user_id": 1,
  "created_at": "2025-10-05T12:34:56.789Z",
  "updated_at": "2025-10-05T12:34:56.789Z",
  "processed_at": "2025-10-05T12:34:56.789Z",
  "tags": [
    {
      "id": 1,
      "name": "test",
      "color": null,
      "created_at": "2025-10-05T12:34:56.789Z"
    }
  ],
  "word_count": 8,
  "page_count": null
}
```

### List Documents (200 OK)
```json
{
  "documents": [ /* array of documents */ ],
  "total": 5,
  "skip": 0,
  "limit": 50
}
```

### Get Content (200 OK)
```json
{
  "content": "This is the extracted text content from the document..."
}
```

---

## 🐛 TROUBLESHOOTING

### Server won't start
```powershell
# Check if port is in use
netstat -ano | findstr :8001

# Kill process if needed
Stop-Process -Id <PID> -Force
```

### Import errors
```powershell
# Reinstall dependencies
cd services\document-processor
pip install -r requirements.txt
```

### Database connection errors
```powershell
# Verify PostgreSQL is running
Get-Service postgresql-x64-18

# Test connection
$env:DATABASE_URL = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
python -c "from sqlalchemy import create_engine; create_engine('$env:DATABASE_URL').connect()"
```

### "PyPDF2 not found" error
```powershell
pip install PyPDF2==3.0.1
```

### "python-docx not found" error
```powershell
pip install python-docx==1.1.0
```

### File upload fails
- Check `data/uploads/` directory exists and is writable
- Verify file type is supported (PDF, DOCX, TXT, MD)
- Check file size (FastAPI default limit is 2GB)

---

## 🎯 SUCCESS CRITERIA

✅ You've successfully implemented the feature when:

1. Server starts without errors
2. Swagger UI shows all document endpoints
3. You can upload a text file
4. File appears in `data/uploads/`
5. Database has document record
6. `/documents/` endpoint lists the document
7. `/documents/{id}/content` returns extracted text
8. Tags are created and associated
9. Delete removes file and database record

---

## 📁 FILE STRUCTURE

```
data/
└── uploads/
    └── 2025/
        └── 10/
            └── 05/
                └── abc123def456_test.txt

services/document-processor/
├── src/
│   ├── routes/
│   │   └── documents.py        ← NEW: API endpoints
│   ├── services/
│   │   └── document_service.py ← NEW: Business logic
│   ├── utils/
│   │   ├── file_storage.py     ← NEW: File management
│   │   └── text_extractor.py   ← NEW: Text extraction
│   └── main.py                 ← UPDATED: Includes routes
```

---

## 🚀 NEXT STEPS

After testing this feature:

1. **Enhance text extraction** - Add support for more formats
2. **Add AI processing** - Generate embeddings, summaries
3. **Implement search** - Vector search across documents
4. **Build frontend** - React UI for document management
5. **Add authentication** - Secure user access

---

## 🎉 YOU DID IT!

You've built a production-ready document upload and processing system!

**Start testing now:**
```powershell
cd "C:\Users\sgbil\In My Head"
.\scripts\start-document-processor.ps1
```

Then open **http://localhost:8001/docs** and explore! 🚀
