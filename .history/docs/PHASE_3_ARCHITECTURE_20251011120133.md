# 🚀 PHASE 3: DOCUMENT PROCESSING PIPELINE
**Project:** In My Head - Personal Knowledge Management System  
**Phase:** 3 of 12  
**Status:** In Progress  
**Started:** October 11, 2025

---

## 📋 PHASE 3 OVERVIEW

### Objectives
Implement a comprehensive document processing pipeline that can:
1. **Accept multiple document formats** (PDF, DOCX, PPTX, TXT, HTML, Markdown)
2. **Extract and preprocess text** with intelligent chunking
3. **Generate embeddings** using OpenAI ada-002 (with local fallback)
4. **Store vectors** in Qdrant for semantic search
5. **Extract metadata** using AI-powered analysis
6. **Process documents asynchronously** using background jobs

### Success Criteria
- ✅ Support 6+ document formats
- ✅ Process documents asynchronously with progress tracking
- ✅ Generate high-quality embeddings for semantic search
- ✅ Extract rich metadata automatically
- ✅ Handle errors gracefully with retry logic
- ✅ Achieve >90% test coverage
- ✅ Process 100+ documents per minute

---

## 🏗️ ARCHITECTURE DESIGN

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Upload API                       │
│         (FastAPI endpoint with file validation)             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Document Job Queue                          │
│              (Redis + Celery/RQ/Dramatiq)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Document Processing Pipeline                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Format Detection & Validation                     │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 2. Content Extraction (Parser Selection)            │  │
│  │    - PDF → PyPDF2/pdfplumber                        │  │
│  │    - DOCX → python-docx                             │  │
│  │    - PPTX → python-pptx                             │  │
│  │    - TXT → direct read                              │  │
│  │    - HTML → BeautifulSoup4                          │  │
│  │    - Markdown → markdown library                    │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 3. Text Preprocessing                                │  │
│  │    - Clean & normalize text                          │  │
│  │    - Remove noise (headers, footers, ads)           │  │
│  │    - Language detection                              │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 4. Intelligent Chunking                              │  │
│  │    - Semantic chunking (preserve meaning)            │  │
│  │    - Overlap for context continuity                  │  │
│  │    - Chunk size optimization (512 tokens)            │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 5. Embedding Generation                              │  │
│  │    - Primary: OpenAI text-embedding-ada-002         │  │
│  │    - Fallback: sentence-transformers (local)         │  │
│  │    - Batch processing for efficiency                 │  │
│  │    - Caching to reduce API calls                     │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 6. AI Metadata Extraction                            │  │
│  │    - Title, author, date extraction                  │  │
│  │    - Topic modeling & categorization                 │  │
│  │    - Keyword extraction                              │  │
│  │    - Summary generation                              │  │
│  │    - Entity recognition (people, places, orgs)       │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 7. Storage                                           │  │
│  │    - Vectors → Qdrant                                │  │
│  │    - Metadata → PostgreSQL                           │  │
│  │    - Original files → MinIO                          │  │
│  │    - Processing status → Redis                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 COMPONENT SPECIFICATIONS

### 1. Document Parser Service

**Location:** `services/document-processor/src/parsers/`

**Files:**
- `base_parser.py` - Abstract base class for all parsers
- `pdf_parser.py` - PDF extraction (PyPDF2, pdfplumber, PyMuPDF)
- `docx_parser.py` - Word documents (python-docx)
- `pptx_parser.py` - PowerPoint presentations (python-pptx)
- `txt_parser.py` - Plain text files
- `html_parser.py` - HTML documents (BeautifulSoup4)
- `markdown_parser.py` - Markdown files (markdown, mistune)
- `parser_factory.py` - Factory pattern for parser selection

**Features:**
- Automatic format detection using magic numbers
- Fallback parsing strategies
- Metadata extraction (author, creation date, modification date)
- Image extraction and OCR (for PDFs with scanned text)
- Table extraction and preservation
- Link extraction

**Example API:**
```python
from src.parsers import ParserFactory

parser = ParserFactory.get_parser("document.pdf")
result = parser.parse()

# Result structure:
{
    "text": "Full extracted text...",
    "metadata": {
        "title": "Document Title",
        "author": "Author Name",
        "created_at": "2025-01-01T00:00:00",
        "modified_at": "2025-01-15T10:30:00",
        "pages": 10,
        "word_count": 5000
    },
    "images": [...],
    "tables": [...],
    "links": [...]
}
```

