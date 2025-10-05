#!/bin/bash

# Setup Development Environment for In My Head
# This script checks prerequisites, installs dependencies, and initializes databases

set -e

echo "==================================="
echo "In My Head - Development Setup"
echo "==================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Print status message
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Check prerequisites
echo ""
echo "Checking prerequisites..."

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi
print_status "Node.js $(node --version) found"

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.11+ from https://python.org/"
    exit 1
fi
print_status "Python $(python3 --version) found"

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker from https://docker.com/"
    exit 1
fi
print_status "Docker $(docker --version | cut -d' ' -f3 | sed 's/,//') found"

if ! command_exists docker-compose; then
    if ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi
    print_status "Docker Compose (v2 via docker compose) found"
else
    print_status "Docker Compose $(docker-compose --version | cut -d' ' -f3 | sed 's/,//') found"
fi

# Install Node.js dependencies for API Gateway
echo ""
echo "Installing Node.js dependencies for API Gateway..."
cd services/api-gateway
if [ -f "package.json" ]; then
    npm ci
    print_status "API Gateway dependencies installed"
else
    print_warning "package.json not found in services/api-gateway"
fi
cd ../..

# Install Python dependencies for each service
PYTHON_SERVICES=("document-processor" "ai-engine" "search-service" "resource-manager")

for service in "${PYTHON_SERVICES[@]}"; do
    echo ""
    echo "Installing Python dependencies for $service..."
    cd "services/$service"
    if [ -f "requirements.txt" ]; then
        python3 -m venv venv 2>/dev/null || print_warning "venv already exists for $service"
        source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null
        pip install --upgrade pip
        pip install -r requirements.txt
        deactivate
        print_status "$service dependencies installed"
    else
        print_warning "requirements.txt not found in services/$service"
    fi
    cd ../..
done

# Build Docker images
echo ""
echo "Building Docker images..."
cd infrastructure/docker
docker-compose -f docker-compose.dev.yml build
print_status "Docker images built successfully"
cd ../..

# Initialize databases
echo ""
echo "Starting database services..."
cd infrastructure/docker
docker-compose -f docker-compose.dev.yml up -d postgres redis qdrant minio
print_status "Database services started"

# Wait for databases to be ready
echo ""
echo "Waiting for databases to be ready..."
sleep 10

# Check database health
echo ""
echo "Checking database connectivity..."
docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U inmyhead && print_status "PostgreSQL is ready" || print_error "PostgreSQL is not ready"

cd ../..

echo ""
echo "==================================="
echo -e "${GREEN}Development environment setup complete!${NC}"
echo "==================================="
echo ""
echo "Next steps:"
echo "  1. Start all services: cd infrastructure/docker && docker-compose -f docker-compose.dev.yml up"
echo "  2. Access API Gateway at: http://localhost:3000"
echo "  3. Access Grafana at: http://localhost:3001 (admin/admin)"
echo "  4. Run tests: ./scripts/run-tests.sh"
echo ""
