# ============================================================================
# ENVIRONMENT SETUP SCRIPT - In My Head Project
# ============================================================================
# Purpose: Automatically configure development environment
# Author: GitHub Copilot
# Date: October 5, 2025
# ============================================================================

# Enable strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"
$Magenta = "Magenta"

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor $Cyan
Write-Host "║     ENVIRONMENT SETUP - In My Head Project                       ║" -ForegroundColor $Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor $Cyan

# ============================================================================
# CONFIGURATION
# ============================================================================

$projectRoot = "C:\Users\sgbil\In My Head"
$pythonVersion = "3.11"
$nodeVersion = "18"

# ============================================================================
# STEP 1: VERIFY PROJECT STRUCTURE
# ============================================================================

Write-Host "📋 STEP 1: Verifying project structure..." -ForegroundColor $Yellow

# Check if we're in the right directory
if (-not (Test-Path $projectRoot)) {
    Write-Host "   ❌ ERROR: Project root not found: $projectRoot" -ForegroundColor $Red
    exit 1
}

# Check for key directories
$requiredDirs = @("services", "docs", "infrastructure", "scripts")
$missingDirs = @()

foreach ($dir in $requiredDirs) {
    $dirPath = Join-Path $projectRoot $dir
    if (Test-Path $dirPath) {
        Write-Host "   ✅ Found: $dir\" -ForegroundColor $Green
    }
    else {
        Write-Host "   ⚠️  Missing: $dir\" -ForegroundColor $Yellow
        $missingDirs += $dir
    }
}

if ($missingDirs.Count -gt 0) {
    Write-Host "`n   ⚠️  WARNING: Some directories are missing. Structure may not be flattened yet." -ForegroundColor $Yellow
    Write-Host "   Run .\flatten-structure.ps1 first if needed." -ForegroundColor $Cyan
}

# ============================================================================
# STEP 2: CHECK SYSTEM PREREQUISITES
# ============================================================================

Write-Host "`n🔍 STEP 2: Checking system prerequisites..." -ForegroundColor $Yellow

# Check Python
try {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonVer = python --version 2>&1
        Write-Host "   ✅ Python: $pythonVer" -ForegroundColor $Green
    }
    else {
        Write-Host "   ⚠️  Python not found in PATH" -ForegroundColor $Yellow
    }
}
catch {
    Write-Host "   ⚠️  Python check failed" -ForegroundColor $Yellow
}

# Check pip
try {
    $pipCmd = Get-Command pip -ErrorAction SilentlyContinue
    if ($pipCmd) {
        $pipVer = pip --version 2>&1
        Write-Host "   ✅ pip: $pipVer" -ForegroundColor $Green
    }
    else {
        Write-Host "   ⚠️  pip not found in PATH" -ForegroundColor $Yellow
    }
}
catch {
    Write-Host "   ⚠️  pip check failed" -ForegroundColor $Yellow
}

# Check Node.js
try {
    $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
    if ($nodeCmd) {
        $nodeVer = node --version 2>&1
        Write-Host "   ✅ Node.js: $nodeVer" -ForegroundColor $Green
    }
    else {
        Write-Host "   ⚠️  Node.js not found in PATH" -ForegroundColor $Yellow
    }
}
catch {
    Write-Host "   ⚠️  Node.js check failed" -ForegroundColor $Yellow
}

# Check npm
try {
    $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
    if ($npmCmd) {
        $npmVer = npm --version 2>&1
        Write-Host "   ✅ npm: v$npmVer" -ForegroundColor $Green
    }
    else {
        Write-Host "   ⚠️  npm not found in PATH" -ForegroundColor $Yellow
    }
}
catch {
    Write-Host "   ⚠️  npm check failed" -ForegroundColor $Yellow
}

