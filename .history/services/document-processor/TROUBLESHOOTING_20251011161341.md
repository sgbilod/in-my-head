# Troubleshooting Guide - Document Processing API

## 📋 Quick Reference

| Issue            | Likely Cause                       | Quick Fix                          |
| ---------------- | ---------------------------------- | ---------------------------------- |
| API won't start  | Port in use / Missing dependencies | Check port, install deps           |
| Redis error      | Redis not running                  | Start Redis container              |
| Qdrant error     | Qdrant not running                 | Start Qdrant container             |
| Slow performance | Too many concurrent requests       | Scale workers                      |
| High memory      | Memory leak / Large files          | Restart workers, reduce batch size |
| Tests failing    | Service dependencies               | Ensure Redis/Qdrant running        |

---

## 🔍 Diagnostic Commands

### Check Service Health

```powershell
# API health
curl http://localhost:8000/health

# Redis
redis-cli ping

# Qdrant
curl http://localhost:6333/health

# Celery workers
celery -A src.jobs.celery_app inspect active
```

### View Logs

```powershell
# API logs (if running in terminal)
# Check terminal output

# Docker logs
docker logs document-processor
docker logs redis
docker logs qdrant

# Celery logs
Get-Content celery_worker.log -Tail 50 -Wait
```

### Check Resource Usage

```powershell
# Docker stats
docker stats

# Windows Task Manager
taskmgr

# Python memory profile
python -m memory_profiler src/app.py
```

---

## 🐛 Common Issues

### 1. API Server Won't Start

#### Symptoms

```
Error: [Errno 10048] error while attempting to bind on address
```

#### Cause

Port 8000 is already in use

#### Solution

```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process
taskkill /PID <pid> /F

# Or use different port
$env:PORT = "8001"
python -m uvicorn src.app:app --host 0.0.0.0 --port 8001
```

---

### 2. Redis Connection Failed

#### Symptoms

```
redis.exceptions.ConnectionError: Error connecting to localhost:6379
```

#### Cause

Redis is not running or wrong host/port

#### Solution

```powershell
# Start Redis (Docker)
docker run -d -p 6379:6379 --name redis redis:7.0-alpine

# Check Redis is running
docker ps | findstr redis

# Test connection
redis-cli ping
# Expected: PONG

# If using different host/port
$env:REDIS_HOST = "your-redis-host"
$env:REDIS_PORT = "6380"
```

---

### 3. Qdrant Connection Failed

#### Symptoms

```
requests.exceptions.ConnectionError: Failed to connect to Qdrant
```

#### Cause

Qdrant is not running or wrong host/port

#### Solution

```powershell
# Start Qdrant (Docker)
docker run -d -p 6333:6333 -p 6334:6334 `
  --name qdrant qdrant/qdrant:v1.7.0

# Check Qdrant
curl http://localhost:6333/health

# View Qdrant logs
docker logs qdrant

# If using different host/port
$env:QDRANT_HOST = "your-qdrant-host"
$env:QDRANT_PORT = "6334"
```

---

### 4. Authentication Failed

#### Symptoms

```
HTTP 401: API key is required
```

#### Cause

No API key provided or invalid key

#### Solution

```powershell
# Set API keys
$env:API_KEYS = "your-api-key-1,your-api-key-2"

# Generate new key
python -c "from src.api.auth import generate_api_key; print(generate_api_key())"

# Test with key
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/statistics
```

---

### 5. Rate Limit Exceeded

#### Symptoms

```
HTTP 429: Rate limit exceeded. Try again in X seconds
```

#### Cause

Too many requests from same user

#### Solution

```powershell
# Increase rate limit (development only)
$env:RATE_LIMIT_REQUESTS = "1000"
$env:RATE_LIMIT_WINDOW = "60"

# Wait for rate limit to reset
Start-Sleep -Seconds 60

# Use different API key
# Or spread requests across multiple keys
```

---

### 6. File Upload Failed

#### Symptoms

```
HTTP 400: File type not supported
HTTP 400: File too large
```

#### Cause

Invalid file type or file exceeds 100MB limit

#### Solution

```powershell
# Check supported formats
# .pdf, .docx, .txt, .html, .md, .json, .xml, .csv

# Compress large files
# Or split into smaller files

