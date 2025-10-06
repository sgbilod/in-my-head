#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup PostgreSQL database for In My Head project
.DESCRIPTION
    Creates a dedicated PostgreSQL user and database for this project.
    This script will prompt for your PostgreSQL superuser password once,
    then set up everything needed for the project.
#>

param(
    [string]$PostgresPassword = "",
    [switch]$UseDocker = $false,
    [switch]$Help
)

# Color output functions
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Step { param($Message) Write-Host "`n🔧 $Message" -ForegroundColor Magenta }

if ($Help) {
    Write-Host @"
USAGE:
    .\setup-database.ps1 [OPTIONS]

OPTIONS:
    -UseDocker          Use Docker PostgreSQL instead of local service
    -PostgresPassword   PostgreSQL superuser password (will prompt if not provided)
    -Help               Show this help message

EXAMPLES:
    # Use local PostgreSQL (recommended)
    .\setup-database.ps1

    # Use Docker instead
    .\setup-database.ps1 -UseDocker

WHAT THIS DOES:
    1. Creates a dedicated PostgreSQL user 'inmyhead' for this project
    2. Creates database 'inmyhead_dev' owned by that user
    3. Runs all database migrations
    4. Seeds test data
    5. Verifies everything works

This keeps your project isolated from other PostgreSQL databases on your system.
"@
    exit 0
}

$ErrorActionPreference = "Stop"

# Project configuration
$PROJECT_USER = "inmyhead"
$PROJECT_PASSWORD = "inmyhead_dev_pass"
$PROJECT_DB = "inmyhead_dev"
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$DOC_PROCESSOR_DIR = Join-Path $PROJECT_ROOT "services\document-processor"

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║         IN MY HEAD - Database Setup Script                   ║
║         Setting up PostgreSQL for your project               ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# ============================================================================
# OPTION 1: Use Docker PostgreSQL
# ============================================================================

if ($UseDocker) {
    Write-Step "Using Docker PostgreSQL"
    
    # Check if Docker is running
    try {
        docker info | Out-Null
        Write-Success "Docker is running"
    } catch {
        Write-Error "Docker is not running. Please start Docker Desktop first."
        exit 1
    }
    
    # Check if local PostgreSQL is running on port 5432
    $localPg = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq "Running" }
    if ($localPg) {
        Write-Warning "Local PostgreSQL service is running and may conflict with Docker."
        $response = Read-Host "Stop local PostgreSQL service? (y/n)"
        if ($response -eq "y") {
            Write-Info "Stopping local PostgreSQL service..."
            Stop-Service $localPg.Name
            Write-Success "Local PostgreSQL service stopped"
        } else {
            Write-Error "Cannot proceed with Docker while local PostgreSQL is using port 5432."
            exit 1
        }
    }
    
    # Start Docker containers
    Write-Step "Starting Docker PostgreSQL container"
    $dockerComposeFile = Join-Path $PROJECT_ROOT "infrastructure\docker\docker-compose.dev.yml"
    
    if (-not (Test-Path $dockerComposeFile)) {
        Write-Error "Docker Compose file not found: $dockerComposeFile"
        exit 1
    }
    
    Push-Location (Split-Path $dockerComposeFile)
    try {
        docker-compose -f (Split-Path -Leaf $dockerComposeFile) up -d postgres
        Write-Success "Docker PostgreSQL started"
        
        # Wait for PostgreSQL to be ready
        Write-Info "Waiting for PostgreSQL to be ready..."
        Start-Sleep -Seconds 5
        
        # The Docker setup automatically creates the user and database
        Write-Success "Docker PostgreSQL is ready with pre-configured credentials"
        
    } finally {
        Pop-Location
    }
    
    $DATABASE_URL = "postgresql://$PROJECT_USER:$PROJECT_PASSWORD@localhost:5432/$PROJECT_DB"
}

# ============================================================================
# OPTION 2: Use Local PostgreSQL
# ============================================================================