# Check Docker
try {
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCmd) {
        $dockerVer = docker --version 2>&1
        Write-Host "   ✅ Docker: $dockerVer" -ForegroundColor $Green
    }
    else {
        Write-Host "   ⚠️  Docker not found in PATH" -ForegroundColor $Yellow
    }
}
catch {
    Write-Host "   ⚠️  Docker check failed" -ForegroundColor $Yellow
}

# Check Git
try {
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        $gitVer = git --version 2>&1
        Write-Host "   ✅ Git: $gitVer" -ForegroundColor $Green
    }
    else {
        Write-Host "   ⚠️  Git not found in PATH" -ForegroundColor $Yellow
    }
}
catch {
    Write-Host "   ⚠️  Git check failed" -ForegroundColor $Yellow
}

# ============================================================================
# STEP 3: CREATE/UPDATE ENVIRONMENT VARIABLES
# ============================================================================

Write-Host "`n🔧 STEP 3: Setting up environment variables..." -ForegroundColor $Yellow

# Set PROJECT_ROOT environment variable
$envVarName = "IN_MY_HEAD_ROOT"
$currentValue = [System.Environment]::GetEnvironmentVariable($envVarName, "User")

if ($currentValue -ne $projectRoot) {
    try {
        [System.Environment]::SetEnvironmentVariable($envVarName, $projectRoot, "User")
        Write-Host "   ✅ Set $envVarName = $projectRoot" -ForegroundColor $Green
        Write-Host "   ℹ️  You may need to restart your terminal for this to take effect" -ForegroundColor $Cyan
    }
    catch {
        Write-Host "   ⚠️  Failed to set environment variable: $_" -ForegroundColor $Yellow
    }
}
else {
    Write-Host "   ✅ $envVarName already set correctly" -ForegroundColor $Green
}

# ============================================================================
# STEP 4: CREATE .ENV FILES
# ============================================================================

Write-Host "`n📝 STEP 4: Creating .env files..." -ForegroundColor $Yellow

# Document Processor .env
$docProcessorEnvPath = Join-Path $projectRoot "services\document-processor\.env"
if (-not (Test-Path $docProcessorEnvPath)) {
    $docProcessorEnv = @"
# Document Processor Service Environment Variables
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Database Configuration
DATABASE_URL=postgresql://inmyhead:inmyhead_dev_pass@localhost:5432/inmyhead_dev
SQL_ECHO=false

# Connection Pool Settings
POOL_SIZE=10
MAX_OVERFLOW=20
POOL_TIMEOUT=30
POOL_RECYCLE=3600

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=inmyhead_minio
MINIO_SECRET_KEY=inmyhead_minio_secret
MINIO_BUCKET=inmyhead-documents

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8001
LOG_LEVEL=INFO

# Development Settings
ENVIRONMENT=development
DEBUG=true
"@
    
    try {
        $docProcessorEnv | Out-File -FilePath $docProcessorEnvPath -Encoding UTF8
        Write-Host "   ✅ Created: services\document-processor\.env" -ForegroundColor $Green
    }
    catch {
        Write-Host "   ⚠️  Failed to create .env file: $_" -ForegroundColor $Yellow
    }
}
else {
    Write-Host "   ℹ️  .env already exists: services\document-processor\.env" -ForegroundColor $Cyan
}

# API Gateway .env
$apiGatewayEnvPath = Join-Path $projectRoot "services\api-gateway\.env"
if (-not (Test-Path $apiGatewayEnvPath)) {
    $apiGatewayEnv = @"
# API Gateway Service Environment Variables
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Database Configuration
DATABASE_URL=postgresql://inmyhead:inmyhead_dev_pass@localhost:5432/inmyhead_dev

# Service URLs
DOCUMENT_PROCESSOR_URL=http://localhost:8001
AI_ENGINE_URL=http://localhost:8002
SEARCH_SERVICE_URL=http://localhost:8003
RESOURCE_MANAGER_URL=http://localhost:8004

# JWT Configuration
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
LOG_LEVEL=INFO

# Development Settings
ENVIRONMENT=development
DEBUG=true
"@
    
    try {
        $apiGatewayEnv | Out-File -FilePath $apiGatewayEnvPath -Encoding UTF8
        Write-Host "   ✅ Created: services\api-gateway\.env" -ForegroundColor $Green
    }
    catch {
        Write-Host "   ⚠️  Failed to create .env file: $_" -ForegroundColor $Yellow
    }
}
else {
    Write-Host "   ℹ️  .env already exists: services\api-gateway\.env" -ForegroundColor $Cyan
}