---

### 2. Text Preprocessing Service

**Location:** `services/document-processor/src/preprocessing/`

**Files:**
- `text_cleaner.py` - Remove noise, normalize whitespace
- `text_normalizer.py` - Unicode normalization, case handling
- `chunker.py` - Intelligent text chunking
- `deduplicator.py` - Remove duplicate content

**Chunking Strategy:**
- **Target chunk size:** 512 tokens (~2000 characters)
- **Overlap:** 50 tokens (for context continuity)
- **Method:** Semantic chunking (preserve sentence/paragraph boundaries)
- **Special handling:** Code blocks, lists, tables

**Example API:**
```python
from src.preprocessing import TextPreprocessor

preprocessor = TextPreprocessor()
chunks = preprocessor.chunk_text(
    text=raw_text,
    chunk_size=512,
    overlap=50,
    strategy="semantic"
)

# Each chunk:
{
    "text": "Chunk text content...",
    "chunk_id": 0,
    "start_char": 0,
    "end_char": 2000,
    "token_count": 512,
    "metadata": {...}
}
```

---

### 3. Embedding Generation Service

**Location:** `services/ai-engine/src/embeddings/`

**Files:**
- `embedding_service.py` - Main embedding generation service
- `openai_embeddings.py` - OpenAI ada-002 integration
- `local_embeddings.py` - sentence-transformers fallback
- `embedding_cache.py` - Redis-based caching

**Models:**
- **Primary:** OpenAI `text-embedding-ada-002` (1536 dimensions)
- **Fallback:** `all-MiniLM-L6-v2` (384 dimensions, local)
- **Alternative:** `all-mpnet-base-v2` (768 dimensions, local)

**Features:**
- Batch processing (up to 100 texts per API call)
- Automatic retry with exponential backoff
- Cost tracking and monitoring
- Cache hit rate optimization
- Embedding normalization (L2 norm)

**Example API:**
```python
from src.embeddings import EmbeddingService

embedding_service = EmbeddingService(
    provider="openai",
    model="text-embedding-ada-002"
)

# Single embedding
embedding = await embedding_service.generate(text="Sample text")

# Batch embeddings
embeddings = await embedding_service.generate_batch(texts=[...])

# Result:
{
    "embedding": [0.123, -0.456, ...],  # 1536 dimensions
    "model": "text-embedding-ada-002",
    "tokens_used": 10,
    "cached": False
}
```

---

### 4. Qdrant Vector Storage

**Location:** `services/search-service/src/vector_store/`

**Collections:**
```python
# Document chunks collection
{
    "name": "document_chunks",
    "vector_size": 1536,  # OpenAI ada-002
    "distance": "Cosine",
    "payload_schema": {
        "document_id": "str",
        "chunk_id": "int",
        "text": "str",
        "metadata": "json"
    }
}

# Document embeddings collection
{
    "name": "documents",
    "vector_size": 1536,
    "distance": "Cosine",
    "payload_schema": {
        "document_id": "str",
        "title": "str",
        "summary": "str",
        "metadata": "json"
    }
}
```

**Features:**
- HNSW indexing for fast similarity search
- Filtered search (by metadata)
- Batch upsert operations
- Incremental updates
- Snapshot backups

**Example API:**
```python
from src.vector_store import QdrantClient

qdrant = QdrantClient(host="localhost", port=6333)

# Store embeddings
await qdrant.upsert(
    collection_name="document_chunks",
    points=[
        {
            "id": "doc1_chunk0",
            "vector": embedding,
            "payload": {
                "document_id": "doc1",
                "chunk_id": 0,
                "text": "Chunk text...",
                "metadata": {...}
            }
        }
    ]
)

# Search
results = await qdrant.search(
    collection_name="document_chunks",
    query_vector=query_embedding,
    limit=10,
    filter={"document_id": "doc1"}
)
```

---

### 5. AI Metadata Extraction

**Location:** `services/ai-engine/src/metadata/`

**Files:**
- `metadata_extractor.py` - Main extraction service
- `title_extractor.py` - Title and author extraction
- `topic_classifier.py` - Topic modeling
- `keyword_extractor.py` - Keyword extraction
- `summarizer.py` - Document summarization
- `entity_extractor.py` - Named entity recognition

**Extraction Types:**

