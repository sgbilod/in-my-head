# 🔧 ENDPOINT FIXES - Investigation & Resolution

**Date:** October 12, 2025  
**Time:** 4:18 PM  
**Status:** ✅ Fixes Implemented (User Action Required)

---

## 📋 Issues Investigated

### Issue 1: Document List Endpoint (HTTP 500) ✅ FIXED

**Endpoint:** `GET /documents/`  
**Error:** Internal Server Error (500)

### Issue 2: RAG Query Validation (HTTP 422) ✅ FIXED

**Endpoint:** `POST /rag/query`  
**Error:** Unprocessable Entity (422) - Validation Error

---

## 🔍 ROOT CAUSE ANALYSIS

### Issue 1: Missing OPENAI_API_KEY Environment Variable

**Error Stack Trace:**

```python
openai.OpenAIError: The api_key client option must be set either by
passing api_key to the client or by setting the OPENAI_API_KEY
environment variable
```

**Root Cause:**

- Document Processor's `ai_service.py` initializes `AIService()`
- With sentence-transformers unavailable, it falls back to OpenAI API
- OpenAI client requires `OPENAI_API_KEY` environment variable
- Variable was missing from docker-compose configuration

**Impact:**

- Every request to Document Processor that initializes `DocumentService`
- This includes `/documents/` list endpoint
- Service fails during initialization, returns 500 error

**Why It Happened:**

- AI Engine had `OPENAI_API_KEY` configured ✅
- Document Processor did NOT have it configured ❌
- Our smart fix (optional sentence-transformers) requires OpenAI fallback
- Environment variable was overlooked when applying fixes

---

### Issue 2: Incorrect Request Field Name

**Error:** HTTP 422 Validation Error

**Root Cause:**

- Test sent: `{"question": "What is machine learning?"}`
- API expects: `{"query": "...", "top_k": 5}`
- Field name mismatch: `question` vs `query`

**Pydantic Schema (from rag.py):**

```python
class RetrieveRequest(BaseModel):
    query: str = Field(..., description="User query", min_length=1)
    top_k: int = Field(default=5, ...)
    use_reranking: bool = Field(default=True, ...)
    collection_name: str = Field(default="chunk_embeddings", ...)
```

**Why It Happened:**

- Test was written before examining actual API schema
- Natural assumption that field would be called `question`
- API uses more generic `query` field name

---

## ✅ FIXES IMPLEMENTED

### Fix 1: Add OPENAI_API_KEY to Docker Compose

**File:** `infrastructure/docker/docker-compose.dev.yml`

**Changes Made:**

```yaml
document-processor:
  environment:
    - PYTHONUNBUFFERED=1
    - LOG_LEVEL=DEBUG
    - POSTGRES_URL=postgresql://...
    - REDIS_URL=redis://redis:6379
    - MINIO_ENDPOINT=minio:9000
    - MINIO_ACCESS_KEY=inmyhead
    - MINIO_SECRET_KEY=inmyhead_dev_pass_change_in_prod
    - MINIO_SECURE=false
    - OPENAI_API_KEY=${OPENAI_API_KEY} # ✅ ADDED THIS LINE
```

**Status:** ✅ Configuration Updated

---

### Fix 2: Update Test to Use Correct Field Names

**File:** `test_e2e_integration.py`

**Changes Made:**

```python
# Before:
response = requests.post(
    f"{self.services['ai_engine']}/rag/query",
    json={"question": "What is machine learning?"},  # ❌ Wrong field
    timeout=10
)

# After:
response = requests.post(
    f"{self.services['ai_engine']}/rag/query",
    json={
        "query": "What is machine learning?",  # ✅ Correct field
        "top_k": 5                             # ✅ Added parameter
    },
    timeout=10
)
```

**Status:** ✅ Test Updated

---

## 🚨 USER ACTION REQUIRED

### You Need to Configure OpenAI API Key

The fixes are implemented, but **you need to provide your OpenAI API key** for the services to work.

### Option 1: Create .env File (RECOMMENDED)

**Step 1:** Create file at `infrastructure/docker/.env`:

```bash
# infrastructure/docker/.env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

**Step 2:** Get your API key from:
https://platform.openai.com/api-keys

**Step 3:** Restart services:

```powershell
cd "C:\Users\sgbil\In My Head\infrastructure\docker"
docker-compose -f docker-compose.dev.yml restart document-processor
```

### Option 2: Set Environment Variable

**PowerShell:**

```powershell
$env:OPENAI_API_KEY = "sk-your-actual-openai-api-key-here"
cd "C:\Users\sgbil\In My Head\infrastructure\docker"
docker-compose -f docker-compose.dev.yml restart document-processor
```

**Note:** This only lasts for the current PowerShell session.

### Option 3: System Environment Variable (Permanent)

1. Open Windows Settings
2. Search "Environment Variables"
3. Click "Edit system environment variables"
4. Click "Environment Variables" button
5. Under "User variables", click "New"
6. Variable name: `OPENAI_API_KEY`
7. Variable value: `sk-your-actual-openai-api-key-here`
8. Click OK
9. Restart PowerShell
10. Restart Docker services

---

## ✅ VERIFICATION STEPS

After configuring your OpenAI API key:

### Step 1: Restart Document Processor

```powershell
cd "C:\Users\sgbil\In My Head\infrastructure\docker"
docker-compose -f docker-compose.dev.yml restart document-processor
```

### Step 2: Wait for Service to Start (15 seconds)

```powershell
Start-Sleep -Seconds 15
```

### Step 3: Test Document List Endpoint

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/documents/" -Method Get
```

**Expected:** Should return JSON (empty array or list of documents, not 500 error)

### Step 4: Run Full Integration Tests

```powershell
cd "C:\Users\sgbil\In My Head"
python test_e2e_integration.py
```

**Expected Results:**

- Document List endpoint: ✅ PASS
- RAG Query endpoint: ✅ PASS (if there are documents) or specific error
- Overall score: 16/21 or better (up from 14/21)

---

## 📊 EXPECTED IMPACT

### Before Fixes

- **Document List:** ❌ HTTP 500 (Internal Server Error)
- **RAG Query:** ❌ HTTP 422 (Validation Error)
- **Test Score:** 14/21 (66.7%)

### After Fixes + API Key

- **Document List:** ✅ HTTP 200 (Empty list or documents)
- **RAG Query:** ✅ HTTP 200 or specific error (not validation)
- **Test Score:** 16/21 (76.2%) or better

### Potential Remaining Issues

Once API key is configured, you might see:

- RAG Query: Might fail if no documents are indexed (expected)
- Document List: Might return empty array (expected - no documents yet)

These are **expected behaviors**, not errors.

---

## 🎯 SUMMARY

### What Was Fixed ✅

1. **Document Processor Configuration:** Added OPENAI_API_KEY to environment
2. **Test Field Names:** Changed `question` → `query`, added `top_k`
3. **Documentation:** Created .env.template for reference

### What You Need to Do 🎯

1. **Get OpenAI API Key** from https://platform.openai.com/api-keys
2. **Configure API Key** using one of the 3 options above
3. **Restart Services** to apply changes
4. **Run Tests** to verify fixes

### Estimated Time ⏱️

- Getting API key: 2 minutes
- Configuring: 1 minute
- Restarting services: 30 seconds
- Testing: 15 seconds
- **Total: ~4 minutes**

---

## 📝 FILES MODIFIED

1. ✅ `infrastructure/docker/docker-compose.dev.yml`

   - Added OPENAI_API_KEY environment variable

2. ✅ `test_e2e_integration.py`

   - Updated RAG query test to use correct fields

3. ✅ `infrastructure/docker/.env.template`
   - Created template for user reference

---

## 🎉 NEXT STEPS

After you configure your OpenAI API key:

1. **Verify Fixes:**

   - Run integration tests
   - Confirm both endpoints pass

2. **Test Document Upload:**

   - Upload a sample PDF
   - Verify end-to-end pipeline

3. **Deploy Frontend:**
   - Move to Phase 8
   - Connect UI to API Gateway

---

## 💡 IMPORTANT NOTES

### API Key Security 🔒

- **NEVER commit .env files to git**
- Add `.env` to `.gitignore`
- Use different keys for development/production
- Rotate keys regularly

### Cost Considerations 💰

- OpenAI API charges per token
- Text embeddings: ~$0.0001 per 1K tokens
- GPT-4 responses: ~$0.01-0.06 per 1K tokens
- Monitor usage at: https://platform.openai.com/usage

### Alternative: Free Tier Testing 🆓

If you don't have an OpenAI API key:

- Create free account (first few months may have credits)
- Or use local sentence-transformers (requires installing heavy packages)
- Or skip AI features for now (test infrastructure only)

---

**Status:** ✅ **FIXES READY - USER ACTION REQUIRED**  
**Blocker:** Need OpenAI API key configuration  
**ETA to 100%:** 4 minutes (after API key setup)

🎊 **Almost there! Just configure your API key and we're good to go!** 🎊