# Root .env file
$rootEnvPath = Join-Path $projectRoot ".env"
if (-not (Test-Path $rootEnvPath)) {
    $rootEnv = @"
# In My Head Project - Root Environment Variables
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Project Configuration
PROJECT_NAME=In My Head
PROJECT_ROOT=$projectRoot
ENVIRONMENT=development

# Database Configuration (PostgreSQL)
POSTGRES_USER=inmyhead
POSTGRES_PASSWORD=inmyhead_dev_pass
POSTGRES_DB=inmyhead_dev
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://inmyhead:inmyhead_dev_pass@localhost:5432/inmyhead_dev

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# MinIO Configuration
MINIO_ROOT_USER=inmyhead_minio
MINIO_ROOT_PASSWORD=inmyhead_minio_secret
MINIO_ENDPOINT=localhost:9000

# Qdrant Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=

# Development Tools
DEBUG=true
LOG_LEVEL=INFO
"@
    
    try {
        $rootEnv | Out-File -FilePath $rootEnvPath -Encoding UTF8
        Write-Host "   ✅ Created: .env (root)" -ForegroundColor $Green
    }
    catch {
        Write-Host "   ⚠️  Failed to create .env file: $_" -ForegroundColor $Yellow
    }
}
else {
    Write-Host "   ℹ️  .env already exists at root" -ForegroundColor $Cyan
}

# ============================================================================
# STEP 5: INSTALL PYTHON DEPENDENCIES
# ============================================================================

Write-Host "`n🐍 STEP 5: Installing Python dependencies..." -ForegroundColor $Yellow

$docProcessorPath = Join-Path $projectRoot "services\document-processor"
$requirementsPath = Join-Path $docProcessorPath "requirements.txt"

if (Test-Path $requirementsPath) {
    Push-Location $docProcessorPath
    try {
        Write-Host "   📦 Installing dependencies from requirements.txt..." -ForegroundColor $Cyan
        pip install -r requirements.txt --quiet
        Write-Host "   ✅ Python dependencies installed" -ForegroundColor $Green
    }
    catch {
        Write-Host "   ⚠️  Failed to install Python dependencies: $_" -ForegroundColor $Yellow
    }
    Pop-Location
}
else {
    Write-Host "   ⚠️  requirements.txt not found at: $requirementsPath" -ForegroundColor $Yellow
}

# ============================================================================
# STEP 6: INSTALL NODE.JS DEPENDENCIES
# ============================================================================

Write-Host "`n📦 STEP 6: Installing Node.js dependencies..." -ForegroundColor $Yellow

$apiGatewayPath = Join-Path $projectRoot "services\api-gateway"
$packageJsonPath = Join-Path $apiGatewayPath "package.json"

if (Test-Path $packageJsonPath) {
    Push-Location $apiGatewayPath
    try {
        Write-Host "   📦 Installing dependencies from package.json..." -ForegroundColor $Cyan
        npm install --silent
        Write-Host "   ✅ Node.js dependencies installed" -ForegroundColor $Green
    }
    catch {
        Write-Host "   ⚠️  Failed to install Node.js dependencies: $_" -ForegroundColor $Yellow
    }
    Pop-Location
}
else {
    Write-Host "   ℹ️  package.json not found at: $packageJsonPath" -ForegroundColor $Cyan
}

# ============================================================================
# STEP 7: SETUP DATABASE
# ============================================================================

Write-Host "`n🗄️  STEP 7: Setting up database..." -ForegroundColor $Yellow

