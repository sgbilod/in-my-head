"""
In My Head - Desktop Application Launcher
==========================================
One-click desktop application with drag-and-drop file upload.

This application:
- Starts all Docker services automatically
- Provides a modern GUI with drag-and-drop file upload
- Monitors service health
- Opens web interface automatically
- Shows system tray icon for easy access
"""

import sys
import os
import subprocess
import time
import webbrowser
import threading
from pathlib import Path
from typing import Optional, List, Dict
import json
import requests
from datetime import datetime

# GUI imports
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QTextEdit, QProgressBar, QSystemTrayIcon,
        QMenu, QFileDialog, QListWidget, QListWidgetItem, QMessageBox,
        QFrame, QSplitter, QDialog, QFormLayout, QLineEdit, QSpinBox,
        QCheckBox, QComboBox, QTabWidget, QGroupBox
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QMimeData, QUrl
    from PyQt6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent, QColor, QPalette
except ImportError:
    print("ERROR: PyQt6 not installed. Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6", "requests"])
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QTextEdit, QProgressBar, QSystemTrayIcon,
        QMenu, QFileDialog, QListWidget, QListWidgetItem, QMessageBox,
        QFrame, QSplitter, QDialog, QFormLayout, QLineEdit, QSpinBox,
        QCheckBox, QComboBox, QTabWidget, QGroupBox
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QMimeData, QUrl
    from PyQt6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent, QColor, QPalette


