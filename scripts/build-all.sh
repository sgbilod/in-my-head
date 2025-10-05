#!/bin/bash

# Build All Docker Images for In My Head
# Builds all service Docker images for development

set -e

echo "==================================="
echo "In My Head - Docker Build"
echo "==================================="

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Build all images using Docker Compose
echo ""
echo "Building all Docker images..."
cd infrastructure/docker

docker-compose -f docker-compose.dev.yml build --parallel

if [ $? -eq 0 ]; then
    print_status "All Docker images built successfully"
else
    print_error "Docker build failed"
    exit 1
fi

cd ../..

# List built images
echo ""
echo "Built images:"
docker images | grep "in-my-head"

echo ""
echo "==================================="
echo -e "${GREEN}Build complete!${NC}"
echo "==================================="
echo ""
echo "Start services with:"
echo "  cd infrastructure/docker && docker-compose -f docker-compose.dev.yml up"
echo ""