1. **Basic Metadata:**
   - Title (if not in document metadata)
   - Author/Creator
   - Publication date
   - Language

2. **Content Metadata:**
   - Topics/Categories (hierarchical)
   - Keywords/Tags (ranked by relevance)
   - Summary (100-500 words)
   - Main entities (people, organizations, locations)

3. **Relationship Metadata:**
   - Related documents
   - Citations/References
   - External links

**Example API:**
```python
from src.metadata import MetadataExtractor

extractor = MetadataExtractor(llm_client=claude)

metadata = await extractor.extract_all(
    text=document_text,
    existing_metadata={...}
)

# Result:
{
    "title": "Document Title",
    "author": "Author Name",
    "topics": [
        {"name": "Technology", "confidence": 0.95},
        {"name": "AI/ML", "confidence": 0.87}
    ],
    "keywords": [
        {"keyword": "artificial intelligence", "score": 0.92},
        {"keyword": "machine learning", "score": 0.88}
    ],
    "summary": "This document discusses...",
    "entities": {
        "people": ["John Doe", "Jane Smith"],
        "organizations": ["OpenAI", "Google"],
        "locations": ["San Francisco", "New York"]
    }
}
```

---

### 6. Background Job Processing

**Technology Choice:** **Dramatiq** (preferred) or Celery

**Why Dramatiq:**
- Simpler than Celery
- Better error handling
- Built-in retries
- Good performance
- Redis backend

**Job Types:**

1. **Document Processing Job:**
   ```python
   @dramatiq.actor(max_retries=3, time_limit=300000)
   def process_document(document_id: str, file_path: str):
       # 1. Parse document
       # 2. Preprocess text
       # 3. Generate embeddings
       # 4. Extract metadata
       # 5. Store in Qdrant + PostgreSQL
       # 6. Update job status
       pass
   ```

2. **Batch Processing Job:**
   ```python
   @dramatiq.actor(max_retries=2, time_limit=600000)
   def process_document_batch(document_ids: List[str]):
       # Process multiple documents in parallel
       pass
   ```

3. **Reprocessing Job:**
   ```python
   @dramatiq.actor(max_retries=1)
   def reprocess_document(document_id: str, reason: str):
       # Reprocess failed or outdated documents
       pass
   ```

**Job Status Tracking:**
```python
# Redis keys
job_status:{job_id} = {
    "status": "pending|processing|completed|failed",
    "progress": 45,  # percentage
    "current_step": "embedding_generation",
    "started_at": "2025-10-11T10:00:00",
    "updated_at": "2025-10-11T10:05:00",
    "error": null,
    "result": {...}
}
```

---

## 🗄️ DATABASE SCHEMA

### PostgreSQL Tables

```sql
-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    file_path TEXT NOT NULL,  -- MinIO path
    
    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_job_id VARCHAR(255),
    processing_error TEXT,
    processed_at TIMESTAMP,
    
    -- Content metadata
    title TEXT,
    author VARCHAR(255),
    language VARCHAR(10),
    page_count INTEGER,
    word_count INTEGER,
    
    -- AI-extracted metadata
    summary TEXT,
    topics JSONB,
    keywords JSONB,
    entities JSONB,
    
    -- Vector storage references
    qdrant_collection VARCHAR(100),
    qdrant_point_ids TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    
    -- Indexes
    INDEX idx_documents_user_id (user_id),
    INDEX idx_documents_processing_status (processing_status),
    INDEX idx_documents_file_type (file_type),
    INDEX idx_documents_created_at (created_at),
    INDEX idx_documents_topics USING GIN (topics),
    INDEX idx_documents_keywords USING GIN (keywords)
);

-- Document chunks table
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    
    -- Content
    text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    
    -- Vector storage
    qdrant_point_id VARCHAR(255) NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints and indexes
    UNIQUE(document_id, chunk_index),
    INDEX idx_chunks_document_id (document_id),
    INDEX idx_chunks_qdrant_point_id (qdrant_point_id)
);

-- Processing jobs table
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Progress tracking
    progress INTEGER DEFAULT 0,
    current_step VARCHAR(100),
    
    -- Results and errors
    result JSONB,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    INDEX idx_jobs_document_id (document_id),
    INDEX idx_jobs_status (status),
    INDEX idx_jobs_created_at (created_at)
);
```

---

## 📡 API ENDPOINTS

### Document Upload & Management