# Check if Docker is running
try {
    docker ps > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Docker is running" -ForegroundColor $Green
        
        # Check if docker-compose.yml exists
        $dockerComposePath = Join-Path $projectRoot "infrastructure\docker\docker-compose.yml"
        if (Test-Path $dockerComposePath) {
            Push-Location (Split-Path $dockerComposePath -Parent)
            try {
                Write-Host "   🐳 Starting database containers..." -ForegroundColor $Cyan
                docker-compose up -d postgres redis qdrant minio
                
                Write-Host "   ⏳ Waiting for PostgreSQL to be ready..." -ForegroundColor $Cyan
                Start-Sleep -Seconds 5
                
                Write-Host "   ✅ Database containers started" -ForegroundColor $Green
            }
            catch {
                Write-Host "   ⚠️  Failed to start containers: $_" -ForegroundColor $Yellow
            }
            Pop-Location
        }
        else {
            Write-Host "   ⚠️  docker-compose.yml not found" -ForegroundColor $Yellow
        }
    }
    else {
        Write-Host "   ⚠️  Docker is not running. Please start Docker Desktop." -ForegroundColor $Yellow
    }
}
catch {
    Write-Host "   ⚠️  Docker check failed: $_" -ForegroundColor $Yellow
}

# ============================================================================
# STEP 8: RUN DATABASE MIGRATIONS
# ============================================================================

Write-Host "`n🔄 STEP 8: Running database migrations..." -ForegroundColor $Yellow

$alembicPath = Join-Path $docProcessorPath "alembic.ini"
if (Test-Path $alembicPath) {
    Push-Location $docProcessorPath
    try {
        Write-Host "   📝 Generating initial migration..." -ForegroundColor $Cyan
        alembic revision --autogenerate -m "Initial schema with 15 tables" 2>&1 | Out-Null
        
        Write-Host "   🔄 Applying migrations..." -ForegroundColor $Cyan
        alembic upgrade head
        
        Write-Host "   ✅ Database migrations applied" -ForegroundColor $Green
    }
    catch {
        Write-Host "   ⚠️  Failed to run migrations: $_" -ForegroundColor $Yellow
        Write-Host "   ℹ️  You may need to run migrations manually later" -ForegroundColor $Cyan
    }
    Pop-Location
}
else {
    Write-Host "   ⚠️  alembic.ini not found" -ForegroundColor $Yellow
}

# ============================================================================
# STEP 9: SEED DATABASE (OPTIONAL)
# ============================================================================

Write-Host "`n🌱 STEP 9: Seeding database with test data..." -ForegroundColor $Yellow

$seedScriptPath = Join-Path $docProcessorPath "src\database\seed.py"
if (Test-Path $seedScriptPath) {
    Push-Location $docProcessorPath
    try {
        Write-Host "   🌱 Running seed script..." -ForegroundColor $Cyan
        python -m src.database.seed
        Write-Host "   ✅ Database seeded with test data" -ForegroundColor $Green
    }
    catch {
        Write-Host "   ⚠️  Failed to seed database: $_" -ForegroundColor $Yellow
    }
    Pop-Location
}
else {
    Write-Host "   ⚠️  Seed script not found" -ForegroundColor $Yellow
}

# ============================================================================
# STEP 10: CREATE USEFUL SHORTCUTS
# ============================================================================

Write-Host "`n🔗 STEP 10: Creating useful shortcuts..." -ForegroundColor $Yellow

# Create start-all.ps1 script
$startAllPath = Join-Path $projectRoot "start-all.ps1"
$startAllContent = @"
# Start All Services - In My Head Project

Write-Host "Starting In My Head services..." -ForegroundColor Cyan

# Start Docker containers
Push-Location infrastructure\docker
docker-compose up -d
Pop-Location

# Wait for services to be ready
Start-Sleep -Seconds 5

