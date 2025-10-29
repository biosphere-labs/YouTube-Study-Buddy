#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}YouTube Study Buddy Web App Setup${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}No .env file found. Creating from .env.webapp.example...${NC}"
    cp .env.webapp.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}⚠ Please edit .env with your API keys and secrets before continuing${NC}"
    echo ""
    read -p "Press Enter after you've updated .env..."
fi

# Validate required environment variables
echo -e "\n${YELLOW}Validating environment variables...${NC}"
source .env

required_vars=(
    "JWT_SECRET_KEY"
    "CLAUDE_API_KEY"
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" == "changeme"* ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo -e "${RED}Error: The following required environment variables are not set or still have default values:${NC}"
    for var in "${missing_vars[@]}"; do
        echo -e "  - ${var}"
    done
    echo -e "\n${YELLOW}Please update your .env file with real values${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment variables validated${NC}"

# Pull Docker images
echo -e "\n${YELLOW}Pulling Docker images...${NC}"
docker-compose -f docker-compose.webapp.yml pull

# Build custom images
echo -e "\n${YELLOW}Building custom images...${NC}"
docker-compose -f docker-compose.webapp.yml build

# Start database and redis first
echo -e "\n${YELLOW}Starting database services...${NC}"
docker-compose -f docker-compose.webapp.yml up -d postgres redis

# Wait for database to be ready
echo -e "${YELLOW}Waiting for database to be ready...${NC}"
for i in {1..30}; do
    if docker-compose -f docker-compose.webapp.yml exec -T postgres pg_isready -U ${POSTGRES_USER:-ytstudy} &> /dev/null; then
        echo -e "${GREEN}✓ Database is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Error: Database failed to start${NC}"
        exit 1
    fi
    sleep 1
done

# Run database migrations
echo -e "\n${YELLOW}Running database migrations...${NC}"
docker-compose -f docker-compose.webapp.yml run --rm backend uv run alembic upgrade head
echo -e "${GREEN}✓ Migrations complete${NC}"

# Start remaining services
echo -e "\n${YELLOW}Starting all services...${NC}"
docker-compose -f docker-compose.webapp.yml up -d

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check service health
services=("backend" "websocket" "frontend")
for service in "${services[@]}"; do
    if docker-compose -f docker-compose.webapp.yml ps | grep -q "$service.*Up"; then
        echo -e "${GREEN}✓ $service is running${NC}"
    else
        echo -e "${RED}✗ $service failed to start${NC}"
    fi
done

# Display URLs
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-5173}
WEBSOCKET_PORT=${WEBSOCKET_PORT:-8001}

echo -e "Services are running:"
echo -e "  ${GREEN}Frontend:${NC}    http://localhost:${FRONTEND_PORT}"
echo -e "  ${GREEN}Backend API:${NC} http://localhost:${BACKEND_PORT}"
echo -e "  ${GREEN}API Docs:${NC}    http://localhost:${BACKEND_PORT}/docs"
echo -e "  ${GREEN}WebSocket:${NC}   ws://localhost:${WEBSOCKET_PORT}"
echo ""
echo -e "To view logs:"
echo -e "  ${YELLOW}docker-compose -f docker-compose.webapp.yml logs -f [service]${NC}"
echo ""
echo -e "To stop services:"
echo -e "  ${YELLOW}docker-compose -f docker-compose.webapp.yml down${NC}"
echo ""
echo -e "To reset everything (WARNING: deletes data):"
echo -e "  ${YELLOW}docker-compose -f docker-compose.webapp.yml down -v${NC}"
echo ""
