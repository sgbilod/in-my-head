# 🔒 Data Security & Safety Guide - In My Head

## Quick Answers

### Upload Limits
- **Max file size:** 100 MB per file
- **Total storage:** Unlimited (constrained only by your disk space)
- **Number of files:** No limit

### Data Safety
- **Very Safe:** Data stored in Docker volumes with persistence
- **Risk Level:** LOW - Data survives container restarts
- **Backup:** Recommended (see backup section below)

---

## 📊 Upload Limits & Constraints

### Per-File Limits

| Limit Type | Value | Configurable? |
|------------|-------|---------------|
| **Max file size** | 100 MB | ✅ Yes |
| **Min file size** | 1 byte | No |
| **Concurrent uploads** | Unlimited | Based on system resources |
| **Request timeout** | 120 seconds | ✅ Yes |

### System-Wide Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| **Total documents** | Unlimited | Constrained by disk space |
| **Total storage** | Unlimited | Constrained by disk space |
| **Database size** | Unlimited | PostgreSQL handles terabytes |
| **Vector DB size** | Unlimited | Qdrant scales well |
| **Concurrent users** | 100+ | Depends on system resources |

### Disk Space Usage

**Estimated storage per 1,000 documents:**
- **Document files:** ~500 MB - 2 GB (varies by file type)
- **PostgreSQL metadata:** ~50 MB
- **Vector embeddings:** ~150 MB (384-dim embeddings)
- **Redis cache:** ~20 MB
- **Total:** ~720 MB - 2.2 GB per 1,000 documents

### How to Change Upload Limit

Edit `services/document-processor/src/api/routes_documents.py`:

```python
# Line 54 - Change from 100MB to your desired size
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB
```

Then rebuild the container:
```powershell
cd infrastructure/docker
docker-compose -f docker-compose.dev.yml up -d --build document-processor
```

---

## 🛡️ Data Security & Safety

### Security Level: **HIGH** ✅

#### Why Your Data is Safe

1. **Local-First Architecture**
   - ✅ All data stays on YOUR computer
   - ✅ No external servers involved (unless you use cloud AI)
   - ✅ No data leaves your network
   - ✅ Complete privacy control

2. **Docker Volume Persistence**
   - ✅ Data stored in Docker-managed volumes
   - ✅ Survives container restarts
   - ✅ Survives container deletions
   - ✅ Survives Docker Desktop restarts
   - ✅ Survives system reboots

3. **Multiple Data Stores**
   - ✅ PostgreSQL: Document metadata (persistent)
   - ✅ Qdrant: Vector embeddings (persistent)
   - ✅ MinIO: File storage (persistent)
   - ✅ Redis: Cache only (ephemeral, but backed up)

---

## 💾 Where Your Data Lives

### Docker Volumes (Persistent Storage)

Your data is stored in 8 Docker volumes:

| Volume | Contains | Size | Critical? |
|--------|----------|------|-----------|
| `inmyhead_postgres_data` | Document metadata, database | ~100 MB | ⭐⭐⭐ CRITICAL |
| `inmyhead_qdrant_data` | Vector embeddings | ~150 MB | ⭐⭐⭐ CRITICAL |
| `inmyhead_minio_data` | Uploaded document files | ~2 GB+ | ⭐⭐⭐ CRITICAL |
| `inmyhead_redis_data` | Cache, temporary data | ~20 MB | ⭐ Optional |
| `inmyhead_ai_models` | Downloaded AI models | ~500 MB | ⭐⭐ Important |
| `inmyhead_document_cache` | Processing cache | ~50 MB | ⭐ Optional |
| `inmyhead_search_cache` | Search cache | ~10 MB | ⭐ Optional |
| `inmyhead_prometheus_data` | Monitoring metrics | ~20 MB | Optional |

### Physical Location on Disk

**Windows (Docker Desktop):**
```
C:\ProgramData\Docker\volumes\
├── inmyhead_postgres_data\_data\
├── inmyhead_qdrant_data\_data\
├── inmyhead_minio_data\_data\
└── ... (other volumes)
```

**Linux:**
```
/var/lib/docker/volumes/
├── inmyhead_postgres_data/_data/
├── inmyhead_qdrant_data/_data/
├── inmyhead_minio_data/_data/
└── ... (other volumes)
```

---

## ⚠️ Data Loss Scenarios

### When Data is SAFE ✅

| Scenario | Data Safe? | Notes |
|----------|------------|-------|
| Container restart | ✅ YES | Volumes persist |
| Container rebuild | ✅ YES | Volumes persist |
| Docker Desktop restart | ✅ YES | Volumes persist |
| System reboot | ✅ YES | Volumes persist |
| `docker-compose restart` | ✅ YES | Volumes persist |
| `docker-compose stop` + `start` | ✅ YES | Volumes persist |
| Power outage | ✅ YES* | *Modern filesystems handle this |