```python
# Upload document
POST /api/v1/documents/upload
Content-Type: multipart/form-data

Request:
- file: File (required)
- collection_id: UUID (optional)
- tags: List[str] (optional)
- metadata: JSON (optional)

Response: 201 Created
{
    "document_id": "uuid",
    "filename": "document.pdf",
    "file_size": 1024000,
    "processing_job_id": "uuid",
    "status": "pending",
    "message": "Document uploaded successfully. Processing started."
}

# Get document processing status
GET /api/v1/documents/{document_id}/status

Response: 200 OK
{
    "document_id": "uuid",
    "status": "processing",
    "progress": 45,
    "current_step": "embedding_generation",
    "started_at": "2025-10-11T10:00:00",
    "estimated_completion": "2025-10-11T10:10:00"
}

# List documents
GET /api/v1/documents?page=1&limit=20&status=completed&file_type=pdf

Response: 200 OK
{
    "total": 150,
    "page": 1,
    "limit": 20,
    "documents": [
        {
            "id": "uuid",
            "filename": "document.pdf",
            "title": "Document Title",
            "file_type": "pdf",
            "status": "completed",
            "summary": "Brief summary...",
            "topics": ["AI", "Machine Learning"],
            "created_at": "2025-10-11T09:00:00",
            "processed_at": "2025-10-11T09:05:00"
        },
        ...
    ]
}

# Get document details
GET /api/v1/documents/{document_id}

Response: 200 OK
{
    "id": "uuid",
    "filename": "document.pdf",
    "original_filename": "my_document.pdf",
    "file_type": "pdf",
    "file_size": 1024000,
    "status": "completed",
    
    "metadata": {
        "title": "Document Title",
        "author": "Author Name",
        "language": "en",
        "page_count": 10,
        "word_count": 5000
    },
    
    "ai_metadata": {
        "summary": "This document discusses...",
        "topics": [
            {"name": "Technology", "confidence": 0.95}
        ],
        "keywords": [
            {"keyword": "AI", "score": 0.92}
        ],
        "entities": {
            "people": ["John Doe"],
            "organizations": ["OpenAI"]
        }
    },
    
    "processing": {
        "job_id": "uuid",
        "processed_at": "2025-10-11T09:05:00",
        "processing_time": 300
    },
    
    "created_at": "2025-10-11T09:00:00"
}

# Download original document
GET /api/v1/documents/{document_id}/download

Response: 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="document.pdf"

# Delete document
DELETE /api/v1/documents/{document_id}

Response: 204 No Content

# Reprocess document
POST /api/v1/documents/{document_id}/reprocess

Response: 202 Accepted
{
    "message": "Document reprocessing initiated",
    "job_id": "uuid"
}
```

---

## 🔧 IMPLEMENTATION PLAN

### Phase 3.1: Foundation (Days 1-2)
- [ ] Set up project structure
- [ ] Install dependencies
- [ ] Create database migrations
- [ ] Set up Qdrant collections
- [ ] Configure MinIO for file storage

### Phase 3.2: Document Parsing (Days 3-5)
- [ ] Implement base parser interface
- [ ] Implement PDF parser (PyPDF2, pdfplumber)
- [ ] Implement DOCX parser
- [ ] Implement PPTX parser
- [ ] Implement TXT, HTML, Markdown parsers
- [ ] Create parser factory
- [ ] Add format detection
- [ ] Write unit tests

### Phase 3.3: Text Preprocessing (Days 6-7)
- [ ] Implement text cleaner
- [ ] Implement text normalizer
- [ ] Implement intelligent chunker
- [ ] Add deduplication logic
- [ ] Write unit tests

### Phase 3.4: Embedding Generation (Days 8-9)
- [ ] Set up OpenAI integration
- [ ] Implement local embedding fallback
- [ ] Add embedding cache (Redis)
- [ ] Implement batch processing
- [ ] Add error handling and retries
- [ ] Write unit tests

### Phase 3.5: Vector Storage (Days 10-11)
- [ ] Configure Qdrant collections
- [ ] Implement vector upsert operations
- [ ] Implement similarity search
- [ ] Add filtered search
- [ ] Implement batch operations
- [ ] Write unit tests

### Phase 3.6: AI Metadata Extraction (Days 12-14)
- [ ] Implement title/author extraction
- [ ] Implement topic classification
- [ ] Implement keyword extraction
- [ ] Implement summarization
- [ ] Implement entity recognition
- [ ] Write unit tests

