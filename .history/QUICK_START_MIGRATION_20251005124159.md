# 🚀 QUICK START - PROJECT MIGRATION

## ⚡ TL;DR

You have a nested folder structure that needs to be flattened. I've created two automated scripts to fix this.

---

## 📝 THE PROBLEM

```
❌ Current (Bad):
C:\Users\sgbil\In My Head\
    ├── .git\
    └── in-my-head\            ← Everything buried here
        ├── services\
        ├── docs\
        └── ...

✅ Target (Good):
C:\Users\sgbil\In My Head\
    ├── .git\
    ├── services\              ← Everything at root level
    ├── docs\
    └── ...
```

---

## ⚡ THE SOLUTION (2 Commands)

### **Step 1: Flatten Structure**
```powershell
cd "C:\Users\sgbil\In My Head"
.\flatten-structure.ps1
```
**Duration:** ~30 seconds  
**What it does:** Moves all files from `in-my-head\` to root, creates backup

---

### **Step 2: Setup Environment**
```powershell
.\setup-environment.ps1
```
**Duration:** ~2-5 minutes  
**What it does:** Installs dependencies, starts Docker, runs migrations, seeds database

---

## ✅ VERIFICATION

After both scripts complete, verify:

```powershell
# Check structure is flat
ls
# Should see: services, docs, infrastructure, etc. at root

# Check Docker containers
docker ps
# Should see: postgres, redis, qdrant, minio running

# Test database
cd services\document-processor
python -c "from src.database.connection import check_health; check_health()"
# Should output: "Database connection healthy!"
```

---

## 🔑 CREDENTIALS

After setup, test user is available:
- **Username:** `testuser`
- **Password:** `Test123!`
- **Email:** `test@inmyhead.local`

---

## 🛠️ UTILITY COMMANDS

```powershell
.\start-all.ps1      # Start all Docker services
.\stop-all.ps1       # Stop all Docker services
docker ps            # View running containers
docker-compose logs  # View container logs
```

---

## 📚 NEED HELP?

Read the full guide: `MIGRATION_GUIDE.md`

---

## ⚠️ IMPORTANT NOTES

1. **Backup is automatic** - Script creates timestamped backup before any changes
2. **Restart terminal** after setup to pick up new environment variables
3. **Update IDE workspace** path from `in-my-head\` to root
4. **Review .env files** and change default passwords before production

---

## 🎯 EXPECTED RESULT

After completion:
- ✅ Flat project structure (no nested folder)
- ✅ All dependencies installed
- ✅ Docker containers running
- ✅ Database migrated and seeded
- ✅ Ready to start Phase 3 development

---

**Total Time:** ~3-5 minutes  
**Risk Level:** Low (automatic backup created)  
**Reversible:** Yes (backup preserved)

**Let's go!** 🚀
