# ==========================================

# AI Provider Setup Guide

# ==========================================

## 🎯 Overview

This guide will help you configure your AI providers for **In My Head**.

**Current Configuration:**

- ✅ **Embeddings**: Local models (sentence-transformers) - 100% private
- 🤖 **LLM**: Claude Pro (Anthropic) - Best reasoning
- 🔄 **Fallback**: Gemini Pro → OpenAI

---

## 📋 Prerequisites

You mentioned you have:

- ✅ Claude Pro subscription
- ✅ GitHub Copilot Pro+
- ✅ Gemini Pro subscription

---

## 🔑 Step 1: Get Your API Keys

### Claude (Anthropic) - PRIMARY LLM

1. Go to: https://console.anthropic.com/settings/keys
2. Log in with your Claude Pro account
3. Click "Create Key"
4. Name it: "In My Head"
5. Copy the key (starts with `sk-ant-api03-...`)

### Gemini Pro (Google) - FALLBACK LLM

1. Go to: https://makersuite.google.com/app/apikey
2. Log in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

### OpenAI - ALREADY CONFIGURED

Your OpenAI key is already set up (but we'll use it minimally).

---

## ⚙️ Step 2: Configure API Keys

Edit this file: `infrastructure/docker/.env`

Replace these lines:

```env
# Anthropic (Claude) - Replace this!
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google (Gemini Pro) - Replace this!
GOOGLE_API_KEY=your_google_api_key_here
```

With your actual keys:

```env
# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx

# Google (Gemini Pro)
GOOGLE_API_KEY=AIzaxxxxxxxxxxxx
```

---

## 🚀 Step 3: Install Local Embedding Models

We'll use **sentence-transformers** for 100% private embeddings (no API calls).

### Option A: Install in Virtual Environment (Recommended)

```powershell
# Activate your virtual environment
& "C:\Users\sgbil\In My Head\venv\Scripts\Activate.ps1"

# Install sentence-transformers and PyTorch
pip install sentence-transformers torch transformers

# This will download ~500MB of packages
# First run will also download the embedding model (~80MB)
```

### Option B: Install in Docker Container

The Docker container will automatically install everything when rebuilt.

---

## 🔧 Step 4: Rebuild Services

After configuring API keys and installing packages:

```powershell
cd "C:\Users\sgbil\In My Head\infrastructure\docker"

# Rebuild document processor with new AI libraries
docker-compose -f docker-compose.dev.yml build document-processor

# Restart all services
docker-compose -f docker-compose.dev.yml -p inmyhead down
docker-compose -f docker-compose.dev.yml -p inmyhead up -d
```

---

## ✅ Step 5: Verify Configuration

Test that everything is working:

```powershell
# Check if services started
docker-compose -f docker-compose.dev.yml -p inmyhead ps

# Upload a test document (should now generate embeddings locally)
curl.exe -X POST "http://localhost:8001/documents/upload" `
  -F "file=@test_document.pdf" `
  -F "title=Test with Local Embeddings"

# Check logs for confirmation
docker logs inmyhead-document-processor 2>&1 | Select-String -Pattern "LOCAL|embedding|Claude|Gemini"
```

You should see output like:

```
🔒 Loading LOCAL embedding model: all-MiniLM-L6-v2
   (This provides 100% privacy - no external API calls)
✅ AI Service initialized!
   📊 Embeddings: local (dim: 384)
   🤖 LLM: claude
```

---

## 🎛️ Configuration Options

### Embedding Provider Options

Edit `.env` file:

```env
# Option 1: Local (PRIVACY FIRST) - No API calls
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Fast, 80MB

# Option 2: Better quality local embeddings
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-mpnet-base-v2  # Better, 420MB

# Option 3: Use OpenAI (if you want to use your quota)
EMBEDDING_PROVIDER=openai
```

### LLM Provider Options

```env
# Option 1: Claude (BEST for reasoning)
LLM_PROVIDER=claude

# Option 2: Gemini Pro (FASTEST and cost-effective)
LLM_PROVIDER=gemini

# Option 3: OpenAI (Fallback)
LLM_PROVIDER=openai
```

### Privacy Mode

```env
# Strict privacy: Only local models, no API calls
PRIVACY_MODE=true

# Balanced: Local embeddings + paid APIs for LLM
PRIVACY_MODE=false
```

---

## 💰 Cost Comparison

| Provider             | Cost                        | Speed     | Quality   |
| -------------------- | --------------------------- | --------- | --------- |
| **Local Embeddings** | FREE                        | Fast      | Good      |
| **Claude Sonnet**    | ~$3/$15 per 1M tokens       | Medium    | Excellent |
| **Gemini Flash**     | ~$0.075/$0.30 per 1M tokens | Very Fast | Great     |
| **OpenAI GPT-4o**    | ~$2.50/$10 per 1M tokens    | Medium    | Excellent |

**Recommendation**: Use local embeddings + Claude for best balance of privacy, quality, and cost.

---

## 🔍 Troubleshooting

### "sentence-transformers not available"

```powershell
pip install sentence-transformers torch transformers
```

### "ANTHROPIC_API_KEY not set"

Check your `.env` file has the correct key without typos.

### Docker container fails to start

```powershell
# Check logs
docker logs inmyhead-document-processor

# Rebuild
docker-compose -f docker-compose.dev.yml build document-processor --no-cache
```

### Model download is slow

First-time setup downloads ~500MB. Subsequent runs use cached models.

---

## 📊 What Happens After Setup

### Document Upload Flow

1. **Upload PDF** → Extract text ✅
2. **Generate Embedding** → **LOCAL MODEL** (no API call) ✅
3. **Store in Qdrant** → Vector database ✅
4. **Store in PostgreSQL** → Metadata ✅

### AI Query Flow

1. **User asks question** → Parse query ✅
2. **Generate query embedding** → **LOCAL MODEL** (no API call) ✅
3. **Search Qdrant** → Find relevant documents ✅
4. **Generate answer** → **Claude API** (paid subscription) ✅

**Privacy**: Only the answer generation uses external APIs. All document processing is 100% local.

---

## 🎉 Next Steps After Setup

Once configured, you can:

1. ✅ Upload unlimited documents (free, local processing)
2. ✅ Generate embeddings instantly (no API quota limits)
3. ✅ Ask questions using Claude (paid subscription, no quota issues)
4. ✅ Build knowledge graphs
5. ✅ Export and share (privacy-first)

---

## 📞 Need Help?

If you get stuck:

1. Check Docker logs: `docker logs inmyhead-document-processor`
2. Verify API keys are correct in `.env`
3. Make sure sentence-transformers is installed: `pip show sentence-transformers`
4. Rebuild containers: `docker-compose build document-processor`

---

**Ready to configure? Follow the steps above and let me know when you've added your API keys!**
