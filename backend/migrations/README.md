# Database Migrations

This directory contains SQL migration files for the LLM Observability Dashboard.

## Overview

Migrations are executed sequentially in numbered order. Each migration file modifies the database schema to add new tables, indexes, or other database objects.

## Files

### `001_init_schema.sql`
**Initial schema setup**

Creates all core tables:
- `users` - Dashboard users and API key management
- `models` - LLM model metadata
- `completions` - LLM API requests and responses
- `traces` - Distributed tracing data
- `eval_results` - Evaluation scores and feedback
- `metrics` - Aggregated metrics and analytics
- `alerts` - Alert events and notifications
- `sessions` - User session management (optional)
- `audit_logs` - Compliance and audit tracking (optional)

Also includes:
- Primary keys and constraints
- Performance indexes
- Materialized views for analytics
- Stored procedures for statistics
- Comments and documentation

### `runner.py`
**Migration execution script**

Executes all SQL migration files in order. Tracks executed migrations to avoid re-running them.

## Usage

### Running Migrations

#### Option 1: Using the Python Runner

```bash
# Set DATABASE_URL
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/llm_obs

# Run migrations
cd backend/migrations
python runner.py
```

#### Option 2: Using Docker

```bash
# Run migrations in Docker container
docker-compose exec backend python -m backend.migrations.runner
```

#### Option 3: Using psql CLI

```bash
# Connect and execute directly
psql postgresql://postgres:postgres@localhost:5432/llm_obs < 001_init_schema.sql
```

#### Option 4: From Backend Application

```python
from backend.migrations.runner import MigrationRunner

runner = MigrationRunner('postgresql://postgres:postgres@localhost:5432/llm_obs')
success = runner.run()
```

### Automatic Migrations on Startup

Update `backend/main.py` to run migrations on app startup:

```python
from fastapi import FastAPI
from backend.migrations.runner import MigrationRunner

app = FastAPI()

@app.on_event("startup")
def startup_event():
    """Run database migrations on startup"""
    runner = MigrationRunner(os.getenv('DATABASE_URL'))
    success = runner.run()
    if not success:
        raise Exception("Database migrations failed")
```

## Schema Design

### Core Tables

#### `completions`
Stores every LLM API request and response

**Key columns:**
- `conversation_id` - Groups related requests
- `model` - LLM model used
- `prompt_tokens`, `completion_tokens` - Token counts
- `latency_ms` - Response time
- `cost_usd` - Estimated cost
- `success` - Request success/failure
- `timestamp` - When request occurred

**Indexes:**
- timestamp (for time-range queries)
- model (for model filtering)
- user_id (for user-specific queries)
- Combined indexes for common query patterns

#### `eval_results`
Stores evaluation scores for completions

**Supports multiple evaluation types:**
- LLM judge (e.g., using Claude/GPT as evaluator)
- BLEU/ROUGE scores
- Semantic similarity scores
- Custom metrics

#### `traces`
Distributed tracing data for request flows

**Contains:**
- Span information
- Parent-child relationships
- Timing and duration
- Status and error information
- JSONB for flexible attributes

#### `metrics`
Time-series metrics for aggregated analytics

**Examples:**
- Daily request counts per model
- Average latency by time period
- Cost trends
- Success rates

### Materialized Views

#### `model_daily_performance`
Aggregated model performance by day

Useful for:
- Dashboard charts
- Model comparison
- Performance trends

#### `user_daily_usage`
User request counts and costs by day

Useful for:
- Usage tracking
- Billing calculations
- User analytics

### Constraints & Validation

All tables include:
- NOT NULL constraints where appropriate
- CHECK constraints for data validation
- Foreign keys for referential integrity
- Unique constraints for identifiers

Examples:
```sql
CONSTRAINT completions_tokens_positive CHECK (prompt_tokens >= 0)
CONSTRAINT completions_temperature_valid CHECK (temperature BETWEEN 0 AND 2)
CONSTRAINT alerts_resolved_after_triggered CHECK (resolved_at >= triggered_at)
```

