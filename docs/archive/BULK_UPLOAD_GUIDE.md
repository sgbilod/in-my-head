# 📚 Bulk Upload Guide - In My Head

## Overview

You have **3 ways** to bulk upload documents:

1. **PowerShell Script** (Recommended for large collections)
2. **Desktop App Bulk Upload** (Easy GUI method)
3. **Drag-and-Drop Multiple Files** (Quick for small batches)

---

## Method 1: PowerShell Bulk Upload Script 🚀

**Best for:** Uploading hundreds or thousands of files from specific folders.

### Quick Start

```powershell
# Interactive mode (will ask you which folder)
.\Bulk_Upload_Documents.ps1

# Upload entire Documents folder recursively
.\Bulk_Upload_Documents.ps1 -SourcePath "$env:USERPROFILE\Documents" -Recursive

# Upload Downloads folder (non-recursive)
.\Bulk_Upload_Documents.ps1 -SourcePath "$env:USERPROFILE\Downloads" -Recursive:$false

# Dry run (see what would be uploaded without actually uploading)
.\Bulk_Upload_Documents.ps1 -SourcePath "C:\MyDocs" -DryRun
```

### Advanced Options

```powershell
# Upload only specific file types
.\Bulk_Upload_Documents.ps1 -FileTypes @("*.pdf", "*.docx", "*.txt")

# Limit file size (default 50MB)
.\Bulk_Upload_Documents.ps1 -MaxFileSizeMB 100

# Process in larger batches
.\Bulk_Upload_Documents.ps1 -BatchSize 10
```

### Supported File Types

The script automatically finds:

- **Documents**: `.pdf`, `.docx`, `.doc`, `.txt`, `.md`, `.rtf`, `.odt`
- **Web**: `.html`, `.htm`
- **Ebooks**: `.epub`

### What It Does

1. ✅ Scans folder for supported documents
2. ✅ Shows file type breakdown
3. ✅ Filters by size (skips files >50MB by default)
4. ✅ Asks for confirmation before uploading
5. ✅ Shows progress and statistics
6. ✅ Automatically generates embeddings after upload
7. ✅ Saves list of failed uploads (if any)

### Example Output

```
╔════════════════════════════════════════════════════╗
║  🧠 In My Head - Bulk Document Upload             ║
╚════════════════════════════════════════════════════╝

🔍 Checking Document Processor service...
   ✅ Service is running!

📊 Scan Configuration:
   Source: C:\Users\YourName\Documents
   Recursive: True
   File Types: *.pdf, *.docx, *.txt, *.md
   Max Size: 50 MB
   Batch Size: 5 files at a time

🔍 Scanning for documents...

📋 Scan Results:
   Total files found: 347
   Files to upload: 342
   Files too large: 5

📊 File Types:
   .pdf: 156 files
   .docx: 98 files
   .txt: 65 files
   .md: 23 files

⚠️  Ready to upload 342 files
Continue with upload? (yes/no): yes

🚀 Starting upload...

[0.3%] Uploading: Research_Paper.pdf
         ✅ Success
[0.6%] Uploading: Meeting_Notes.docx
         ✅ Success
...

╔════════════════════════════════════════════════════╗
║              Upload Complete!                      ║
╚════════════════════════════════════════════════════╝

📊 Summary:
   ✅ Successful: 340 files
   ❌ Failed: 2 files
   ⏱️  Duration: 187.3 seconds
   📦 Total Uploaded: 2,456.78 MB
   ⚡ Throughput: 1.82 files/sec

🤖 Generating embeddings for uploaded documents...
   ✅ Embeddings generated successfully!

🎉 Bulk upload completed!
```

---

## Method 2: Desktop App Bulk Upload 📁

**Best for:** Visual folder selection with GUI.

### Steps

1. **Open the Desktop App**

   ```powershell
   .\Start_InMyHead.ps1
   ```

2. **Click "📁 Bulk Upload Folder"** button