# Check file size
(Get-Item "document.pdf").Length / 1MB
```

---

### 7. Job Stuck in Pending

#### Symptoms

Job status remains "pending" for long time

#### Causes

1. Celery workers not running
2. Workers overwhelmed
3. Redis queue full

#### Solution

```powershell
# Check Celery workers
celery -A src.jobs.celery_app inspect active

# Start workers if not running
.\start_celery_workers.ps1

# Check worker stats
celery -A src.jobs.celery_app inspect stats

# Purge queue (development only)
celery -A src.jobs.celery_app purge

# Scale workers
# Edit start_celery_workers.ps1 to increase --concurrency
```

---

### 8. Job Processing Failed

#### Symptoms

```json
{
  "status": "failure",
  "error": "Processing failed: ..."
}
```

#### Causes

Multiple possible causes - check error message

#### Solution

```powershell
# Get detailed error
$jobId = "your-job-id"
curl -H "X-API-Key: your-key" `
  "http://localhost:8000/api/v1/jobs/$jobId"

# Common errors:

# 1. File parsing error
#    - File corrupted or invalid format
#    - Try re-uploading file

# 2. AI service error
#    - Check AI engine is running
#    - Check AI service logs

# 3. Vector database error
#    - Check Qdrant connection
#    - Verify collection exists

# 4. Memory error
#    - File too large for worker
#    - Reduce worker concurrency or increase memory
```

---

### 9. Search Returns No Results

#### Symptoms

Search query returns empty results despite having documents

#### Causes

1. Documents not yet indexed
2. Wrong query
3. Filters too restrictive

#### Solution

```powershell
# Check document count
curl -H "X-API-Key: your-key" `
  "http://localhost:8000/api/v1/statistics"

# Try simpler query
$body = @{query="test"; limit=10} | ConvertTo-Json
curl -X POST "http://localhost:8000/api/v1/search" `
  -H "X-API-Key: your-key" `
  -H "Content-Type: application/json" `
  -d $body

# Remove filters
# Check spelling
# Wait for documents to finish processing
```

---

### 10. Slow Performance

#### Symptoms

Requests taking >1 second
High CPU/memory usage

#### Causes

1. Too many concurrent requests
2. Large files being processed
3. Insufficient resources

#### Solution

```powershell
# Check resource usage
docker stats

# Scale workers
# Increase from 2 to 4 workers
# Edit docker-compose.yml:
# celery-worker:
#   command: ... --concurrency=4

# Restart services
docker-compose restart

# Add more API replicas (K8s)
kubectl scale deployment document-processor-api --replicas=5

# Optimize queries
# - Reduce search limit
# - Use more specific queries
# - Add caching

# Monitor performance
python benchmark.py
```

---

### 11. WebSocket Connection Issues

#### Symptoms

```
WebSocket connection failed
Connection closed unexpectedly
```

#### Causes

1. Proxy/firewall blocking WebSocket
2. Connection timeout
3. Invalid job_id

#### Solution

```powershell
# Test WebSocket endpoint exists
curl -I http://localhost:8000/api/v1/ws/jobs/test

# Check firewall rules
# Ensure WebSocket protocol allowed

# Use WebSocket test page
# Open: http://localhost:8000/api/v1/ws/test

# Increase timeout
# In client code, set connection timeout to 60s

# Verify job_id is valid
curl -H "X-API-Key: your-key" `
  "http://localhost:8000/api/v1/jobs/$jobId"
```

---

### 12. High Memory Usage

#### Symptoms

```
Container using >2GB RAM
Out of memory errors
Container killed by OOM
```

#### Causes

1. Memory leak
2. Too many large files
3. Worker concurrency too high

#### Solution

```powershell
# Restart workers
.\start_celery_workers.ps1

# Reduce concurrency
# Edit celery command:
celery -A src.jobs.celery_app worker --concurrency=2

# Add memory limits (Docker)
# docker-compose.yml:
# services:
#   celery-worker:
#     mem_limit: 1g
#     memswap_limit: 1g

# Monitor memory
docker stats celery-worker

# Profile memory usage
pip install memory_profiler
python -m memory_profiler src/jobs/pipeline.py

# Clear caches
redis-cli FLUSHALL
```

---

### 13. Tests Failing

#### Symptoms

```
pytest failures
Import errors
Fixture errors
```

#### Causes

1. Missing dependencies
2. Services not running
3. Test isolation issues

#### Solution

```powershell
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Start required services
docker-compose up -d redis qdrant

# Run tests with verbose output
pytest test_api.py -v --tb=short

