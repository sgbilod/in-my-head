# 🔧 PROJECT STRUCTURE MIGRATION GUIDE

## 📋 Overview

This guide helps you flatten the nested project structure and set up your development environment.

**Current Structure (Problem):**

```
C:\Users\sgbil\In My Head\          ← Root (has .git)
    └── in-my-head\                  ← Nested folder (has all project files)
        ├── services\
        ├── docs\
        └── ... everything here
```

**Target Structure (Solution):**

```
C:\Users\sgbil\In My Head\          ← Root (has .git AND all files)
    ├── services\
    ├── docs\
    └── ... everything at root level
```

---

## 🚀 STEP-BY-STEP INSTRUCTIONS

### **Step 1: Flatten the Project Structure**

Run the flattening script:

```powershell
cd "C:\Users\sgbil\In My Head"
.\flatten-structure.ps1
```

**What it does:**

1. ✅ Creates a timestamped backup of `in-my-head\` folder
2. ✅ Moves all files from `in-my-head\` to root
3. ✅ Intelligently merges duplicate folders (like `.github`)
4. ✅ Removes the empty `in-my-head\` folder
5. ✅ Verifies all files were moved successfully
6. ✅ Displays summary and next steps

**Safety features:**

- Full backup created before any changes
- Backup is timestamped (won't overwrite previous backups)
- Dry-run verification before destructive operations
- Detailed logging of all operations

**Expected output:**

```
╔══════════════════════════════════════════════════════════════════╗
║     FLATTEN PROJECT STRUCTURE - In My Head                       ║
╚══════════════════════════════════════════════════════════════════╝

📋 STEP 1: Verifying current structure...
   ✅ Root path exists: C:\Users\sgbil\In My Head
   ✅ Nested path exists: C:\Users\sgbil\In My Head\in-my-head

📦 STEP 2: Creating backup...
   ✅ Backup created successfully
   ℹ️  Backup contains 1234 items

🚚 STEP 4: Moving files and folders...
   ➡️  Moving: services
   ➡️  Moving: docs
   ... (continues for all items)
   ✅ Moved: 25 items
   🔀 Merged: 2 folders

✅ STEP 6: Verifying move was successful...
   ✅ Found: services\
   ✅ Found: docs\
   ✅ Found: README.md

╔══════════════════════════════════════════════════════════════════╗
║                 FLATTENING COMPLETE ✅                            ║
╚══════════════════════════════════════════════════════════════════╝
```

---

### **Step 2: Set Up Development Environment**

After flattening, run the environment setup script:

```powershell
cd "C:\Users\sgbil\In My Head"
.\setup-environment.ps1
```

**What it does:**

1. ✅ Verifies project structure is correct
2. ✅ Checks system prerequisites (Python, Node.js, Docker, Git)
3. ✅ Creates environment variable: `IN_MY_HEAD_ROOT`
4. ✅ Creates `.env` files for all services
5. ✅ Installs Python dependencies (`pip install -r requirements.txt`)
6. ✅ Installs Node.js dependencies (`npm install`)
7. ✅ Starts database containers (PostgreSQL, Redis, Qdrant, MinIO)
8. ✅ Runs database migrations (`alembic upgrade head`)
9. ✅ Seeds test data (user, collections, tags)
10. ✅ Creates utility scripts (`start-all.ps1`, `stop-all.ps1`)

**Expected output:**

```
╔══════════════════════════════════════════════════════════════════╗
║     ENVIRONMENT SETUP - In My Head Project                       ║
╚══════════════════════════════════════════════════════════════════╝

🔍 STEP 2: Checking system prerequisites...
   ✅ Python: Python 3.11.5
   ✅ pip: pip 23.2.1
   ✅ Node.js: v18.17.1
   ✅ npm: 9.8.1
   ✅ Docker: Docker version 24.0.5
   ✅ Git: git version 2.42.0

🔧 STEP 3: Setting up environment variables...
   ✅ Set IN_MY_HEAD_ROOT = C:\Users\sgbil\In My Head

📝 STEP 4: Creating .env files...
   ✅ Created: services\document-processor\.env
   ✅ Created: services\api-gateway\.env
   ✅ Created: .env (root)

🐍 STEP 5: Installing Python dependencies...
   ✅ Python dependencies installed

📦 STEP 6: Installing Node.js dependencies...
   ✅ Node.js dependencies installed

🗄️  STEP 7: Setting up database...
   ✅ Database containers started

🔄 STEP 8: Running database migrations...
   ✅ Database migrations applied

🌱 STEP 9: Seeding database with test data...
   ✅ Database seeded with test data

╔══════════════════════════════════════════════════════════════════╗
║             ENVIRONMENT SETUP COMPLETE ✅                         ║
╚══════════════════════════════════════════════════════════════════╝
```

---

### **Step 3: Verify Everything Works**

Check that your environment is ready:

```powershell
# Check Docker containers are running
docker ps

# Expected: postgres, redis, qdrant, minio containers running

# Test database connection
cd services\document-processor
python -c "from src.database.connection import check_health; check_health()"

