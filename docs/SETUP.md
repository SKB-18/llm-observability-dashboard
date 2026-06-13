# Setup Guide - LLM Observability Dashboard

Complete step-by-step instructions for setting up the LLM Observability Dashboard locally.

## System Requirements

- **Docker & Docker Compose** - For PostgreSQL, Redis, pgAdmin
- **Python 3.9+** - For backend development
- **Node.js 16+** - For frontend development
- **Git** - For cloning the repository
- **4GB RAM minimum** - For running all services
- **2GB disk space** - For sample dataset

## Option 1: Docker Compose (Recommended)

### Quick Start (5 minutes)

```bash
# 1. Clone repository
git clone <repository-url>
cd llm-observability-dashboard

# 2. Copy environment template
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Load sample data
docker-compose exec backend python backend/seed_data.py --rows 5000

# 5. Verify everything is running
docker-compose ps
```

### Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend Dashboard | http://localhost:3000 | N/A |
| Backend API | http://localhost:8000 | N/A |
| API Docs (Swagger) | http://localhost:8000/docs | N/A |
| pgAdmin | http://localhost:5050 | admin@admin.com / admin |
| PostgreSQL | localhost:5432 | postgres / postgres |
| Redis | localhost:6379 | No auth |

### Check Service Health

```bash
# View logs
docker-compose logs -f

# Check specific service
docker-compose logs backend

# View running containers
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Verify database
docker-compose exec postgres psql -U postgres -d llm_obs -c "SELECT COUNT(*) FROM completions;"
```

---

## Option 2: Local Development Setup

### Prerequisites

```bash
# Python 3.9+
python --version

# Node 16+
node --version

# PostgreSQL 15
# For macOS: brew install postgresql
# For Ubuntu: sudo apt-get install postgresql-15
```

### 1. Clone Repository

```bash
git clone <repository-url>
cd llm-observability-dashboard
```

### 2. Configure Environment

Create `.env` file in project root:

```env
# Database (use localhost if PostgreSQL running locally)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/llm_obs

# Redis
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# JWT (change in production!)
SECRET_KEY=your-super-secret-key-change-in-production

# Frontend
VITE_API_URL=http://localhost:8000

# Optional: LLM API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### 3. Create Databases

```bash
# Create main database
createdb llm_obs

# Verify
psql -U postgres -d llm_obs -c "\dt"
```

### 4. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Run migrations
python backend/migrations/runner.py

# Seed sample data
python backend/seed_data.py --rows 5000

# Start backend
uvicorn backend.main:app --reload
```

Backend will be available at http://localhost:8000

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at http://localhost:5173

### 6. Redis Setup (Optional, for caching)

```bash
# macOS
brew install redis
redis-server

# Ubuntu
sudo apt-get install redis-server
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

---

## Verification Checklist

### Database

```bash
# Connect to database
psql -U postgres -d llm_obs

# Check tables
\dt

# Count completions
SELECT COUNT(*) FROM completions;

# Exit
\q
```

### Backend

```bash
# Health check
curl http://localhost:8000/health

# Get metrics
curl http://localhost:8000/api/v1/metrics/summary

# API documentation
open http://localhost:8000/docs
```

### Frontend

```bash
# Should load at
open http://localhost:5173

# Check browser console (F12) for errors
```

### Data

```bash
# Verify sample data loaded
curl http://localhost:8000/api/v1/metrics/summary | jq

# Should show non-zero totals:
# {
#   "total_requests": 5000,
#   "total_cost_usd": 12.45,
#   "avg_latency_ms": 645.3,
#   ...
# }
```

---

## Troubleshooting

### Docker Issues

**Services won't start:**
```bash
# Check port conflicts
lsof -i :5432   # PostgreSQL
lsof -i :6379   # Redis
lsof -i :8000   # Backend
lsof -i :3000   # Frontend

# Kill process on specific port (macOS/Linux)
sudo lsof -ti:5432 | xargs kill -9

# Or use different ports in docker-compose.yml
```

**Database connection error:**
```bash
# Ensure PostgreSQL is healthy
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Wait for healthcheck (30 seconds)
docker-compose exec postgres pg_isready
```

### Backend Issues

**Import errors:**
```bash
# Reinstall dependencies
pip install -r backend/requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.9+
```

**Port 8000 already in use:**
```bash
# Use different port
uvicorn backend.main:app --reload --port 8001

# Or kill process on 8000
sudo lsof -ti:8000 | xargs kill -9
```

**Database tables not created:**
```bash
# Run migrations manually
python backend/migrations/runner.py

# Or seed creates tables
python backend/seed_data.py
```

### Frontend Issues

**npm install fails:**
```bash
# Clear cache
npm cache clean --force

# Delete node_modules and try again
rm -rf node_modules package-lock.json
npm install
```

**API calls failing (CORS error):**
```bash
# Ensure backend is running
curl http://localhost:8000/health

# Check VITE_API_URL in .env
# Should be: VITE_API_URL=http://localhost:8000
```

### Data Issues

**No data in dashboard:**
```bash
# Check if seed ran
curl http://localhost:8000/api/v1/metrics/summary

# Load data manually
python backend/seed_data.py --rows 5000

# Verify in database
psql -U postgres -d llm_obs -c "SELECT COUNT(*) FROM completions;"
```

**CSV file not found:**
```bash
# Check file exists
ls backend/data/lmsys_sample.csv

# Specify path explicitly
python backend/seed_data.py --csv-path backend/data/lmsys_sample.csv
```

---

## Advanced Configuration

### PostgreSQL Tuning

For better performance with large datasets:

```sql
-- Connect to database
psql -U postgres -d llm_obs

-- Enable TimescaleDB extension (optional, for time-series)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create hypertable for completions
SELECT create_hypertable('completions', 'timestamp', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX idx_completions_timestamp ON completions(timestamp DESC);
CREATE INDEX idx_completions_model ON completions(model);
```

### Redis Optimization

```bash
# Enable AOF (persistence)
redis-cli CONFIG SET appendonly yes

# Set memory policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Monitor stats
redis-cli INFO stats
```

---

## Next Steps

1. **Load Your Data** - Connect your LLM application and start logging
2. **Configure Alerts** - Set up monitoring thresholds in dashboard
3. **Explore API** - Read [API.md](API.md) for integration details
4. **Deploy** - See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
5. **Contribute** - Check [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

---

**Last Updated:** 2026-06-11