### When Data is AT RISK ⚠️

| Scenario | Data Safe? | How to Prevent |
|----------|------------|----------------|
| `docker-compose down -v` | ❌ NO | DON'T use `-v` flag! |
| `docker volume rm` | ❌ NO | Never delete volumes manually |
| Docker Desktop "Reset to Factory" | ❌ NO | Backup first! |
| Disk failure | ❌ NO | Regular backups essential |
| Accidental volume deletion | ❌ NO | Backup regularly |
| Docker Desktop uninstall (Windows) | ⚠️ MAYBE | Depends on options selected |

### The ONLY Dangerous Commands

**NEVER RUN THESE without backing up first:**

```powershell
# ❌ DANGEROUS - Deletes ALL data
docker-compose down -v

# ❌ DANGEROUS - Deletes specific volume
docker volume rm inmyhead_postgres_data

# ❌ DANGEROUS - Deletes all unused volumes
docker volume prune

# ❌ DANGEROUS - Factory reset
# Docker Desktop → Settings → Reset to factory defaults
```

**SAFE commands:**

```powershell
# ✅ SAFE - Stops containers, keeps data
docker-compose down

# ✅ SAFE - Stops containers
docker-compose stop

# ✅ SAFE - Restarts containers
docker-compose restart

# ✅ SAFE - Rebuilds without losing data
docker-compose up -d --build
```

---

## 💾 Backup Strategy

### I've Created a Backup Script for You!

Check `Backup_Data.ps1` - it backs up all critical volumes.

### Quick Backup

```powershell
# Backup everything to a zip file
.\Backup_Data.ps1

# Result: inmyhead_backup_YYYYMMDD_HHMMSS.zip
```

### What Gets Backed Up

1. **PostgreSQL database** (complete dump)
2. **Qdrant vector data** (all embeddings)
3. **MinIO file storage** (all uploaded documents)
4. **Redis data** (cache)
5. **Configuration files** (.env, docker-compose)

### Backup File Location

Backups are saved to:
```
C:\Users\sgbil\In My Head\backups\
```

### Recommended Backup Schedule

| Frequency | Method | Purpose |
|-----------|--------|---------|
| **Daily** | Automated script | Regular protection |
| **Before major changes** | Manual backup | Safety net |
| **Weekly** | Copy to external drive | Offsite backup |
| **Monthly** | Cloud backup | Disaster recovery |

---

## 📂 Restore from Backup

### Restore Everything

```powershell
# 1. Stop services
docker-compose down

# 2. Restore from backup zip
.\Restore_Data.ps1 -BackupFile "backups\inmyhead_backup_20251014_120000.zip"

# 3. Start services
docker-compose up -d
```

### Restore Specific Component

```powershell
# Restore only PostgreSQL
docker run --rm -v inmyhead_postgres_data:/data -v ${PWD}/backups:/backup alpine sh -c "cd /data && tar xzf /backup/postgres_backup.tar.gz"

# Restore only Qdrant
docker run --rm -v inmyhead_qdrant_data:/data -v ${PWD}/backups:/backup alpine sh -c "cd /data && tar xzf /backup/qdrant_backup.tar.gz"
```

---

## 🔐 Security Best Practices

### 1. Protect API Keys

Your API keys are stored in:
```
infrastructure/docker/.env
```

**Security measures:**
- ✅ File is git-ignored (not committed)
- ✅ Only accessible from your machine
- ✅ Encrypted at rest (if using BitLocker/FileVault)

**Best practices:**
```powershell
# Restrict file permissions (PowerShell)
icacls "infrastructure\docker\.env" /inheritance:r /grant:r "${env:USERNAME}:F"

# Or move to a more secure location and symlink
```

### 2. Database Security

**Current PostgreSQL password:**
- Username: `inmyhead`
- Password: `inmyhead_dev_pass_change_in_prod`

**⚠️ CHANGE THIS FOR PRODUCTION!**

Edit `infrastructure/docker/docker-compose.dev.yml`:
```yaml
POSTGRES_PASSWORD: your_secure_password_here
```

### 3. Network Security

**Current setup:**
- ✅ Services only accessible on localhost
- ✅ No external access by default
- ✅ Isolated Docker network

**Ports exposed to localhost only:**
- 5432 (PostgreSQL)
- 6333/6334 (Qdrant)
- 6379 (Redis)
- 8001 (Document Processor)
- 9000/9001 (MinIO)

---

## 🚨 Disaster Recovery

### Complete Data Loss Recovery

If you lose ALL data but have a backup:

```powershell
# 1. Stop everything
docker-compose down

# 2. Remove old volumes
docker volume rm inmyhead_postgres_data inmyhead_qdrant_data inmyhead_minio_data

# 3. Recreate volumes
docker-compose up -d

# 4. Stop services again
docker-compose down

# 5. Restore from backup
.\Restore_Data.ps1 -BackupFile "your_backup.zip"

# 6. Start services
docker-compose up -d
```