# Run specific test
pytest test_api.py::TestAuthentication::test_generate_api_key -v

# Clear test data
redis-cli -n 2 FLUSHDB

# Check test environment
$env:REDIS_HOST = "localhost"
$env:QDRANT_HOST = "localhost"
$env:API_KEYS = "test-key-123"

# Run tests in isolation
pytest test_api.py --forked
```

---

### 14. Docker Build Failed

#### Symptoms

```
ERROR: failed to solve
Could not find a version that satisfies the requirement
```

#### Causes

1. Missing dependencies
2. Python version mismatch
3. Network issues

#### Solution

```powershell
# Clean Docker cache
docker builder prune -af

# Rebuild without cache
docker build --no-cache -t document-processor .

# Check Python version
docker run --rm python:3.11-slim python --version

# Test build locally
docker build -t document-processor:test .
docker run --rm document-processor:test python -c "import src.app"

# Check requirements.txt
pip install --dry-run -r requirements.txt

# Use --trusted-host for corporate proxies
pip install --trusted-host pypi.org \
  --trusted-host pypi.python.org \
  --trusted-host files.pythonhosted.org \
  -r requirements.txt
```

---

### 15. Kubernetes Deployment Issues

#### Symptoms

```
Pod CrashLoopBackOff
ImagePullBackOff
Pending pod
```

#### Causes

Multiple K8s-specific issues

#### Solution

```bash
# Check pod status
kubectl get pods -n document-processing

# Describe pod
kubectl describe pod <pod-name> -n document-processing

# View logs
kubectl logs <pod-name> -n document-processing

# Check events
kubectl get events -n document-processing --sort-by='.lastTimestamp'

# Common fixes:

# 1. ImagePullBackOff
kubectl get pod <pod-name> -n document-processing -o yaml
# Check image name and registry credentials

# 2. CrashLoopBackOff
kubectl logs <pod-name> -n document-processing
# Fix error in application

# 3. Pending
kubectl describe pod <pod-name> -n document-processing
# Check resource requests vs cluster capacity

# 4. ConfigMap/Secret not found
kubectl get configmaps -n document-processing
kubectl get secrets -n document-processing
# Create missing resources
```

---

## 🔧 Advanced Debugging

### Enable Debug Logging

```powershell
# Set log level
$env:LOG_LEVEL = "DEBUG"

# Python logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Profile Performance

```powershell
# Install profilers
pip install py-spy memory_profiler line_profiler

# CPU profiling
py-spy top -- python -m uvicorn src.app:app

# Memory profiling
python -m memory_profiler src/app.py

# Line profiling
kernprof -l -v src/jobs/pipeline.py
```

### Network Debugging

```powershell
# Test API connectivity
Test-NetConnection localhost -Port 8000

# Test Redis
Test-NetConnection localhost -Port 6379

# Test Qdrant
Test-NetConnection localhost -Port 6333

# Trace route
tracert api.example.com

# DNS lookup
nslookup api.example.com
```

### Database Debugging

```powershell
# Redis CLI
redis-cli

# Check keys
redis-cli KEYS "*"

# Get value
redis-cli GET "key"

# Monitor commands
redis-cli MONITOR

# Qdrant API
curl http://localhost:6333/collections
curl http://localhost:6333/collections/documents
```

---

## 📞 Getting Help

### Before Asking for Help

1. ✅ Check this troubleshooting guide
2. ✅ Review error messages carefully
3. ✅ Check service logs
4. ✅ Verify all dependencies are running
5. ✅ Try restarting services
6. ✅ Search GitHub issues

### When Reporting Issues

Include:

- **Error message** (full stack trace)
- **Steps to reproduce**
- **Environment** (OS, Python version, Docker version)
- **Configuration** (sanitized - no secrets)
- **Logs** (relevant sections)
- **What you've tried** (troubleshooting steps)

### Support Channels

- **GitHub Issues**: Technical bugs and features
- **GitHub Discussions**: Questions and community help
- **Documentation**: README, API docs, deployment guide
- **Email**: support@example.com (for urgent issues)

---

## 📚 Additional Resources

- [API Documentation](PHASE_3_8_COMPLETE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Quick Start Guide](QUICKSTART_API.md)
- [Testing Guide](test_e2e.py)
- [Performance Benchmarks](benchmark.py)
- [Load Testing](load_test.py)

---

**Last Updated**: October 11, 2025  
**Version**: 1.0.0
