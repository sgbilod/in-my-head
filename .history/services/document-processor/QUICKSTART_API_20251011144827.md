# Phase 3.8 - Quick Start Guide

## 🚀 Starting the API Server

### Prerequisites

1. **Redis** - Must be running

   ```powershell
   # Check if running
   Test-NetConnection localhost -Port 6379
   ```

2. **Qdrant** - Should be running (optional for basic functionality)

   ```powershell
   # Check if running
   Test-NetConnection localhost -Port 6333
   ```

3. **Celery Workers** - Must be running for background processing
   ```powershell
   .\start_celery_workers.ps1
   ```

### Start Server

```powershell
# Simple start
.\start_api_server.ps1

# Or manually
cd "c:\Users\sgbil\In My Head\services\document-processor"
$env:API_KEYS = "test-api-key-123"
python -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 API Endpoints

### Base URL

```
http://localhost:8000
```

### Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI**: http://localhost:8000/openapi.json

### Health Check

```bash
curl http://localhost:8000/health
```

## 🔑 Authentication

All API endpoints require API key in header:

```bash
curl -H "X-API-Key: test-api-key-123" http://localhost:8000/api/v1/statistics
```

Default API key for testing: `test-api-key-123`

## 📤 Upload Document

### Single Document

**Python:**

```python
import requests

files = {"file": open("document.pdf", "rb")}
headers = {"X-API-Key": "test-api-key-123"}

response = requests.post(
    "http://localhost:8000/api/v1/documents",
    files=files,
    headers=headers,
)

job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")
```

**cURL:**

```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "X-API-Key: test-api-key-123" \
  -F "file=@document.pdf"
```

### Batch Upload

**Python:**

```python
files = [
    ("files", open("doc1.pdf", "rb")),
    ("files", open("doc2.docx", "rb")),
]

response = requests.post(
    "http://localhost:8000/api/v1/documents/batch",
    files=files,
    headers={"X-API-Key": "test-api-key-123"}
)

job_ids = response.json()["job_ids"]
```

## 📊 Check Job Status

**Python:**

```python
response = requests.get(
    f"http://localhost:8000/api/v1/jobs/{job_id}",
    headers={"X-API-Key": "test-api-key-123"}
)

status = response.json()
print(f"Status: {status['status']}")
print(f"Progress: {status['progress']}")
```

**cURL:**

```bash
curl -H "X-API-Key: test-api-key-123" \
  "http://localhost:8000/api/v1/jobs/{job_id}"
```

## 🔍 Search Documents

**Python:**

```python
data = {
    "query": "machine learning",
    "topics": ["AI", "technology"],
    "limit": 10
}

response = requests.post(
    "http://localhost:8000/api/v1/search",
    json=data,
    headers={"X-API-Key": "test-api-key-123"}
)

results = response.json()["results"]
for result in results:
    print(f"Score: {result['score']}")
    print(f"Text: {result['text'][:100]}")
```

## 🌐 WebSocket Monitoring

### JavaScript

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/jobs/abc123');

ws.onopen = () => console.log('Connected');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Type: ${data.type}`);
  console.log(`Data:`, data.data);
};

ws.onerror = (error) => console.error('Error:', error);
ws.onclose = () => console.log('Disconnected');
```

### Python

```python
import asyncio
import websockets
import json

async def monitor(job_id):
    uri = f"ws://localhost:8000/api/v1/ws/jobs/{job_id}"

    async with websockets.connect(uri) as ws:
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"{data['type']}: {data['data']}")

            if data['type'] in ['result', 'error']:
                break

asyncio.run(monitor("abc123"))
```

### Test Page

Open browser: http://localhost:8000/api/v1/ws/test

## 🧪 Running Demos

```powershell
# Complete demo suite
cd "c:\Users\sgbil\In My Head\services\document-processor"
python examples\api_demo.py
```

Demos include:

1. Upload single document
2. Upload batch
3. Search documents
4. WebSocket monitoring
5. Statistics
6. Health check

## 📈 Rate Limits

| Endpoint      | Cost | Limit   |
| ------------- | ---- | ------- |
| Upload single | 5    | 100/min |
| Upload batch  | 10   | 100/min |
| Search        | 2    | 100/min |
| Others        | 1    | 100/min |

## 🔧 Environment Variables

```powershell
$env:API_KEYS = "key1,key2,key3"
$env:RATE_LIMIT_REQUESTS = "100"
$env:RATE_LIMIT_WINDOW = "60"
$env:CORS_ORIGINS = "*"
$env:PORT = "8000"
```

## 🐛 Troubleshooting

### "API key is required"

Add API key header: `-H "X-API-Key: test-api-key-123"`

### "Rate limit exceeded"

Wait for rate limit window to reset (default: 60 seconds)

### "Redis connection failed"

Start Redis: Check if running on localhost:6379

### "Job not found"

Job may have expired (24 hour TTL) or invalid job_id

### "File type not supported"

Check allowed extensions: .pdf, .docx, .txt, .html, .md, .json, etc.

## 📚 Full Documentation

See: `PHASE_3_8_COMPLETE.md`

## ✅ Quick Test

```bash
# Test health
curl http://localhost:8000/health

# Test auth (should fail)
curl http://localhost:8000/api/v1/statistics

# Test with key (should work)
curl -H "X-API-Key: test-api-key-123" \
  http://localhost:8000/api/v1/statistics
```

## 🎯 Next Steps

1. Upload some documents
2. Monitor via WebSocket
3. Search your documents
4. Check statistics
5. Explore Swagger UI: http://localhost:8000/docs