## Performance Optimizations

### Indexes
```sql
-- Fast lookups by timestamp (most common query)
CREATE INDEX idx_completions_timestamp ON completions(timestamp DESC);

-- Filter by model
CREATE INDEX idx_completions_model ON completions(model);

-- Composite indexes for common patterns
CREATE INDEX idx_completions_user_timestamp 
    ON completions(user_id, timestamp DESC);
```

### Materialized Views
Pre-computed aggregations for faster analytics queries:
```sql
-- Refresh when data updates significantly
REFRESH MATERIALIZED VIEW model_daily_performance;
```

### Future: TimescaleDB
For production with high data volume, consider TimescaleDB:
```sql
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convert completions to hypertable
SELECT create_hypertable('completions', 'timestamp', if_not_exists => TRUE);
```

## Migration Workflow

### Adding a New Migration

1. Create a new file: `002_add_feature.sql`
2. Write SQL to add new tables/columns/indexes
3. Test locally:
   ```bash
   psql postgresql://localhost/llm_obs < 002_add_feature.sql
   ```
4. Verify with `psql`:
   ```sql
   \dt  -- List all tables
   \di  -- List all indexes
   ```
5. Commit to git

### Rollback Strategy

For now, migrations are **append-only** (forward-only).

For rollback capability:
1. Create `002_add_feature.sql` (adds new schema)
2. Create `003_add_feature_rollback.sql` (removes new schema)
3. Only run rollback migration if needed

### Naming Convention

- Prefix with 3-digit number (001, 002, 003...)
- Use descriptive names: `001_init_schema.sql`
- Number in git order (commits to this directory)

## Testing Migrations

### Test in Isolated Database

```bash
# Create test database
createdb llm_obs_test

# Run migrations
export DATABASE_URL=postgresql://postgres:postgres@localhost/llm_obs_test
python runner.py

# Verify schema
psql llm_obs_test -c "\dt"

# Cleanup
dropdb llm_obs_test
```

### Test with Docker

```bash
# Migrations run automatically on docker-compose up
docker-compose up -d postgres

# Wait for healthcheck
docker-compose ps postgres

# Verify in pgAdmin (http://localhost:5050)
# or via CLI
docker-compose exec postgres psql -U postgres -d llm_obs -c "\dt"
```

## Monitoring Migrations

### Check Migration History

```sql
-- View executed migrations
SELECT * FROM schema_migrations ORDER BY executed_at;
```

### View Table Structure

```sql
-- List all tables
\dt

-- Describe a table
\d completions

-- List indexes
\di

-- View constraints
SELECT constraint_name, table_name
FROM information_schema.table_constraints
WHERE table_schema = 'public';
```

### Check Index Usage

```sql
-- Unused indexes
SELECT schemaname, tablename, indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0;

-- Most used indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## Troubleshooting

### Migrations Fail

**Check logs:**
```bash
python runner.py  # Detailed output
```

**Common issues:**
1. Database connection error → Check DATABASE_URL
2. Schema already exists → Safe to re-run (uses `IF NOT EXISTS`)
3. Invalid SQL → Check syntax in .sql file

### Re-run Migrations

```bash
# Migrations are idempotent (safe to re-run)
# They use IF NOT EXISTS clauses
python runner.py
```

### Reset Database

**WARNING: Destructive operation!**

```bash
# Drop everything and start fresh
dropdb llm_obs
createdb llm_obs

# Run migrations
python runner.py
```

## Documentation

See comments in `001_init_schema.sql` for detailed table documentation.

Key design decisions:
- JSONB columns for flexible attributes (traces, metrics)
- Materialized views for analytics performance
- Time-series optimization (future: TimescaleDB)
- Audit logging for compliance
- Hash columns for sensitive data (optional)

---

**Last Updated:** 2026-06-11