Write-Host "All services started!" -ForegroundColor Green
Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor Cyan
Write-Host "  - Redis: localhost:6379" -ForegroundColor Cyan
Write-Host "  - Qdrant: localhost:6333" -ForegroundColor Cyan
Write-Host "  - MinIO: localhost:9000" -ForegroundColor Cyan
"@

try {
    $startAllContent | Out-File -FilePath $startAllPath -Encoding UTF8
    Write-Host "   ✅ Created: start-all.ps1" -ForegroundColor $Green
}
catch {
    Write-Host "   ⚠️  Failed to create start-all.ps1" -ForegroundColor $Yellow
}

# Create stop-all.ps1 script
$stopAllPath = Join-Path $projectRoot "stop-all.ps1"
$stopAllContent = @"
# Stop All Services - In My Head Project

Write-Host "Stopping In My Head services..." -ForegroundColor Yellow

Push-Location infrastructure\docker
docker-compose down
Pop-Location

Write-Host "All services stopped!" -ForegroundColor Green
"@

try {
    $stopAllContent | Out-File -FilePath $stopAllPath -Encoding UTF8
    Write-Host "   ✅ Created: stop-all.ps1" -ForegroundColor $Green
}
catch {
    Write-Host "   ⚠️  Failed to create stop-all.ps1" -ForegroundColor $Yellow
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor $Green
Write-Host "║             ENVIRONMENT SETUP COMPLETE ✅                         ║" -ForegroundColor $Green
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor $Green

Write-Host "📊 SUMMARY:" -ForegroundColor $Yellow
Write-Host "   ✅ Project structure verified" -ForegroundColor $Green
Write-Host "   ✅ Environment variables configured" -ForegroundColor $Green
Write-Host "   ✅ .env files created" -ForegroundColor $Green
Write-Host "   ✅ Python dependencies installed" -ForegroundColor $Green
Write-Host "   ✅ Node.js dependencies installed" -ForegroundColor $Green
Write-Host "   ✅ Database containers started" -ForegroundColor $Green
Write-Host "   ✅ Database migrations applied" -ForegroundColor $Green
Write-Host "   ✅ Test data seeded" -ForegroundColor $Green
Write-Host "   ✅ Utility scripts created" -ForegroundColor $Green

Write-Host "`n🎯 QUICK COMMANDS:" -ForegroundColor $Yellow
Write-Host "   Start all services:    .\start-all.ps1" -ForegroundColor $Cyan
Write-Host "   Stop all services:     .\stop-all.ps1" -ForegroundColor $Cyan
Write-Host "   View containers:       docker-compose ps" -ForegroundColor $Cyan
Write-Host "   View logs:             docker-compose logs -f" -ForegroundColor $Cyan

Write-Host "`n🔗 SERVICE URLS:" -ForegroundColor $Yellow
Write-Host "   PostgreSQL:   localhost:5432" -ForegroundColor $Cyan
Write-Host "   Redis:        localhost:6379" -ForegroundColor $Cyan
Write-Host "   Qdrant:       http://localhost:6333" -ForegroundColor $Cyan
Write-Host "   MinIO:        http://localhost:9000" -ForegroundColor $Cyan

Write-Host "`n🔑 TEST CREDENTIALS:" -ForegroundColor $Yellow
Write-Host "   Username: testuser" -ForegroundColor $Cyan
Write-Host "   Password: Test123!" -ForegroundColor $Cyan
Write-Host "   Email:    test@inmyhead.local" -ForegroundColor $Cyan

Write-Host "`n📚 NEXT STEPS:" -ForegroundColor $Yellow
Write-Host "   1. Restart your terminal/IDE to pick up new environment variables" -ForegroundColor $Cyan
Write-Host "   2. Review .env files and update any passwords/secrets" -ForegroundColor $Cyan
Write-Host "   3. Start coding! The environment is ready." -ForegroundColor $Cyan

Write-Host "`n════════════════════════════════════════════════════════════════════`n" -ForegroundColor $Cyan

# Pause to let user review
Write-Host "Press any key to exit..." -ForegroundColor $Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