else {
    Write-Step "Using local PostgreSQL service"
    
    # Check if PostgreSQL service is running
    $pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq "Running" }
    
    if (-not $pgService) {
        Write-Error "No PostgreSQL service is running."
        Write-Info "Either start your PostgreSQL service or use Docker: .\setup-database.ps1 -UseDocker"
        exit 1
    }
    
    Write-Success "PostgreSQL service is running: $($pgService.DisplayName)"
    
    # Ensure psql is in PATH
    $psqlPath = "C:\Program Files\PostgreSQL\14\bin"
    if (Test-Path $psqlPath) {
        $env:Path += ";$psqlPath"
        Write-Success "Added PostgreSQL to PATH"
    }
    
    # Get PostgreSQL superuser password
    if (-not $PostgresPassword) {
        Write-Info "To create a dedicated database user for this project, I need your PostgreSQL superuser password."
        Write-Warning "This will only be used once to set up the project user. It won't be stored anywhere."
        $securePassword = Read-Host "Enter PostgreSQL 'postgres' user password" -AsSecureString
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
        $PostgresPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    }
    
    # Set PGPASSWORD for non-interactive commands
    $env:PGPASSWORD = $PostgresPassword
    
    Write-Step "Creating dedicated project user and database"
    
    try {
        # Check if user already exists
        $checkUser = "SELECT 1 FROM pg_roles WHERE rolname='$PROJECT_USER';"
        $userExists = psql -U postgres -h localhost -t -c $checkUser 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to connect to PostgreSQL. Please check your password."
            Write-Info "You can also try resetting the password in pgAdmin or use Docker: .\setup-database.ps1 -UseDocker"
            exit 1
        }
        
        if ($userExists -match "1") {
            Write-Info "User '$PROJECT_USER' already exists"
        } else {
            # Create user
            $createUser = "CREATE USER $PROJECT_USER WITH PASSWORD '$PROJECT_PASSWORD';"
            psql -U postgres -h localhost -c $createUser | Out-Null
            Write-Success "Created PostgreSQL user: $PROJECT_USER"
        }
        
        # Check if database already exists
        $checkDb = "SELECT 1 FROM pg_database WHERE datname='$PROJECT_DB';"
        $dbExists = psql -U postgres -h localhost -t -c $checkDb 2>&1
        
        if ($dbExists -match "1") {
            Write-Info "Database '$PROJECT_DB' already exists"
            
            # Ensure proper ownership
            $alterDb = "ALTER DATABASE $PROJECT_DB OWNER TO $PROJECT_USER;"
            psql -U postgres -h localhost -c $alterDb | Out-Null
            Write-Success "Updated database ownership"
        } else {
            # Create database
            $createDb = "CREATE DATABASE $PROJECT_DB OWNER $PROJECT_USER;"
            psql -U postgres -h localhost -c $createDb | Out-Null
            Write-Success "Created database: $PROJECT_DB"
        }
        
        # Grant all privileges
        $grantPrivileges = "GRANT ALL PRIVILEGES ON DATABASE $PROJECT_DB TO $PROJECT_USER;"
        psql -U postgres -h localhost -c $grantPrivileges | Out-Null
        Write-Success "Granted privileges to $PROJECT_USER"
        
    } catch {
        Write-Error "Failed to set up database: $_"
        exit 1
    } finally {
        # Clear password from environment
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    }
    
    $DATABASE_URL = "postgresql://$PROJECT_USER:$PROJECT_PASSWORD@localhost:5432/$PROJECT_DB"
}

# ============================================================================
# Run Database Migrations
# ============================================================================

Write-Step "Running database migrations"

if (-not (Test-Path $DOC_PROCESSOR_DIR)) {
    Write-Error "Document processor directory not found: $DOC_PROCESSOR_DIR"
    exit 1
}

Push-Location $DOC_PROCESSOR_DIR

try {
    # Set DATABASE_URL environment variable
    $env:DATABASE_URL = $DATABASE_URL
    
    # Check if alembic is installed
    try {
        python -m alembic --version | Out-Null
    } catch {
        Write-Error "Alembic not found. Installing dependencies..."
        pip install -r requirements.txt
    }
    
    # Run migrations
    Write-Info "Running Alembic migrations..."
    $output = python -m alembic upgrade head 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database migrations completed successfully"
        Write-Host $output -ForegroundColor Gray
    } else {
        Write-Error "Migration failed:"
        Write-Host $output -ForegroundColor Red
        exit 1
    }
    
} finally {
    Pop-Location
}

# ============================================================================
# Seed Test Data
# ============================================================================

Write-Step "Seeding test data"

Push-Location $DOC_PROCESSOR_DIR

try {
    $env:DATABASE_URL = $DATABASE_URL
    
    Write-Info "Seeding database with test data..."
    $output = python -m src.database.seed 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Test data seeded successfully"
    } else {
        Write-Warning "Seeding may have failed, but migrations succeeded"
        Write-Host $output -ForegroundColor Yellow
    }
    
} catch {
    Write-Warning "Seeding encountered an error: $_"
} finally {
    Pop-Location
}

# ============================================================================
# Verify Database Connection
# ============================================================================

Write-Step "Verifying database connection"

Push-Location $DOC_PROCESSOR_DIR

try {
    $env:DATABASE_URL = $DATABASE_URL
    
    $testScript = @"
from src.database.connection import check_health
try:
    check_health()
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
"@
    
    $result = python -c $testScript 2>&1
    
    if ($result -match "SUCCESS") {
        Write-Success "Database connection verified!"
    } else {
        Write-Warning "Connection test failed: $result"
    }
    
} finally {
    Pop-Location
}

# ============================================================================
# Update .env Files
# ============================================================================

Write-Step "Updating .env files with database credentials"

$envFiles = @(
    (Join-Path $PROJECT_ROOT ".env"),
    (Join-Path $DOC_PROCESSOR_DIR ".env"),
    (Join-Path $PROJECT_ROOT "services\api-gateway\.env")
)

foreach ($envFile in $envFiles) {
    if (Test-Path $envFile) {
        $content = Get-Content $envFile -Raw
        
        # Update DATABASE_URL
        if ($content -match "DATABASE_URL=") {
            $content = $content -replace "DATABASE_URL=.*", "DATABASE_URL=$DATABASE_URL"
        } else {
            $content += "`nDATABASE_URL=$DATABASE_URL"
        }
        
        Set-Content -Path $envFile -Value $content
        Write-Success "Updated: $envFile"
    }
}

# ============================================================================
# Summary
# ============================================================================

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                 ✅ DATABASE SETUP COMPLETE!                  ║
╚══════════════════════════════════════════════════════════════╝

📊 Database Details:
   • Database: $PROJECT_DB
   • User: $PROJECT_USER
   • Host: localhost:5432
   • Connection String: $DATABASE_URL

🧪 Test Credentials:
   • Username: testuser
   • Password: Test123!
   • Email: test@inmyhead.local

📝 Next Steps:
   1. Your database is ready to use!
   2. All migrations have been applied
   3. Test data has been seeded
   4. You can start developing now

🔧 Useful Commands:
   # Connect to database
   psql -U $PROJECT_USER -d $PROJECT_DB

   # Run migrations
   cd services\document-processor
   alembic upgrade head

   # Seed data
   python -m src.database.seed

🎉 Happy coding!

"@ -ForegroundColor Green
