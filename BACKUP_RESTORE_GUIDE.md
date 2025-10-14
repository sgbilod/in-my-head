# 🔒 Backup & Restore Guide - In My Head

## Quick Access

### Desktop Application (Recommended)

The easiest way to backup and restore is through the desktop app:

1. **Launch App:** `.\Start_InMyHead.ps1` or double-click `InMyHead.py`
2. **Backup:** Click "💾 Backup Data" button
3. **Restore:** Click "🔄 Restore Data" button
4. **Settings:** Menu Bar → File → Settings (or press Ctrl+,)

---

## 💾 Backup Your Data

### Method 1: Desktop App (One-Click)

1. Click **"💾 Backup Data"** button
2. Confirm the backup operation
3. Wait for completion (progress shown in dialog)
4. Backup saved to `backups/backup_YYYYMMDD_HHMMSS/`

**What Gets Backed Up:**

- ✅ All uploaded documents (MinIO)
- ✅ Document metadata (PostgreSQL)
- ✅ Vector embeddings (Qdrant)
- ✅ Cache data (Redis)
- ✅ Configuration files (.env, docker-compose.yml)

### Method 2: PowerShell Script

```powershell
# Basic backup
.\Backup_Data.ps1

# Include AI models (larger backup)
.\Backup_Data.ps1 -IncludeAIModels

# Custom backup location
.\Backup_Data.ps1 -BackupPath "D:\MyBackups"
```

**Optional ZIP Archive:**

- Script asks if you want to create a ZIP archive
- Recommended for portability and storage efficiency

---

## 🔄 Restore Your Data

### Method 1: Desktop App (Interactive)

1. Click **"🔄 Restore Data"** button
2. Select backup from the list (shows date and type)
3. Confirm the restore operation
4. Wait for completion (services automatically restarted)

**Automatic Detection:**

- App scans `backups/` folder
- Shows both folder and ZIP backups
- Displays backup date and size

### Method 2: PowerShell Script

```powershell
# Interactive restore (shows menu)
.\Restore_Data.ps1

# Restore specific backup
.\Restore_Data.ps1 -BackupPath ".\backups\backup_20251014_143022"

# Restore from ZIP
.\Restore_Data.ps1 -BackupPath ".\backups\backup_20251014_143022.zip"

# Skip confirmation (use with caution!)
.\Restore_Data.ps1 -BackupPath ".\backups\backup_20251014_143022" -Force
```

---

## ⚙️ Settings & Configuration

### Access Settings

**Desktop App:**

- Menu Bar → **File → Settings**
- Or use system tray → **Settings**

**Config File:**

- Located at: `config.json`
- Auto-created on first run

### Available Settings

#### 📤 Upload Settings

| Setting               | Default | Description                       |
| --------------------- | ------- | --------------------------------- |
| **Max File Size**     | 100 MB  | Maximum file size for uploads     |
| **Batch Upload Size** | 5       | Number of files processed at once |
| **Auto Embeddings**   | Yes     | Generate embeddings automatically |
| **API Timeout**       | 30 sec  | Timeout for API requests          |

#### 💾 Backup Settings

| Setting             | Default     | Description              |
| ------------------- | ----------- | ------------------------ |
| **Backup Location** | `./backups` | Where backups are stored |

#### 📄 File Types

Configure supported file extensions for uploads:

- `.pdf` - PDF documents
- `.docx` / `.doc` - Word documents
- `.txt` - Plain text files
- `.md` / `.markdown` - Markdown files
- `.html` / `.htm` - Web pages
- `.rtf` - Rich text format
- `.odt` - OpenDocument text
- `.epub` - E-books

### Change Upload File Size Limit

**Method 1: Desktop App Settings**

1. Open Settings (File → Settings)
2. Go to "Upload" tab
3. Change "Max File Size" value
4. Click "Save Settings"

**Method 2: Edit Config File**

```json
{
  "max_file_size_mb": 200,
  "batch_size": 10,
  "auto_generate_embeddings": true,
  "backup_path": "./backups",
  "api_timeout": 60
}
```

**Method 3: Server Configuration**
Edit `services/document-processor/src/api/routes_documents.py`:

```python
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB
```

Then rebuild:

```powershell
cd infrastructure/docker
docker-compose -f docker-compose.dev.yml up -d --build document-processor
```

---

## 📋 Menu Bar Features

### File Menu

- **⚙️ Settings** - Open settings dialog
- **❌ Quit** - Exit application

### Tools Menu

- **💾 Backup Data** - Create data backup
- **🔄 Restore Data** - Restore from backup
- **📁 Bulk Upload** - Bulk upload folder

### Help Menu

- **📚 Documentation** - Open API documentation
- **ℹ️ About** - About In My Head

---

## 🔐 Best Practices

### Backup Schedule

**Recommended:**

- **Daily:** If actively uploading documents
- **Weekly:** For moderate use
- **Before major changes:** Always backup first!