### Partial Data Loss

**If only PostgreSQL is corrupted:**
```powershell
# 1. Stop services
docker-compose stop postgres

# 2. Remove volume
docker volume rm inmyhead_postgres_data

# 3. Restore from backup (see above)

# 4. Restart
docker-compose up -d postgres
```

---

## 📈 Monitoring Data Health

### Check Volume Sizes

```powershell
# List all volumes with sizes
docker system df -v | Select-String "inmyhead"

# Detailed volume info
docker volume ls | Select-String "inmyhead" | ForEach-Object {
    $vol = $_.ToString().Split()[-1]
    docker volume inspect $vol | ConvertFrom-Json | Select-Object Name, Mountpoint
}
```

### Check Database Health

```powershell
# PostgreSQL connection test
docker exec inmyhead-postgres psql -U inmyhead -d inmyhead_dev -c "SELECT COUNT(*) FROM documents;"

# Qdrant health
Invoke-RestMethod -Uri "http://localhost:6333/collections/documents/info" -Method Get

# Document count
Invoke-RestMethod -Uri "http://localhost:8001/documents/" -Method Get | Select-Object -ExpandProperty count
```

### Verify Backups

```powershell
# List backups
Get-ChildItem backups\*.zip | Select-Object Name, Length, CreationTime | Format-Table

# Test backup integrity
Test-Path "backups\inmyhead_backup_*.zip"
```

---

## 🎯 Data Safety Checklist

### Daily
- [ ] Verify services are running (`docker ps`)
- [ ] Check available disk space
- [ ] Review application logs for errors

### Weekly
- [ ] Run backup script (`.\Backup_Data.ps1`)
- [ ] Copy backup to external drive
- [ ] Verify backup file integrity

### Monthly
- [ ] Test restore process (on test system)
- [ ] Review and clean old backups
- [ ] Update passwords if needed
- [ ] Check for In My Head updates

---

## 💡 Pro Tips

### 1. Automatic Backups

Create a scheduled task (Windows):

```powershell
# Create scheduled daily backup at 2 AM
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File `"C:\Users\sgbil\In My Head\Backup_Data.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "InMyHead_Backup" -Description "Daily backup of In My Head data"
```

### 2. Monitor Disk Space

```powershell
# Check free space
Get-PSDrive C | Select-Object Used, Free, @{n="FreeGB";e={[math]::Round($_.Free/1GB,2)}}

# Alert if low
if ((Get-PSDrive C).Free -lt 10GB) {
    Write-Warning "Low disk space! Less than 10GB remaining."
}
```

### 3. Version Control Your Configuration

```powershell
# Backup configuration files separately
Copy-Item infrastructure\docker\docker-compose.dev.yml backups\docker-compose_$(Get-Date -Format 'yyyyMMdd').yml
Copy-Item infrastructure\docker\.env backups\.env_$(Get-Date -Format 'yyyyMMdd')
```

---

## 🔍 FAQ

**Q: Can I lose data if I close the desktop app?**
A: No! Data is stored in Docker containers, not the desktop app.

**Q: What if Docker Desktop crashes?**
A: Your data is safe. Just restart Docker Desktop and the app.

**Q: Can I move In My Head to another computer?**
A: Yes! Create a backup, copy to new PC, restore. See "Restore from Backup" section.

**Q: How much disk space do I need?**
A: Minimum 10 GB free. Recommended 50+ GB for large libraries.

**Q: Can I access the raw files?**
A: Yes, they're in Docker volumes. Use backup script to extract them.

**Q: What if I accidentally run `docker-compose down -v`?**
A: Restore from your most recent backup. This is why backups are critical!

**Q: Is my data encrypted?**
A: At rest: Depends on your drive encryption (BitLocker, FileVault, etc.)
   In transit: Local only, no network transmission by default.

**Q: Can someone else access my data?**
A: Only if they have physical access to your computer. Services are localhost-only.

---

## 📞 Emergency Contacts

**If you experience data loss:**

1. **STOP** - Don't make changes
2. **Don't run** `docker-compose down -v`
3. **Check** if volumes still exist: `docker volume ls`
4. **Restore** from most recent backup
5. **Contact support** if issues persist

---

## Summary: Your Data is Safe IF...

✅ **You backup regularly** (use `Backup_Data.ps1`)
✅ **You don't use `-v` flag** with `docker-compose down`
✅ **You don't manually delete volumes**
✅ **You have enough disk space**
✅ **You keep backups on external drive**

**Bottom line:** Your data is as safe as a traditional database (PostgreSQL) with the added benefit of Docker's isolation and easy backup/restore capabilities.

---

**Last Updated:** October 14, 2025
**Version:** 1.0.0
