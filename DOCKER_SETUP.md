# Docker Setup Guide - LLM Observability Dashboard

Complete guide to running the LLM Observability Dashboard using Docker Compose.

## 📋 Overview

The `docker-compose.yml` file defines a complete development stack with:

1. **PostgreSQL 15** - Primary database
2. **pgAdmin 4** - Database administration GUI
3. **Redis 7** - In-memory cache
4. **Backend** - FastAPI application
5. **Frontend** - React/Vite application

All services communicate through a shared Docker network (`llm-obs-network`).

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)
- 4GB+ RAM available
- Ports 3000, 5050, 5432, 6379, 8000 available

### Start All Services

```bash
# Navigate to project root
cd llm-observability-dashboard

# Copy environment template
cp .env.example .env

# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Verify Services are Running

```bash
# View logs
docker-compose logs -f

# Check individual service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

## 🔌 Service Details & Access

### PostgreSQL Database
**Purpose:** Primary data storage for requests, metrics, traces, and user data

**Access:**
```
Host: localhost (or postgres from Docker)
Port: 5432
Username: postgres
Password: postgres
Database: llm_obs
```

**Connection String:**
```
postgresql://postgres:postgres@localhost:5432/llm_obs
```

**psql CLI Example:**
```bash
docker-compose exec postgres psql -U postgres -d llm_obs
```

### pgAdmin Web Interface
**Purpose:** Visual database management, query execution, schema inspection

**Access:**
```
URL: http://localhost:5050
Email: admin@admin.com
Password: admin
```

**Features:**
- Create and manage databases
- Execute SQL queries
- View table structures
- Monitor database performance
- Import/Export data

**Connection:**
- Server Name: `LLM Observability DB`
- Host: `postgres` (Docker network) or `localhost` (from host)
- Username/Password: postgres/postgres

### Redis Cache
**Purpose:** In-memory caching, session storage, job queues

**Access:**
```
Host: localhost (or redis from Docker)
Port: 6379
No authentication required (local dev only!)
```

**CLI Commands:**
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check connection
redis-cli ping
# Output: PONG

# View all keys
redis-cli KEYS *

# Get value
redis-cli GET llm_obs:cache_key

# Monitor in real-time
redis-cli MONITOR
```

### Backend API
**Purpose:** FastAPI server handling all business logic

**Access:**
```
URL: http://localhost:8000
API Docs: http://localhost:8000/docs (Swagger UI)
ReDoc: http://localhost:8000/redoc
Health Check: http://localhost:8000/health
```

**Logs:**
```bash
docker-compose logs -f backend
```

### Frontend Application
**Purpose:** React web interface for the dashboard

**Access:**
```
URL: http://localhost:3000
```

**Development:**
- Hot reload enabled for code changes
- Connected to backend via proxy at http://localhost:8000/api

## 📁 Volume Mounts

### Persistent Data
```yaml
postgres_data:      # PostgreSQL data directory
pgadmin_data:       # pgAdmin configuration
redis_data:         # Redis snapshots (if AOF enabled)
```

### Development Mounts
```yaml
./backend:/app      # Backend source code
./frontend:/app     # Frontend source code
```

## 🔄 Managing Services

### Stop All Services
```bash
docker-compose down
```

### Stop Services (Keep Volumes)
```bash
docker-compose down
```

### Stop Services (Remove All Data)
```bash
docker-compose down -v
```

### Restart a Single Service
```bash
docker-compose restart backend
```

### Rebuild Images
```bash
docker-compose build --no-cache
```

### Run One-Off Commands

**Database Initialization:**
```bash
docker-compose exec backend python -m backend.seed_data
```

**Database Migrations:**
```bash
docker-compose exec backend alembic upgrade head
```

**Backend Tests:**
```bash
docker-compose exec backend pytest backend/tests/
```

## 🔐 Environment Configuration

### Default .env File
Created from `.env.example` with defaults for development:

```env
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/llm_obs
REDIS_URL=redis://redis:6379/0
VITE_API_URL=http://localhost:8000
API_DEBUG=true
SECRET_KEY=dev-secret-key
```

### For Production
Update `.env` with:
- Strong `SECRET_KEY`
- Production database credentials
- Production Redis URL
- Proper CORS settings
- Security headers

```env
# Production example
DATABASE_URL=postgresql://prod_user:strong_pass@prod-db.example.com:5432/llm_obs
REDIS_URL=redis://:strong_pass@prod-redis.example.com:6379/0
SECRET_KEY=production-secret-key-minimum-32-chars
API_DEBUG=false
CORS_ORIGINS=["https://yourdomain.com"]
```

## 🐛 Troubleshooting

### Services Won't Start

**Check Port Conflicts:**
```bash
# macOS/Linux
lsof -i :5432    # PostgreSQL
lsof -i :6379    # Redis
lsof -i :8000    # Backend
lsof -i :3000    # Frontend
lsof -i :5050    # pgAdmin