3. **Select folder** in the file browser

4. **Choose recursive option**

   - Yes: Scan all subfolders
   - No: Only scan selected folder

5. **Review file list** and confirm

6. **Click "⬆️ Upload Files"**

### Features

- ✅ Visual folder browser
- ✅ Automatic file type detection
- ✅ Shows file count and types before upload
- ✅ Adds files to queue for review
- ✅ Can remove unwanted files before uploading

---

## Method 3: Drag-and-Drop Multiple Files 🖱️

**Best for:** Quick uploads of 10-50 files.

### Steps

1. **Open File Explorer** and select multiple files:

   - Click first file
   - Hold `Ctrl` and click additional files
   - Or select a range with `Shift + Click`

2. **Drag selected files** into the desktop app window

3. **Drop onto the blue dashed area**

4. **Click "⬆️ Upload Files"**

### Tips

- You can drag from multiple folders sequentially
- Files appear in the list before upload
- Remove unwanted files with the "🗑️ Clear List" button

---

## Recommended Workflows

### Workflow 1: Initial Library Setup (Thousands of Files)

```powershell
# 1. Upload entire Documents folder
.\Bulk_Upload_Documents.ps1 -SourcePath "$env:USERPROFILE\Documents"

# 2. Upload Downloads
.\Bulk_Upload_Documents.ps1 -SourcePath "$env:USERPROFILE\Downloads"

# 3. Upload Desktop files
.\Bulk_Upload_Documents.ps1 -SourcePath "$env:USERPROFILE\Desktop"
```

### Workflow 2: Selective Upload by File Type

```powershell
# Only PDFs
.\Bulk_Upload_Documents.ps1 -FileTypes @("*.pdf")

# Only text documents
.\Bulk_Upload_Documents.ps1 -FileTypes @("*.txt", "*.md")

# Only Office documents
.\Bulk_Upload_Documents.ps1 -FileTypes @("*.docx", "*.doc", "*.odt")
```

### Workflow 3: Cautious Upload (Preview First)

```powershell
# 1. Dry run to see what would be uploaded
.\Bulk_Upload_Documents.ps1 -SourcePath "C:\MyImportantDocs" -DryRun

# 2. If satisfied, run actual upload
.\Bulk_Upload_Documents.ps1 -SourcePath "C:\MyImportantDocs"
```

---

## Performance Tips

### For Best Upload Speed

1. **Use PowerShell script** for large batches (fastest)
2. **Close other applications** to free up resources
3. **Use SSD** if possible (faster file reading)
4. **Batch size**: Default (5) works well for most cases
5. **Network**: Ensure Docker has sufficient resources

### Expected Throughput

| Method            | Speed         | Use Case       |
| ----------------- | ------------- | -------------- |
| PowerShell Script | 1-3 files/sec | Bulk uploads   |
| Desktop App       | 1-2 files/sec | Medium batches |
| Drag-and-Drop     | 1 file/sec    | Small batches  |

**Note:** Actual speed depends on:

- File sizes
- Document complexity (PDFs with images slower)
- System resources
- Docker configuration

---

## Troubleshooting

### "Document Processor is not running"

**Solution:**

```powershell
.\Start_InMyHead.ps1
```

Wait for all services to show green checkmarks.

### "Failed to upload some files"

**Common causes:**

1. **File is open** in another program (Word, Adobe, etc.)
   - Close the application and retry
2. **File is corrupted**
   - Skip and continue with others
3. **Permission denied**
   - Run as administrator or move files to accessible location
4. **File size too large**
   - Increase limit: `-MaxFileSizeMB 100`

### Upload is very slow

**Solutions:**

1. Reduce batch size: `-BatchSize 3`
2. Close other applications
3. Increase Docker memory allocation (Docker Desktop → Settings → Resources)
4. Upload smaller subsets at a time

### "Out of memory" error

**Solutions:**