# Expected output: "Database connection healthy!"
```

---

### **Step 4: Clean Up (Optional)**

Once you've verified everything works, you can delete the backup:

```powershell
# Find the backup folder (it has a timestamp)
Get-ChildItem "C:\Users\sgbil\In My Head" -Directory | Where-Object { $_.Name -like "*backup*" }

# Delete the backup (replace timestamp with your actual backup folder name)
Remove-Item "C:\Users\sgbil\In My Head\in-my-head-backup-20251005-123456" -Recurse -Force
```

---

## 🎯 UTILITY SCRIPTS CREATED

After setup, you'll have these convenient scripts:

### **start-all.ps1**

Starts all Docker services (PostgreSQL, Redis, Qdrant, MinIO)

```powershell
.\start-all.ps1
```

### **stop-all.ps1**

Stops all Docker services

```powershell
.\stop-all.ps1
```

---

## 🔗 SERVICE URLS

After environment setup, services will be available at:

| Service        | URL                     | Purpose         |
| -------------- | ----------------------- | --------------- |
| **PostgreSQL** | `localhost:5432`        | Main database   |
| **Redis**      | `localhost:6379`        | Caching         |
| **Qdrant**     | `http://localhost:6333` | Vector database |
| **MinIO**      | `http://localhost:9000` | Object storage  |

---

## 🔑 TEST CREDENTIALS

The seed script creates a test user:

- **Username:** `testuser`
- **Password:** `Test123!`
- **Email:** `test@inmyhead.local`

**Test Data Included:**

- 4 Collections: Work, Personal, Research, Archive
- 7 Tags: Important, TODO, Ideas, Reference, Learning, Archive, Meeting Notes

---

## 📝 POST-SETUP TASKS

After running both scripts:

### **1. Restart Your Terminal/IDE**

The environment variable `IN_MY_HEAD_ROOT` requires a restart to take effect.

### **2. Update IDE Workspace**

If you use VS Code or another IDE, update your workspace folder:

- **Old:** `C:\Users\sgbil\In My Head\in-my-head`
- **New:** `C:\Users\sgbil\In My Head`

### **3. Review .env Files**

Check the generated `.env` files and update any passwords/secrets:

- `.env` (root)
- `services\document-processor\.env`
- `services\api-gateway\.env`

**Important:** Change default passwords before production!

### **4. Update Git Remote (if needed)**

If you have a remote repository, update the paths:

```powershell
cd "C:\Users\sgbil\In My Head"
git remote -v  # Check current remotes
# Update if needed
```

### **5. Commit Changes**

Commit the structure change to Git:

```powershell
git add .
git commit -m "Flatten project structure - remove nested in-my-head folder"
git push
```

---

## ⚠️ TROUBLESHOOTING

### **Problem: "Docker is not running"**

**Solution:** Start Docker Desktop and wait for it to fully start, then re-run the script.

### **Problem: "Permission denied"**

**Solution:** Run PowerShell as Administrator:

```powershell
Start-Process powershell -Verb RunAs
```

### **Problem: "Python/Node.js not found"**

**Solution:** Install missing tools:

- Python: https://www.python.org/downloads/
- Node.js: https://nodejs.org/

### **Problem: "Database connection failed"**

**Solution:** Ensure Docker containers are running:

```powershell
docker ps
docker-compose -f infrastructure\docker\docker-compose.yml up -d
```

### **Problem: "Migration failed"**

**Solution:** Check database is accessible and try manually:

```powershell
cd services\document-processor
alembic upgrade head
```

---

## 🔄 ROLLBACK (If Needed)

If something goes wrong, you can restore from backup:

```powershell
# Find your backup folder
Get-ChildItem "C:\Users\sgbil\In My Head" -Directory | Where-Object { $_.Name -like "*backup*" }

# Remove current files (be careful!)
# (Only do this if you're sure!)

# Restore from backup
Copy-Item -Path "C:\Users\sgbil\In My Head\in-my-head-backup-TIMESTAMP\*" `
          -Destination "C:\Users\sgbil\In My Head\in-my-head" `
          -Recurse -Force
```

---

## 📚 ADDITIONAL RESOURCES

- **Phase 2 Documentation:** `docs\PHASE_2_COMPLETE.md`
- **Quick Reference:** `docs\PHASE_2_QUICK_REFERENCE.md`
- **Database Setup:** `services\document-processor\README.md`
- **Project README:** `README.md`

---

## ✅ VERIFICATION CHECKLIST

After completing all steps:

- [ ] Project structure is flattened (no nested `in-my-head\` folder)
- [ ] All files are at root level (`services\`, `docs\`, etc.)
- [ ] `.env` files created for all services
- [ ] Python dependencies installed
- [ ] Node.js dependencies installed
- [ ] Docker containers running
- [ ] Database migrations applied
- [ ] Test data seeded
- [ ] Can connect to database successfully
- [ ] Git repository still works
- [ ] IDE/terminal updated to new paths

---

## 🎉 SUCCESS!

Once all steps are complete, your development environment is ready to go!

**Next:** Proceed to Phase 3 - Microservices Implementation 🚀

---

**Questions or Issues?**
Refer to the main project documentation or Phase 2 completion reports in the `docs\` folder.

**Happy Coding!** ✨