class ServiceManager(QThread):
    """Manages Docker services in background thread"""

    status_update = pyqtSignal(str, str)  # service_name, status
    log_message = pyqtSignal(str)
    all_services_ready = pyqtSignal()

    def __init__(self, project_root: Path):
        super().__init__()
        self.project_root = project_root
        self.docker_compose_path = project_root / "infrastructure" / "docker"
        self.running = True
        self.services = [
            ("postgres", "http://localhost:5432", "Database"),
            ("redis", "http://localhost:6379", "Cache"),
            ("qdrant", "http://localhost:6333", "Vector DB"),
            ("document-processor", "http://localhost:8001/health", "API"),
        ]

    def run(self):
        """Start Docker services and monitor health"""
        self.log_message.emit("🚀 Starting In My Head services...")

        # Check if Docker is running
        if not self.check_docker():
            self.log_message.emit("❌ Docker is not running. Please start Docker Desktop first.")
            return

        # Start Docker Compose services
        self.start_docker_services()

        # Monitor service health
        self.monitor_services()

    def check_docker(self) -> bool:
        """Check if Docker daemon is running"""
        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            self.log_message.emit(f"Docker check failed: {e}")
            return False

    def start_docker_services(self):
        """Start all Docker services"""
        try:
            self.log_message.emit("📦 Starting Docker containers...")

            cmd = [
                "docker-compose",
                "-f", "docker-compose.dev.yml",
                "up", "-d"
            ]

            process = subprocess.Popen(
                cmd,
                cwd=str(self.docker_compose_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Stream output
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.log_message.emit(f"  {line}")

            process.wait()

            if process.returncode == 0:
                self.log_message.emit("✅ Docker containers started successfully!")
            else:
                self.log_message.emit(f"⚠️ Docker startup completed with warnings")

        except Exception as e:
            self.log_message.emit(f"❌ Failed to start Docker services: {e}")

    def monitor_services(self):
        """Monitor service health and update status"""
        self.log_message.emit("\n🔍 Checking service health...\n")

        max_retries = 30
        retry_delay = 2

        for retry in range(max_retries):
            if not self.running:
                break

            all_healthy = True

            for service_name, url, display_name in self.services:
                if not self.running:
                    break

                status = self.check_service_health(service_name, url)
                self.status_update.emit(service_name, status)

                if status != "healthy":
                    all_healthy = False

            if all_healthy:
                self.log_message.emit("\n✅ All services are healthy and ready!")
                self.all_services_ready.emit()
                break

            if retry < max_retries - 1:
                time.sleep(retry_delay)

        if not all_healthy:
            self.log_message.emit("\n⚠️ Some services failed to start. Check Docker logs.")

    def check_service_health(self, service_name: str, url: str) -> str:
        """Check if a service is healthy"""
        try:
            # Special handling for different services
            if "postgres" in service_name:
                # Check Docker container status
                result = subprocess.run(
                    ["docker", "ps", "--filter", f"name={service_name}", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "Up" in result.stdout and "healthy" in result.stdout:
                    return "healthy"
                elif "Up" in result.stdout:
                    return "starting"
                return "stopped"

            elif "redis" in service_name or "qdrant" in service_name:
                result = subprocess.run(
                    ["docker", "ps", "--filter", f"name={service_name}", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return "healthy" if "Up" in result.stdout else "stopped"

            else:
                # HTTP health check
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    return "healthy"
                return "starting"

        except requests.exceptions.RequestException:
            return "starting"
        except Exception as e:
            return "error"

    def stop(self):
        """Stop monitoring"""
        self.running = False
        self.wait()

    def shutdown_services(self):
        """Shutdown all Docker services"""
        try:
            self.log_message.emit("\n🛑 Shutting down services...")

            subprocess.run(
                ["docker-compose", "-f", "docker-compose.dev.yml", "down"],
                cwd=str(self.docker_compose_path),
                timeout=30
            )

            self.log_message.emit("✅ Services stopped successfully")
        except Exception as e:
            self.log_message.emit(f"⚠️ Error stopping services: {e}")


class FileUploadWidget(QWidget):
    """Drag-and-drop file upload widget"""

    files_uploaded = pyqtSignal(list)  # List of uploaded file paths

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.uploaded_files = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Drop zone
        self.drop_zone = QFrame()
        self.drop_zone.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.drop_zone.setLineWidth(2)
        self.drop_zone.setStyleSheet("""
            QFrame {
                background-color: #f0f8ff;
                border: 3px dashed #4a90e2;
                border-radius: 10px;
                min-height: 150px;
            }
            QFrame:hover {
                background-color: #e6f2ff;
                border-color: #2e6da4;
            }
        """)

        drop_layout = QVBoxLayout()
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.drop_label = QLabel("📁 Drag & Drop Files Here\n\nor click to browse")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                color: #4a90e2;
                font-size: 16px;
                font-weight: bold;
                padding: 20px;
            }
        """)

        drop_layout.addWidget(self.drop_label)
        self.drop_zone.setLayout(drop_layout)
        self.drop_zone.mousePressEvent = lambda e: self.browse_files()

        layout.addWidget(self.drop_zone)

        # File list
        list_label = QLabel("📋 Files to Upload:")
        list_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(list_label)

        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(150)
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
        """)
        layout.addWidget(self.file_list)

        # Buttons
        button_layout = QHBoxLayout()

        self.browse_btn = QPushButton("📂 Browse Files")
        self.browse_btn.clicked.connect(self.browse_files)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)

        self.bulk_upload_btn = QPushButton("📁 Bulk Upload Folder")
        self.bulk_upload_btn.clicked.connect(self.bulk_upload_folder)
        self.bulk_upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)

        self.clear_btn = QPushButton("🗑️ Clear List")
        self.clear_btn.clicked.connect(self.clear_files)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)

        self.upload_btn = QPushButton("⬆️ Upload Files")
        self.upload_btn.clicked.connect(self.upload_files)
        self.upload_btn.setEnabled(False)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)

        button_layout.addWidget(self.browse_btn)
        button_layout.addWidget(self.bulk_upload_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.upload_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_zone.setStyleSheet("""
                QFrame {
                    background-color: #d4edda;
                    border: 3px dashed #28a745;
                    border-radius: 10px;
                    min-height: 150px;
                }
            """)

    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.drop_zone.setStyleSheet("""
            QFrame {
                background-color: #f0f8ff;
                border: 3px dashed #4a90e2;
                border-radius: 10px;
                min-height: 150px;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_files(files)
        self.drop_zone.setStyleSheet("""
            QFrame {
                background-color: #f0f8ff;
                border: 3px dashed #4a90e2;
                border-radius: 10px;
                min-height: 150px;
            }
        """)
        event.acceptProposedAction()

    def browse_files(self):
        """Open file browser"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Upload",
            "",
            "All Files (*);;Documents (*.pdf *.docx *.txt *.md);;Images (*.png *.jpg *.jpeg)"
        )
        if files:
            self.add_files(files)

    def bulk_upload_folder(self):
        """Open folder browser for bulk upload"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder for Bulk Upload",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            # Ask for recursive option
            reply = QMessageBox.question(
                self,
                "Recursive Scan?",
                "Do you want to scan subfolders recursively?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            recursive = (reply == QMessageBox.StandardButton.Yes)

            # Scan folder for documents
            self.scan_folder(folder, recursive)

    def scan_folder(self, folder: str, recursive: bool = True):
        """Scan folder for supported document types"""
        supported_extensions = ['.pdf', '.docx', '.doc', '.txt', '.md', '.markdown',
                               '.html', '.htm', '.rtf', '.odt', '.epub']

        files_found = []

        # Show progress dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Scanning Folder")
        progress.setText(f"Scanning: {folder}\n\nPlease wait...")
        progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress.show()
        QApplication.processEvents()

        try:
            folder_path = Path(folder)

            if recursive:
                for ext in supported_extensions:
                    files_found.extend(folder_path.rglob(f"*{ext}"))
            else:
                for ext in supported_extensions:
                    files_found.extend(folder_path.glob(f"*{ext}"))

            progress.close()

            if not files_found:
                QMessageBox.information(
                    self,
                    "No Files Found",
                    f"No supported documents found in:\n{folder}\n\n"
                    f"Supported types: {', '.join(supported_extensions)}"
                )
                return

            # Ask for confirmation
            file_types = {}
            for file in files_found:
                ext = file.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1

            type_breakdown = "\n".join([f"  {ext}: {count} files" for ext, count in sorted(file_types.items())])

            reply = QMessageBox.question(
                self,
                "Confirm Bulk Upload",
                f"Found {len(files_found)} documents:\n\n{type_breakdown}\n\n"
                f"Add all files to upload queue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                file_paths = [str(f) for f in files_found]
                self.add_files(file_paths)
                QMessageBox.information(
                    self,
                    "Files Added",
                    f"✅ Added {len(files_found)} files to upload queue!\n\n"
                    f"Click 'Upload Files' when ready."
                )

        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Scan Error",
                f"Error scanning folder:\n{str(e)}"
            )

    def add_files(self, files: List[str]):
        """Add files to upload list"""
        for file_path in files:
            if file_path not in self.uploaded_files:
                self.uploaded_files.append(file_path)
                item = QListWidgetItem(f"📄 {Path(file_path).name}")
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.file_list.addItem(item)

        self.upload_btn.setEnabled(len(self.uploaded_files) > 0)

    def clear_files(self):
        """Clear file list"""
        self.uploaded_files.clear()
        self.file_list.clear()
        self.upload_btn.setEnabled(False)

    def upload_files(self):
        """Upload files to document processor"""
        if not self.uploaded_files:
            return

        try:
            successful = 0
            failed = 0

            for file_path in self.uploaded_files:
                try:
                    with open(file_path, 'rb') as f:
                        files = {'file': (Path(file_path).name, f)}
                        response = requests.post(
                            'http://localhost:8001/documents/upload',
                            files=files,
                            timeout=30
                        )

                    if response.status_code == 200:
                        successful += 1
                    else:
                        failed += 1

                except Exception as e:
                    failed += 1

            # Show result
            if failed == 0:
                QMessageBox.information(
                    self,
                    "Upload Complete",
                    f"✅ Successfully uploaded {successful} file(s)!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Upload Completed with Errors",
                    f"✅ Uploaded: {successful}\n❌ Failed: {failed}"
                )

            self.clear_files()
            self.files_uploaded.emit(self.uploaded_files)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Upload Error",
                f"❌ Upload failed: {str(e)}\n\nMake sure the Document Processor service is running."
            )


class SettingsDialog(QDialog):
    """Settings configuration dialog"""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Settings")
        self.setMinimumSize(600, 500)
        self.load_settings()
        self.init_ui()

    def load_settings(self):
        """Load settings from config file"""
        config_file = Path("config.json")
        self.settings = {
            "max_file_size_mb": 100,
            "batch_size": 5,
            "auto_generate_embeddings": True,
            "backup_path": "./backups",
            "api_timeout": 30,
            "supported_extensions": [".pdf", ".docx", ".doc", ".txt", ".md",
                                    ".markdown", ".html", ".htm", ".rtf", ".odt", ".epub"]
        }

        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        """Save settings to config file"""
        try:
            with open("config.json", 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{str(e)}")
            return False

    def init_ui(self):
        """Initialize settings UI"""
        layout = QVBoxLayout()

        # Create tab widget
        tabs = QTabWidget()

        # Upload Settings Tab
        upload_tab = QWidget()
        upload_layout = QFormLayout()

        self.max_file_size = QSpinBox()
        self.max_file_size.setRange(1, 1000)
        self.max_file_size.setValue(self.settings["max_file_size_mb"])
        self.max_file_size.setSuffix(" MB")
        upload_layout.addRow("Max File Size:", self.max_file_size)

        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 50)
        self.batch_size.setValue(self.settings["batch_size"])
        upload_layout.addRow("Batch Upload Size:", self.batch_size)

        self.auto_embeddings = QCheckBox("Automatically generate embeddings after upload")
        self.auto_embeddings.setChecked(self.settings["auto_generate_embeddings"])
        upload_layout.addRow("", self.auto_embeddings)

        self.api_timeout = QSpinBox()
        self.api_timeout.setRange(10, 300)
        self.api_timeout.setValue(self.settings["api_timeout"])
        self.api_timeout.setSuffix(" seconds")
        upload_layout.addRow("API Timeout:", self.api_timeout)

        upload_tab.setLayout(upload_layout)
        tabs.addTab(upload_tab, "📤 Upload")

        # Backup Settings Tab
        backup_tab = QWidget()
        backup_layout = QFormLayout()

        backup_path_layout = QHBoxLayout()
        self.backup_path = QLineEdit(self.settings["backup_path"])
        browse_backup_btn = QPushButton("📁 Browse")
        browse_backup_btn.clicked.connect(self.browse_backup_path)
        backup_path_layout.addWidget(self.backup_path)
        backup_path_layout.addWidget(browse_backup_btn)
        backup_layout.addRow("Backup Location:", backup_path_layout)

        backup_tab.setLayout(backup_layout)
        tabs.addTab(backup_tab, "💾 Backup")

        # File Types Tab
        types_tab = QWidget()
        types_layout = QVBoxLayout()

        types_label = QLabel("Supported File Extensions (one per line):")
        types_layout.addWidget(types_label)

        self.extensions_text = QTextEdit()
        self.extensions_text.setMaximumHeight(200)
        self.extensions_text.setPlainText("\n".join(self.settings["supported_extensions"]))
        types_layout.addWidget(self.extensions_text)

        types_tab.setLayout(types_layout)
        tabs.addTab(types_tab, "📄 File Types")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Save Settings")
        save_btn.clicked.connect(self.on_save)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def browse_backup_path(self):
        """Browse for backup directory"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Directory",
            self.backup_path.text()
        )
        if path:
            self.backup_path.setText(path)

    def on_save(self):
        """Save settings and emit signal"""
        # Update settings dictionary
        self.settings["max_file_size_mb"] = self.max_file_size.value()
        self.settings["batch_size"] = self.batch_size.value()
        self.settings["auto_generate_embeddings"] = self.auto_embeddings.isChecked()
        self.settings["backup_path"] = self.backup_path.text()
        self.settings["api_timeout"] = self.api_timeout.value()

        # Parse extensions
        extensions_text = self.extensions_text.toPlainText()
        self.settings["supported_extensions"] = [
            ext.strip() for ext in extensions_text.split('\n')
            if ext.strip() and ext.strip().startswith('.')
        ]

        if self.save_settings():
            self.settings_changed.emit(self.settings)
            QMessageBox.information(self, "Success", "✅ Settings saved successfully!")
            self.accept()


