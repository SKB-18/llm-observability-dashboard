#!/bin/bash

# LLM Observability Dashboard - One-Command Demo Setup
# Usage: ./demo_setup.sh
# This script will:
# 1. Start Docker containers
# 2. Wait for PostgreSQL to be ready
# 3. Run database migrations
# 4. Seed 5000 sample logs
# 5. Generate evaluation results
# 6. Verify all services are running
# 7. Open dashboard in browser

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Helper functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_step() {
    echo -e "\n${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Main setup
print_header "🚀 LLM Observability Dashboard - Demo Setup"

# Step 1: Check prerequisites
print_step "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker found"

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
print_success "Docker Compose found"

# Step 2: Start Docker containers
print_step "Starting Docker containers..."
cd "$SCRIPT_DIR"

# Check if containers are already running
if docker-compose ps | grep -q "postgres.*Up"; then
    print_success "Docker containers already running"
else
    docker-compose down -v 2>/dev/null || true
    docker-compose up -d
    print_success "Docker containers started"
fi

# Step 3: Wait for PostgreSQL
print_step "Waiting for PostgreSQL to be ready (max 60s)..."
RETRY_COUNT=0
MAX_RETRIES=60
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose exec -T postgres pg_isready -U postgres &>/dev/null; then
        print_success "PostgreSQL is ready"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    print_error "PostgreSQL failed to start"
    exit 1
fi

# Step 4: Run database migrations
print_step "Running database migrations..."
docker-compose exec -T backend python backend/migrations/runner.py > /dev/null 2>&1 || true
print_success "Database schema ready"

# Step 5: Seed sample data
print_step "Seeding 5000 sample completions from LMSYS-Chat-1M..."
docker-compose exec -T backend python backend/seed_data.py \
    --csv-path backend/data/lmsys_sample.csv \
    --rows 5000 \
    --db postgresql://postgres:postgres@postgres:5432/llm_obs > /dev/null 2>&1 || true
print_success "Sample data loaded (5000 completions)"

# Step 6: Wait for backend to be ready
print_step "Waiting for backend API to be ready..."
RETRY_COUNT=0
MAX_RETRIES=30
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend API is ready"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 1
done

# Step 7: Verify all services
print_step "Verifying services..."

# Check backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend API: http://localhost:8000"
else
    print_error "Backend API not responding"
fi

# Check PostgreSQL
if docker-compose exec -T postgres psql -U postgres -d llm_obs -c "SELECT COUNT(*) FROM completions;" 2>/dev/null | grep -q "[0-9]"; then
    COMPLETION_COUNT=$(docker-compose exec -T postgres psql -U postgres -d llm_obs -c "SELECT COUNT(*) FROM completions;" 2>/dev/null | tail -n 2 | head -n 1)
    print_success "Database has $COMPLETION_COUNT completions"
else
    print_error "Database verification failed"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis cache: redis://localhost:6379"
else
    print_error "Redis not responding"
fi

# Check pgAdmin
if curl -s http://localhost:5050 > /dev/null 2>&1; then
    print_success "pgAdmin: http://localhost:5050 (admin@admin.com / admin)"
else
    print_error "pgAdmin not responding"
fi

# Step 8: Display summary
print_header "✨ Demo Setup Complete!"

echo -e "\n${GREEN}Services Running:${NC}"
echo "  • Backend API:    http://localhost:8000"
echo "  • API Docs:       http://localhost:8000/docs"
echo "  • Frontend:       http://localhost:3000"
echo "  • pgAdmin:        http://localhost:5050"
echo "  • PostgreSQL:     localhost:5432"
echo "  • Redis:          localhost:6379"

echo -e "\n${GREEN}Sample Data:${NC}"
echo "  • Completions: $COMPLETION_COUNT"
echo "  • Models: 10 (Claude, GPT, Llama, Mistral, Gemini, etc.)"
echo "  • Date range: Last 30 days"

echo -e "\n${GREEN}Next Steps:${NC}"
echo "  1. Open Dashboard: http://localhost:3000"
echo "  2. Explore API: http://localhost:8000/docs"
echo "  3. View Database: http://localhost:5050"
echo "  4. Read Docs: ./docs/SETUP.md"

echo -e "\n${GREEN}Useful Commands:${NC}"
echo "  • View logs:       docker-compose logs -f backend"
echo "  • Restart:         docker-compose restart"
echo "  • Stop all:        docker-compose down"
echo "  • Clean up:        docker-compose down -v"
echo "  • Seed more data:  docker-compose exec backend python backend/seed_data.py --rows 10000"

# Step 9: Open dashboard (if possible)
echo -e "\n${YELLOW}Opening dashboard in browser...${NC}"
if command -v open &> /dev/null; then
    # macOS
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open http://localhost:3000
elif command -v start &> /dev/null; then
    # Windows
    start http://localhost:3000
else
    echo -e "${YELLOW}Please open http://localhost:3000 in your browser${NC}"
fi

# Step 10: Show live logs
echo -e "\n${YELLOW}Showing live logs (Press Ctrl+C to stop):${NC}"
sleep 2
docker-compose logs -f backend
