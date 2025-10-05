#!/bin/bash

# Clean Up Development Environment
# Removes containers, volumes, build artifacts, and cache

set -e

echo "==================================="
echo "In My Head - Cleanup"
echo "==================================="

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Stop and remove containers
echo ""
echo "Stopping and removing Docker containers..."
cd infrastructure/docker
docker-compose -f docker-compose.dev.yml down -v
print_status "Containers and volumes removed"
cd ../..

# Remove Docker images
echo ""
read -p "Remove Docker images? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker images | grep "in-my-head" | awk '{print $3}' | xargs -r docker rmi -f
    print_status "Docker images removed"
fi

# Remove node_modules
echo ""
read -p "Remove node_modules? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    find . -name "node_modules" -type d -prune -exec rm -rf '{}' +
    print_status "node_modules removed"
fi

# Remove Python virtual environments
echo ""
read -p "Remove Python virtual environments? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    find . -name "venv" -type d -prune -exec rm -rf '{}' +
    print_status "Python venvs removed"
fi

# Remove coverage reports
echo ""
read -p "Remove coverage reports? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf reports/coverage
    find . -name ".coverage" -type f -delete
    find . -name "htmlcov" -type d -prune -exec rm -rf '{}' +
    find . -name "coverage" -type d -prune -exec rm -rf '{}' +
    print_status "Coverage reports removed"
fi

# Remove build artifacts
echo ""
read -p "Remove build artifacts? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    find . -name "dist" -type d -prune -exec rm -rf '{}' +
    find . -name "build" -type d -prune -exec rm -rf '{}' +
    find . -name "*.egg-info" -type d -prune -exec rm -rf '{}' +
    find . -name "__pycache__" -type d -prune -exec rm -rf '{}' +
    find . -name "*.pyc" -type f -delete
    print_status "Build artifacts removed"
fi

echo ""
echo "==================================="
echo -e "${GREEN}Cleanup complete!${NC}"
echo "==================================="
echo ""
