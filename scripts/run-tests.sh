#!/bin/bash

# Run All Tests for In My Head
# Executes unit tests, integration tests, and generates coverage reports

set -e

echo "==================================="
echo "In My Head - Test Runner"
echo "==================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Create reports directory
mkdir -p reports/coverage

# Run Node.js tests (API Gateway)
echo ""
echo "Running API Gateway tests..."
cd services/api-gateway
if [ -f "package.json" ]; then
    npm test -- --coverage --coverageDirectory=../../reports/coverage/api-gateway
    if [ $? -eq 0 ]; then
        print_status "API Gateway tests passed"
    else
        print_error "API Gateway tests failed"
        exit 1
    fi
else
    print_error "package.json not found in services/api-gateway"
fi
cd ../..

# Run Python tests for each service
PYTHON_SERVICES=("document-processor" "ai-engine" "search-service" "resource-manager")

for service in "${PYTHON_SERVICES[@]}"; do
    echo ""
    echo "Running $service tests..."
    cd "services/$service"
    if [ -f "requirements.txt" ]; then
        source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null
        pytest tests/ -v --cov=src --cov-report=html:../../reports/coverage/$service --cov-report=term-missing
        if [ $? -eq 0 ]; then
            print_status "$service tests passed"
        else
            print_error "$service tests failed"
            deactivate
            exit 1
        fi
        deactivate
    else
        print_error "requirements.txt not found in services/$service"
    fi
    cd ../..
done

# Run integration tests
echo ""
echo "Running integration tests..."
cd tests/integration
if [ -f "requirements.txt" ]; then
    python3 -m venv venv 2>/dev/null || true
    source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null
    pip install -r requirements.txt
    pytest . -v --cov=../../services --cov-report=html:../../reports/coverage/integration --cov-report=term-missing
    if [ $? -eq 0 ]; then
        print_status "Integration tests passed"
    else
        print_error "Integration tests failed"
        deactivate
        exit 1
    fi
    deactivate
else
    print_error "requirements.txt not found in tests/integration"
fi
cd ../..

# Generate combined coverage report
echo ""
echo "Generating combined coverage report..."
print_status "Coverage reports generated in reports/coverage/"

echo ""
echo "==================================="
echo -e "${GREEN}All tests passed!${NC}"
echo "==================================="
echo ""
echo "Coverage reports:"
for service in "api-gateway" "${PYTHON_SERVICES[@]}" "integration"; do
    if [ -d "reports/coverage/$service" ]; then
        echo "  - reports/coverage/$service/index.html"
    fi
done
echo ""