1. Upload in smaller batches
2. Restart Docker Desktop
3. Increase Docker memory:
   - Docker Desktop → Settings → Resources
   - Set memory to at least 8GB (recommended 16GB)

---

## Post-Upload Actions

### 1. Verify Upload

Open web interface:

```powershell
# Or click "Open Web Interface" in desktop app
start http://localhost:8001/docs
```

Navigate to `/documents/` endpoint to see all uploaded documents.

### 2. Generate Embeddings

Embeddings are auto-generated, but you can manually trigger:

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/search/generate-embeddings" -Method Post
```

### 3. Test Search

Try semantic search:

```powershell
$body = @{
    query = "artificial intelligence"
    top_k = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/search/semantic" -Method Post -Body $body -ContentType "application/json"
```

---

## Supported File Types

| Category      | Extensions                 | Notes                    |
| ------------- | -------------------------- | ------------------------ |
| **PDF**       | `.pdf`                     | Best compatibility       |
| **Word**      | `.docx`, `.doc`, `.odt`    | Requires text extraction |
| **Text**      | `.txt`, `.md`, `.markdown` | Fastest processing       |
| **Web**       | `.html`, `.htm`            | HTML parsing             |
| **Rich Text** | `.rtf`                     | Formatted text           |
| **Ebooks**    | `.epub`                    | E-book format            |

### File Size Limits

- **Default max:** 50 MB
- **Recommended:** Under 25 MB for best performance
- **Increase limit:** Use `-MaxFileSizeMB` parameter

---

## Common Use Cases

### Use Case 1: Academic Research Library

```powershell
# Upload research papers and notes
.\Bulk_Upload_Documents.ps1 -SourcePath "C:\Research" -FileTypes @("*.pdf", "*.md", "*.txt")
```

### Use Case 2: Work Documents Archive

```powershell
# Upload all work documents
.\Bulk_Upload_Documents.ps1 -SourcePath "C:\Work" -Recursive
```

### Use Case 3: Personal Knowledge Base

```powershell
# Upload notes, articles, and downloads
.\Bulk_Upload_Documents.ps1 -SourcePath "$env:USERPROFILE\Documents\Notes"
.\Bulk_Upload_Documents.ps1 -SourcePath "$env:USERPROFILE\Downloads" -FileTypes @("*.pdf")
```

### Use Case 4: Code Documentation

```powershell
# Upload markdown documentation
.\Bulk_Upload_Documents.ps1 -SourcePath "C:\Projects" -FileTypes @("*.md", "*.txt") -Recursive
```

---

## FAQ

**Q: Can I upload the same file twice?**
A: Yes, but it will create a duplicate entry. The system doesn't prevent duplicates (yet).

**Q: What happens to my original files?**
A: They remain untouched. Uploads create copies in the system storage.

**Q: Can I cancel a bulk upload?**
A: Press `Ctrl+C` in PowerShell. Partially uploaded files will remain in the system.

**Q: How do I delete uploaded documents?**
A: Use the API or wait for the delete feature in the desktop app (coming soon).

**Q: Can I upload files from network drives?**
A: Yes, but it will be slower. Copy to local drive first for best performance.

**Q: Will it upload hidden files?**
A: No, hidden files are automatically skipped.

---

## Next Steps

After bulk upload:

1. ✅ **Search your documents**

   - Try semantic search in web interface
   - Ask questions about your documents

2. ✅ **Organize with tags**

   - Add tags to uploaded documents (via API)

3. ✅ **Create collections**

   - Group related documents (via API)

4. ✅ **Set up regular uploads**
   - Create scheduled task for automatic uploads
   - Example: Upload new files from Downloads daily

---

## Support

For issues or questions:

- Check `DESKTOP_APP_README.md` for troubleshooting
- View upload logs in the desktop app ("View Logs" button)
- Check Docker logs if services fail

---

**Happy uploading! 🎉 Your knowledge base awaits!**
