# Create Desktop Shortcut for In My Head
# ========================================

$WScriptShell = New-Object -ComObject WScript.Shell

# Get paths
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$BatFile = Join-Path $ScriptPath "Start_InMyHead.bat"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "In My Head.lnk"

# Create shortcut
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $BatFile
$Shortcut.WorkingDirectory = $ScriptPath
$Shortcut.Description = "In My Head - AI Knowledge Management System"
$Shortcut.IconLocation = "shell32.dll,222"  # Brain/lightbulb icon
$Shortcut.Save()

Write-Host ""
Write-Host "✅ Desktop shortcut created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Shortcut location: $ShortcutPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now double-click 'In My Head' on your desktop to launch the app!" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to close"