class BackupRestoreWorker(QThread):
    """Worker thread for backup/restore operations"""

    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, operation: str, backup_path: str = ""):
        super().__init__()
        self.operation = operation  # 'backup' or 'restore'
        self.backup_path = backup_path
        self.project_root = Path(__file__).parent

    def run(self):
        """Execute backup or restore operation"""
        try:
            if self.operation == "backup":
                self.run_backup()
            elif self.operation == "restore":
                self.run_restore()
        except Exception as e:
            self.finished.emit(False, str(e))

    def run_backup(self):
        """Run backup script"""
        self.progress.emit("🔍 Checking Docker status...")

        # Check Docker
        if not self.check_docker():
            self.finished.emit(False, "Docker is not running")
            return

        self.progress.emit("💾 Starting backup process...")

        script_path = self.project_root / "Backup_Data.ps1"

        if not script_path.exists():
            self.finished.emit(False, "Backup script not found")
            return

        try:
            # Run PowerShell script
            process = subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(self.project_root)
            )

            # Stream output
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.progress.emit(line)

            process.wait()

            if process.returncode == 0:
                self.finished.emit(True, "Backup completed successfully!")
            else:
                self.finished.emit(False, "Backup completed with errors")

        except Exception as e:
            self.finished.emit(False, f"Backup failed: {str(e)}")

    def run_restore(self):
        """Run restore script"""
        self.progress.emit("🔍 Checking Docker status...")

        if not self.check_docker():
            self.finished.emit(False, "Docker is not running")
            return

        self.progress.emit("🔄 Starting restore process...")

        script_path = self.project_root / "Restore_Data.ps1"

        if not script_path.exists():
            self.finished.emit(False, "Restore script not found")
            return

        try:
            # Run PowerShell script with backup path
            args = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
            if self.backup_path:
                args.extend(["-BackupPath", self.backup_path, "-Force"])

            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(self.project_root)
            )

            # Stream output
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.progress.emit(line)

            process.wait()

            if process.returncode == 0:
                self.finished.emit(True, "Restore completed successfully!")
            else:
                self.finished.emit(False, "Restore completed with errors")

        except Exception as e:
            self.finished.emit(False, f"Restore failed: {str(e)}")

    def check_docker(self) -> bool:
        """Check if Docker is running"""
        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False


class InMyHeadApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.project_root = Path(__file__).parent
        self.service_manager = None
        self.services_ready = False
        self.settings = self.load_settings()

        self.init_ui()
        self.setup_system_tray()
        self.setup_menu_bar()
        self.start_services()

    def load_settings(self) -> Dict:
        """Load application settings"""
        config_file = Path("config.json")
        default_settings = {
            "max_file_size_mb": 100,
            "batch_size": 5,
            "auto_generate_embeddings": True,
            "backup_path": "./backups",
            "api_timeout": 30,
            "supported_extensions": [".pdf", ".docx", ".doc", ".txt", ".md",
                                    ".markdown", ".html", ".htm", ".rtf", ".odt", ".epub"]
        }

        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    loaded = json.load(f)
                    default_settings.update(loaded)
            except:
                pass

        return default_settings

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("In My Head - Knowledge Management System")
        self.setMinimumSize(900, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("🧠 In My Head")
        header.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 10px;
            }
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # Service status section
        status_group = QFrame()
        status_group.setFrameStyle(QFrame.Shape.Box)
        status_group.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        status_layout = QVBoxLayout()

        status_title = QLabel("📊 Service Status")
        status_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #495057;")
        status_layout.addWidget(status_title)

        self.status_labels = {}
        services = [
            ("postgres", "🗄️ PostgreSQL Database"),
            ("redis", "⚡ Redis Cache"),
            ("qdrant", "🔍 Qdrant Vector DB"),
            ("document-processor", "📄 Document Processor"),
        ]

        for service_id, service_name in services:
            label = QLabel(f"{service_name}: ⏳ Starting...")
            label.setStyleSheet("padding: 5px; font-size: 12px;")
            self.status_labels[service_id] = label
            status_layout.addWidget(label)

        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)

        # File upload section
        upload_group = QFrame()
        upload_group.setFrameStyle(QFrame.Shape.Box)
        upload_group.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        upload_layout = QVBoxLayout()

        upload_title = QLabel("📤 Upload Documents")
        upload_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #495057;")
        upload_layout.addWidget(upload_title)

        self.upload_widget = FileUploadWidget()
        upload_layout.addWidget(self.upload_widget)

        upload_group.setLayout(upload_layout)
        main_layout.addWidget(upload_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.open_web_btn = QPushButton("🌐 Open Web Interface")
        self.open_web_btn.clicked.connect(self.open_web_interface)
        self.open_web_btn.setEnabled(False)
        self.open_web_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)

        self.backup_btn = QPushButton("💾 Backup Data")
        self.backup_btn.clicked.connect(self.show_backup_dialog)
        self.backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)

        self.restore_btn = QPushButton("🔄 Restore Data")
        self.restore_btn.clicked.connect(self.show_restore_dialog)
        self.restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
        """)

        self.logs_btn = QPushButton("📋 View Logs")
        self.logs_btn.clicked.connect(self.toggle_logs)
        self.logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)

        button_layout.addWidget(self.open_web_btn)
        button_layout.addWidget(self.backup_btn)
        button_layout.addWidget(self.restore_btn)
        button_layout.addWidget(self.logs_btn)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # Log console (hidden by default)
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(200)
        self.log_console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        self.log_console.hide()
        main_layout.addWidget(self.log_console)

        central_widget.setLayout(main_layout)

        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
        """)

    def setup_system_tray(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)

        # Create icon (you can replace with actual icon file)
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("#667eea"))
        self.tray_icon.setIcon(QIcon(pixmap))

        # Create tray menu
        tray_menu = QMenu()

        show_action = tray_menu.addAction("Show Window")
        show_action.triggered.connect(self.show)

        web_action = tray_menu.addAction("Open Web Interface")
        web_action.triggered.connect(self.open_web_interface)

        tray_menu.addSeparator()

        backup_action = tray_menu.addAction("💾 Backup Data")
        backup_action.triggered.connect(self.show_backup_dialog)

        restore_action = tray_menu.addAction("🔄 Restore Data")
        restore_action.triggered.connect(self.show_restore_dialog)

        tray_menu.addSeparator()

        settings_action = tray_menu.addAction("⚙️ Settings")
        settings_action.triggered.connect(self.show_settings)

        tray_menu.addSeparator()

        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.tray_icon_activated)

    def setup_menu_bar(self):
        """Setup application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("📁 File")

        settings_action = file_menu.addAction("⚙️ Settings")
        settings_action.triggered.connect(self.show_settings)

        file_menu.addSeparator()

        quit_action = file_menu.addAction("❌ Quit")
        quit_action.triggered.connect(self.quit_application)

        # Tools menu
        tools_menu = menubar.addMenu("🛠️ Tools")

        backup_action = tools_menu.addAction("💾 Backup Data")
        backup_action.triggered.connect(self.show_backup_dialog)

        restore_action = tools_menu.addAction("🔄 Restore Data")
        restore_action.triggered.connect(self.show_restore_dialog)

        tools_menu.addSeparator()

        bulk_upload_action = tools_menu.addAction("📁 Bulk Upload")
        bulk_upload_action.triggered.connect(self.upload_widget.bulk_upload_folder)

        # Help menu
        help_menu = menubar.addMenu("❓ Help")

        docs_action = help_menu.addAction("📚 Documentation")
        docs_action.triggered.connect(lambda: webbrowser.open("http://localhost:8001/docs"))

        help_menu.addSeparator()

        about_action = help_menu.addAction("ℹ️ About")
        about_action.triggered.connect(self.show_about)

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show()
            self.activateWindow()

    def start_services(self):
        """Start Docker services"""
        self.service_manager = ServiceManager(self.project_root)
        self.service_manager.status_update.connect(self.update_service_status)
        self.service_manager.log_message.connect(self.add_log_message)
        self.service_manager.all_services_ready.connect(self.on_services_ready)
        self.service_manager.start()

    def update_service_status(self, service_name: str, status: str):
        """Update service status label"""
        if service_name in self.status_labels:
            label = self.status_labels[service_name]

            if status == "healthy":
                label.setText(label.text().split(":")[0] + ": ✅ Running")
                label.setStyleSheet("padding: 5px; color: #28a745; font-size: 12px;")
            elif status == "starting":
                label.setText(label.text().split(":")[0] + ": ⏳ Starting...")
                label.setStyleSheet("padding: 5px; color: #ffc107; font-size: 12px;")
            else:
                label.setText(label.text().split(":")[0] + ": ❌ Error")
                label.setStyleSheet("padding: 5px; color: #dc3545; font-size: 12px;")

    def add_log_message(self, message: str):
        """Add message to log console"""
        self.log_console.append(message)
        # Auto-scroll to bottom
        self.log_console.verticalScrollBar().setValue(
            self.log_console.verticalScrollBar().maximum()
        )

    def on_services_ready(self):
        """Called when all services are ready"""
        self.services_ready = True
        self.open_web_btn.setEnabled(True)
        self.tray_icon.showMessage(
            "In My Head",
            "All services are ready! Click to open the application.",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def open_web_interface(self):
        """Open web interface in browser"""
        webbrowser.open("http://localhost:8001/docs")

    def toggle_logs(self):
        """Toggle log console visibility"""
        if self.log_console.isVisible():
            self.log_console.hide()
            self.logs_btn.setText("📋 View Logs")
        else:
            self.log_console.show()
            self.logs_btn.setText("📋 Hide Logs")

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec()

    def on_settings_changed(self, new_settings: Dict):
        """Handle settings change"""
        self.settings = new_settings
        QMessageBox.information(
            self,
            "Settings Updated",
            "Settings have been updated successfully!\n\n"
            "Some changes may require restarting the application."
        )

    def show_backup_dialog(self):
        """Show backup confirmation and execute backup"""
        reply = QMessageBox.question(
            self,
            "Backup Data",
            "🔒 Create a backup of all your data?\n\n"
            "This will backup:\n"
            "  • All uploaded documents\n"
            "  • Database and vector embeddings\n"
            "  • Configuration files\n\n"
            f"Backup location: {self.settings['backup_path']}\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.execute_backup()

    def execute_backup(self):
        """Execute backup operation"""
        # Create progress dialog
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("💾 Backing Up Data")
        progress_dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        progress_label = QLabel("Backup in progress...")
        progress_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(progress_label)

        progress_log = QTextEdit()
        progress_log.setReadOnly(True)
        progress_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        layout.addWidget(progress_log)

        progress_dialog.setLayout(layout)
        progress_dialog.show()
        QApplication.processEvents()

        # Create worker thread
        self.backup_worker = BackupRestoreWorker("backup")
        self.backup_worker.progress.connect(progress_log.append)
        self.backup_worker.finished.connect(
            lambda success, msg: self.on_backup_finished(success, msg, progress_dialog)
        )
        self.backup_worker.start()

    def on_backup_finished(self, success: bool, message: str, dialog: QDialog):
        """Handle backup completion"""
        dialog.close()

        if success:
            QMessageBox.information(
                self,
                "Backup Complete",
                f"✅ {message}\n\n"
                f"Backup saved to: {self.settings['backup_path']}\n\n"
                "💡 Tip: Store backups on an external drive for safety!"
            )
        else:
            QMessageBox.critical(
                self,
                "Backup Failed",
                f"❌ {message}\n\n"
                "Please check the logs for more details."
            )

    def show_restore_dialog(self):
        """Show restore dialog with backup selection"""
        # Find available backups
        backup_path = Path(self.settings['backup_path'])
        backups = []

        if backup_path.exists():
            # Find backup folders
            for folder in backup_path.glob("backup_*"):
                if folder.is_dir():
                    manifest_path = folder / "manifest.json"
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r') as f:
                                manifest = json.load(f)
                                backups.append({
                                    "path": str(folder),
                                    "name": folder.name,
                                    "date": manifest.get("date", "Unknown"),
                                    "type": "folder"
                                })
                        except:
                            pass

            # Find backup ZIPs
            for zip_file in backup_path.glob("backup_*.zip"):
                backups.append({
                    "path": str(zip_file),
                    "name": zip_file.name,
                    "date": datetime.fromtimestamp(zip_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "zip"
                })

        if not backups:
            QMessageBox.warning(
                self,
                "No Backups Found",
                f"No backups found in: {backup_path}\n\n"
                "Create a backup first using the 'Backup Data' button."
            )
            return

        # Show selection dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("🔄 Restore Data")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        info_label = QLabel("⚠️ WARNING: This will replace ALL current data!\n\n"
                           "Select a backup to restore:")
        info_label.setStyleSheet("background-color: #fff3cd; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)

        backup_list = QListWidget()
        for backup in backups:
            icon = "📦" if backup["type"] == "zip" else "📁"
            item = QListWidgetItem(f"{icon} {backup['name']}\n    Date: {backup['date']}")
            item.setData(Qt.ItemDataRole.UserRole, backup["path"])
            backup_list.addItem(item)
        layout.addWidget(backup_list)

        button_layout = QHBoxLayout()
        restore_btn = QPushButton("🔄 Restore Selected")
        restore_btn.clicked.connect(lambda: self.execute_restore(
            backup_list.currentItem().data(Qt.ItemDataRole.UserRole) if backup_list.currentItem() else None,
            dialog
        ))
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(restore_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec()

    def execute_restore(self, backup_path: str, parent_dialog: QDialog):
        """Execute restore operation"""
        if not backup_path:
            QMessageBox.warning(self, "No Selection", "Please select a backup to restore.")
            return

        # Final confirmation
        reply = QMessageBox.warning(
            self,
            "⚠️ Confirm Restore",
            "This will REPLACE ALL current data!\n\n"
            "Are you absolutely sure?\n\n"
            "💡 Tip: Create a backup of current data first.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        parent_dialog.close()

        # Create progress dialog
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("🔄 Restoring Data")
        progress_dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        progress_label = QLabel("Restore in progress...")
        progress_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(progress_label)

        progress_log = QTextEdit()
        progress_log.setReadOnly(True)
        progress_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        layout.addWidget(progress_log)

        progress_dialog.setLayout(layout)
        progress_dialog.show()
        QApplication.processEvents()

        # Create worker thread
        self.restore_worker = BackupRestoreWorker("restore", backup_path)
        self.restore_worker.progress.connect(progress_log.append)
        self.restore_worker.finished.connect(
            lambda success, msg: self.on_restore_finished(success, msg, progress_dialog)
        )
        self.restore_worker.start()

    def on_restore_finished(self, success: bool, message: str, dialog: QDialog):
        """Handle restore completion"""
        dialog.close()

        if success:
            QMessageBox.information(
                self,
                "Restore Complete",
                f"✅ {message}\n\n"
                "Services have been restarted with restored data.\n\n"
                "💡 Tip: Verify your documents in the web interface."
            )
        else:
            QMessageBox.critical(
                self,
                "Restore Failed",
                f"❌ {message}\n\n"
                "Please check the logs for more details."
            )

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About In My Head",
            "🧠 <b>In My Head</b><br><br>"
            "AI-Powered Personal Knowledge Management System<br><br>"
            "<b>Features:</b><br>"
            "• 100% Local-First Architecture<br>"
            "• Multi-Modal Document Processing<br>"
            "• Real-Time Semantic Search<br>"
            "• Automatic Backup & Restore<br>"
            "• Intelligent Resource Management<br><br>"
            "<b>Version:</b> 1.0.0<br>"
            "<b>Status:</b> Active Development<br><br>"
            "\"Your Knowledge, Infinitely Connected,<br>"
            "Eternally Private, Boundlessly Intelligent\""
        )

    def closeEvent(self, event):
        """Handle window close event"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "In My Head",
            "Application minimized to system tray",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def quit_application(self):
        """Quit application and stop services"""
        reply = QMessageBox.question(
            self,
            "Quit Application",
            "Do you want to stop all services and quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.service_manager:
                self.service_manager.shutdown_services()
                self.service_manager.stop()
            QApplication.quit()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("In My Head")
    app.setOrganizationName("In My Head")

    # Set application style
    app.setStyle("Fusion")

    window = InMyHeadApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