**Automated Backup (Optional):**
Create Windows scheduled task:

```powershell
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File 'C:\Users\sgbil\In My Head\Backup_Data.ps1'"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "InMyHead_Backup"
```

### Storage Strategy

**3-2-1 Backup Rule:**

- **3** copies of your data
- **2** different storage media
- **1** copy offsite

**Example:**

1. **Primary:** Live data in Docker volumes
2. **Local Backup:** `backups/` folder on same computer
3. **External Backup:** Copy to external hard drive
4. **Cloud Backup (Optional):** Upload to OneDrive/Dropbox

### Before Restore

**ALWAYS:**

1. ✅ Create a backup of current data first
2. ✅ Verify backup integrity (check file sizes)
3. ✅ Understand you'll lose data added after backup
4. ✅ Have restore script ready to go

---

## 🚨 Troubleshooting

### Backup Issues

**Problem:** "Docker is not running"

- **Solution:** Start Docker Desktop first

**Problem:** Backup fails with permission error

- **Solution:** Run PowerShell as Administrator

**Problem:** Backup is very large

- **Solution:**
  - Exclude AI models (don't use `-IncludeAIModels`)
  - Clean up old documents before backup
  - Use ZIP compression

### Restore Issues

**Problem:** "No backups found"

- **Solution:** Check `backups/` folder exists and contains backup files

**Problem:** Restore stuck at "Starting services"

- **Solution:** Wait 30-60 seconds for Docker containers to initialize

**Problem:** Services won't start after restore

- **Solution:**
  ```powershell
  cd infrastructure/docker
  docker-compose -f docker-compose.dev.yml down
  docker-compose -f docker-compose.dev.yml up -d
  ```

### Settings Issues

**Problem:** Settings not saving

- **Solution:** Check write permissions for `config.json`

**Problem:** File size limit not applying

- **Solution:**
  - Desktop app setting only affects client-side validation
  - Server setting requires container rebuild

---

## 📊 What's in a Backup?

### Folder Structure

```
backups/
└── backup_20251014_143022/
    ├── inmyhead_postgres_data.tar.gz    (245 MB)
    ├── inmyhead_qdrant_data.tar.gz      (1.2 GB)
    ├── inmyhead_minio_data.tar.gz       (3.4 GB)
    ├── inmyhead_redis_data.tar.gz       (12 MB)
    ├── docker-compose.dev.yml           (Config)
    ├── .env                             (Environment)
    ├── manifest.json                    (Metadata)
    └── README.txt                       (Instructions)
```

### Manifest File

```json
{
  "timestamp": "20251014_143022",
  "date": "2025-10-14 14:30:22",
  "volumes": [
    "inmyhead_postgres_data",
    "inmyhead_qdrant_data",
    "inmyhead_minio_data",
    "inmyhead_redis_data"
  ],
  "backup_location": "C:\\Users\\sgbil\\In My Head\\backups\\backup_20251014_143022",
  "machine": "YOUR-PC",
  "user": "sgbil"
}
```

---

## 💡 Pro Tips

### Faster Backups

- Exclude cache volumes (they're regenerated)
- Use SSD for backup storage
- Compress with ZIP for long-term storage

### Verify Backups

```powershell
# Check backup contents
Get-ChildItem "backups\backup_*" -Recurse | Select-Object Name, Length, LastWriteTime

# Test restore on another machine
# Better to discover issues before you need it!
```

### Backup Before Updates

```powershell
# Always backup before updating
.\Backup_Data.ps1

# Then update
cd infrastructure/docker
docker-compose -f docker-compose.dev.yml pull
docker-compose -f docker-compose.dev.yml up -d
```

### Quick Restore Test

```powershell
# Restore to a test directory
.\Restore_Data.ps1 -BackupPath ".\backups\backup_20251014_143022"

# If successful, your backups are good!
```

---

## 🎯 Quick Reference

### Keyboard Shortcuts (Desktop App)

- **Ctrl+S** - Open Settings
- **Ctrl+B** - Backup Data
- **Ctrl+R** - Restore Data
- **Ctrl+L** - Toggle Logs
- **Ctrl+Q** - Quit Application

### System Tray Actions

- **Left Click** - Show/Hide window
- **Right Click** - Context menu
  - Show Window
  - Open Web Interface
  - Backup Data
  - Restore Data
  - Settings
  - Quit

---

## 📞 Need Help?

**Check Logs:**

- Desktop App → Click "📋 View Logs"
- PowerShell scripts show detailed progress

**Common Issues:**

- [Backup Issues](#backup-issues)
- [Restore Issues](#restore-issues)
- [Settings Issues](#settings-issues)

**Get Support:**

- Check `README.md` for general help
- Review `DATA_SECURITY_GUIDE.md` for security info
- Check GitHub issues for known problems

---

**Last Updated:** October 14, 2025  
**Version:** 1.0.0