# Windows (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 5432).OwningProcess
```

**Free Ports:**
```bash
# macOS/Linux - Kill process on port
sudo lsof -ti:5432 | xargs kill -9

# Or use different ports in docker-compose.yml
# Change "5432:5432" to "5433:5432" etc.
```

### Database Connection Issues

**Check Service Health:**
```bash
docker-compose ps
# STATUS should be "Up" with health status

# Check logs
docker-compose logs postgres
```

**Test Connection:**
```bash
docker-compose exec postgres psql -U postgres -c "SELECT 1"
```

### Frontend/Backend Not Communicating

**Check Network:**
```bash
# Verify network exists
docker network ls | grep llm-obs

# Check service DNS resolution
docker-compose exec frontend ping backend
docker-compose exec backend ping postgres
```

**Update API URL:**
In `.env`:
```env
VITE_API_URL=http://localhost:8000
```

### High Memory Usage

**Reduce Allocated Memory:**
```bash
# docker-compose.yml services section
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 512M  # Adjust as needed
```

### Data Persistence Issues

**Verify Volumes:**
```bash
docker volume ls | grep llm_obs
docker volume inspect llm_obs_postgres_data
```

**Recreate Volumes:**
```bash
# WARNING: This deletes all data!
docker-compose down -v
docker-compose up -d
```

## 📊 Database Maintenance

### Backup Database

**Using pg_dump:**
```bash
docker-compose exec postgres pg_dump -U postgres llm_obs > backup.sql
```

**Using pgAdmin:**
- Right-click database → Backup...
- Select backup format (custom, tar, plain)
- Download backup file

### Restore Database

```bash
# From SQL file
docker-compose exec -T postgres psql -U postgres llm_obs < backup.sql

# In pgAdmin
- Right-click database → Restore...
- Select backup file
- Execute
```

### Database Optimization

**Analyze Tables:**
```bash
docker-compose exec postgres psql -U postgres llm_obs -c "ANALYZE;"
```

**Vacuum:**
```bash
docker-compose exec postgres psql -U postgres llm_obs -c "VACUUM ANALYZE;"
```

**Check Index Health:**
```bash
docker-compose exec postgres psql -U postgres llm_obs << EOF
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
EOF
```

## 📝 Useful Docker Commands

```bash
# View all resources
docker-compose ps -a
docker volume ls
docker network ls

# Resource usage
docker stats

# View configuration
docker-compose config

# Pull latest images
docker-compose pull

# Clean up unused resources
docker system prune
docker system prune -a --volumes

# Execute commands
docker-compose exec SERVICE_NAME COMMAND

# View logs (live)
docker-compose logs -f SERVICE_NAME

# Copy files
docker cp container:path/file local/path/file
docker cp local/path/file container:path/file
```

## 🔗 Health Checks

All services include health checks. View status:

```bash
docker-compose ps
```

**Manual Health Checks:**

```bash
# PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Redis
docker-compose exec redis redis-cli ping

# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000/
```

## 🆘 Getting Help

**View Container Logs:**
```bash
docker-compose logs [SERVICE_NAME]
```

**Enter Container Shell:**
```bash
docker-compose exec SERVICE_NAME /bin/sh
# Or bash if available
docker-compose exec SERVICE_NAME /bin/bash
```

**Example Debugging:**
```bash
# Check environment variables in container
docker-compose exec backend env | grep DATABASE

# Test database connection
docker-compose exec backend python -c \
  "from backend.database import engine; print(engine.connect())"
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres/)
- [pgAdmin Documentation](https://www.pgadmin.org/docs/)
- [Redis Docker Image](https://hub.docker.com/_/redis/)

---

**Last Updated:** 2026-06-11