### Phase 3.7: Background Jobs (Days 15-16)
- [ ] Set up Dramatiq/Celery
- [ ] Implement document processing job
- [ ] Implement batch processing job
- [ ] Add job status tracking
- [ ] Implement retry logic
- [ ] Add monitoring and logging
- [ ] Write unit tests

### Phase 3.8: API Endpoints (Days 17-18)
- [ ] Implement upload endpoint
- [ ] Implement status endpoint
- [ ] Implement list endpoint
- [ ] Implement get details endpoint
- [ ] Implement download endpoint
- [ ] Implement delete endpoint
- [ ] Implement reprocess endpoint
- [ ] Add input validation
- [ ] Add authentication/authorization
- [ ] Write API tests

### Phase 3.9: Integration & Testing (Days 19-20)
- [ ] End-to-end integration tests
- [ ] Performance testing
- [ ] Load testing (100+ docs/min)
- [ ] Error scenario testing
- [ ] Fix bugs and issues
- [ ] Code review and refactoring

### Phase 3.10: Documentation & Deployment (Days 21-22)
- [ ] Write API documentation
- [ ] Write user guide
- [ ] Create usage examples
- [ ] Update README
- [ ] Deploy to staging
- [ ] Smoke tests in staging
- [ ] Deploy to production

---

## 📦 DEPENDENCIES

### Python Packages

```txt
# Document parsing
PyPDF2==3.0.1
pdfplumber==0.10.3
PyMuPDF==1.23.8  # fitz
python-docx==1.1.0
python-pptx==0.6.23
beautifulsoup4==4.12.2
markdown==3.5.1
mistune==3.0.2
python-magic==0.4.27  # File type detection

# Text processing
spacy==3.7.2
nltk==3.8.1
langdetect==1.0.9

# Embeddings
openai==1.3.7
sentence-transformers==2.2.2
tiktoken==0.5.2  # Token counting

# Vector storage
qdrant-client==1.7.0

# Background jobs
dramatiq[redis]==1.15.0
# OR
celery[redis]==5.3.4

# File storage
minio==7.2.0

# Utilities
python-multipart==0.0.6  # File uploads
aiofiles==23.2.1  # Async file operations
tenacity==8.2.3  # Retry logic
```

---

## 🎯 SUCCESS METRICS

### Performance Targets
- **Upload speed:** <5 seconds for 10MB files
- **Processing speed:** >100 documents per minute
- **Embedding generation:** <2 seconds per document
- **Search latency:** <200ms (p95)
- **API response time:** <500ms (p95)

### Quality Targets
- **Text extraction accuracy:** >95%
- **Metadata extraction accuracy:** >90%
- **Embedding quality:** Cosine similarity >0.7 for similar docs
- **Test coverage:** >90%
- **Error rate:** <1%

### Reliability Targets
- **Job success rate:** >99%
- **Retry success rate:** >95%
- **Uptime:** 99.9%
- **Data durability:** 99.99%

---

## 🔒 SECURITY CONSIDERATIONS

### File Upload Security
- Validate file types (whitelist)
- Scan for malware (ClamAV)
- Size limits (max 100MB per file)
- Rate limiting (max 10 uploads/minute per user)
- Sanitize filenames

### Data Privacy
- Encrypt files at rest (MinIO)
- Encrypt data in transit (TLS)
- Anonymize sensitive data in logs
- Implement data retention policies
- GDPR compliance (right to deletion)

### API Security
- Authentication (JWT tokens)
- Authorization (RBAC)
- Input validation
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting

---

## 📊 MONITORING & LOGGING

### Metrics to Track
- Documents processed per hour
- Processing time per document
- Embedding generation time
- API request latency
- Error rates by type
- Queue depth
- Worker utilization
- Storage usage

### Logging Strategy
- Structured logging (JSON)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Correlation IDs for request tracing
- Performance logging (timings)
- Error logging with stack traces
- Audit logging (user actions)

### Alerting
- Processing failures
- High error rates
- Slow processing times
- Queue backlog
- Storage approaching limits
- API downtime

---

## 🚀 NEXT STEPS

1. **Review and approve architecture** ✅
2. **Set up development environment**
3. **Install dependencies**
4. **Create database migrations**
5. **Begin Phase 3.1 implementation**

---

**Document Status:** Draft  
**Last Updated:** October 11, 2025  
**Next Review:** After Phase 3.1 completion
