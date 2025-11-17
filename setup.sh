#!/bin/bash

# CreatorSync Setup Script
# This script sets up the entire CreatorSync development environment

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   CreatorSync Setup                            ║"
echo "║          Financial OS for Content Creators                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠ Python 3 not found. Some features may not work.${NC}"
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠ Node.js not found. Frontend will not work.${NC}"
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js ${NODE_VERSION} found${NC}"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Step 1: Setting up environment files"
echo "════════════════════════════════════════════════════════════════"

# Create .env files from examples
for dir in backend/attribution-engine backend/tax-optimizer backend/brand-crm backend/invoice-factoring frontend/web-app; do
    if [ -f "$dir/.env.example" ]; then
        if [ ! -f "$dir/.env" ]; then
            echo "Creating $dir/.env..."
            cp "$dir/.env.example" "$dir/.env"
            echo -e "${GREEN}✓ Created $dir/.env${NC}"
        else
            echo -e "${YELLOW}⚠ $dir/.env already exists, skipping${NC}"
        fi
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Step 2: Starting infrastructure services"
echo "════════════════════════════════════════════════════════════════"

echo "Starting PostgreSQL, Redis, Kafka, and Elasticsearch..."
docker-compose up -d postgres redis zookeeper kafka elasticsearch

echo "Waiting for services to be healthy..."
sleep 10

echo -e "${GREEN}✓ Infrastructure services started${NC}"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Step 3: Building application services"
echo "════════════════════════════════════════════════════════════════"

echo "Building all services..."
docker-compose build

echo -e "${GREEN}✓ Services built successfully${NC}"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Step 4: Starting application services"
echo "════════════════════════════════════════════════════════════════"

docker-compose up -d

echo "Waiting for services to start..."
sleep 5

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "                    Setup Complete! 🎉"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Services are now running at:"
echo ""
echo "  📊 Attribution Engine:   http://localhost:8001/docs"
echo "  💰 Tax Optimizer:        http://localhost:8002/docs"
echo "  🤝 Brand CRM:            http://localhost:8003/graphql"
echo "  ⚡ Invoice Factoring:    http://localhost:8004/docs"
echo "  🌐 Frontend:             http://localhost:3000"
echo ""
echo "Database:"
echo "  🗄️  PostgreSQL:           localhost:5432"
echo "  🔴 Redis:                localhost:6379"
echo "  📨 Kafka:                localhost:9093"
echo "  🔍 Elasticsearch:        localhost:9200"
echo ""
echo "Useful commands:"
echo "  • View logs:        docker-compose logs -f [service]"
echo "  • Stop all:         docker-compose down"
echo "  • Restart service:  docker-compose restart [service]"
echo "  • View status:      docker-compose ps"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Configure API keys in backend/*/.env files"
echo "  2. Run database migrations (if any)"
echo "  3. Visit http://localhost:3000 to see the app"
echo ""
echo "For more information, see README.md"
echo ""
