@echo off
REM In My Head - One-Click Launcher
REM ================================
REM This script launches the In My Head desktop application
REM Prerequisites: Docker Desktop must be running

title In My Head - Starting...

echo.
echo ========================================
echo    IN MY HEAD - Knowledge Management
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from python.org
    pause
    exit /b 1
)

REM Check if Docker is running
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

echo [OK] Python detected
echo [OK] Docker is running
echo.

REM Install dependencies if needed
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/updating dependencies...
python -m pip install --upgrade pip --quiet
pip install PyQt6 requests --quiet

echo.
echo Starting In My Head...
echo.

REM Launch the application
python InMyHead.py

REM If the application exits
deactivate
pause
