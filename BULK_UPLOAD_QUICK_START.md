# 🚀 Quick Start: Bulk Upload

## Three Easy Methods

### 1️⃣ PowerShell Script (Fastest)

```powershell
# Interactive mode
.\Bulk_Upload_Documents.ps1

# Upload entire Documents folder
.\Bulk_Upload_Documents.ps1 -SourcePath "$env:USERPROFILE\Documents"
```

### 2️⃣ Desktop App Button

1. Click **"📁 Bulk Upload Folder"**
2. Select folder
3. Confirm file list
4. Click **"⬆️ Upload Files"**

### 3️⃣ Drag & Drop

1. Select multiple files in File Explorer
2. Drag into desktop app
3. Click **"⬆️ Upload Files"**

---

## Supported File Types

✅ PDF, Word, Text, Markdown, HTML, RTF, ODT, EPUB

## Default Settings

- **Max file size:** 50 MB
- **Scan subfolders:** Yes
- **Files copied, not moved:** Your originals are safe!

---

## Quick Examples

```powershell
# Preview what would be uploaded (no actual upload)
.\Bulk_Upload_Documents.ps1 -DryRun

# Upload only PDFs from Downloads
.\Bulk_Upload_Documents.ps1 -SourcePath "$env:USERPROFILE\Downloads" -FileTypes @("*.pdf")

# Upload Desktop files (non-recursive)
.\Bulk_Upload_Documents.ps1 -SourcePath "$env:USERPROFILE\Desktop" -Recursive:$false
```

---

**📖 Full Documentation:** See `BULK_UPLOAD_GUIDE.md`
