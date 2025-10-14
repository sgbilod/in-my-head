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
from typing import Optional, List
import json
import requests

# GUI imports
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QTextEdit, QProgressBar, QSystemTrayIcon,
        QMenu, QFileDialog, QListWidget, QListWidgetItem, QMessageBox,
        QFrame, QSplitter
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
        QFrame, QSplitter
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


class InMyHeadApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.project_root = Path(__file__).parent
        self.service_manager = None
        self.services_ready = False

        self.init_ui()
        self.setup_system_tray()
        self.start_services()

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

        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.tray_icon_activated)

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
