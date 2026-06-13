# Architecture - LLM Observability Dashboard

Comprehensive overview of the system architecture, components, and data flow.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  LLM Applications (Your Code)               │
│           (Using Anthropic SDK, OpenAI, etc.)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ (Wrapped with Python SDK)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         LLM Observer SDK (Python Package)                   │
│  • Intercepts LLM API calls                                 │
│  • Extracts: prompt, response, tokens, latency              │
│  • Sends to Collector API (async)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                 POST /api/v1/logs
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           FastAPI Backend (Python)                          │
│  • Request validation & parsing                             │
│  • Database writes (PostgreSQL)                             │
│  • Evaluation pipeline (LLM Judge)                          │
│  • Metrics queries & aggregations                           │
│  • Cache layer (Redis)                                      │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
 ┌──────────────┐  ┌──────────────┐   ┌──────────────┐
 │ PostgreSQL   │  │ Redis Cache  │   │ Anthropic    │
 │ • Completions│  │ • Hot metrics│   │ Claude API   │
 │ • Evals      │  │ • Sessions   │   │ (for evals)  │
 │ • Metrics    │  │              │   │              │
 └──────┬───────┘  └──────────────┘   └──────────────┘
        │
        │ GET /api/v1/metrics/*
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│          React Dashboard (JavaScript)                       │
│  • Real-time metrics charts                                 │
│  • Model comparison & filtering                             │
│  • Interactive visualizations (Recharts)                    │
│  • User preferences & settings                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Python SDK (SDK Layer)

**Location:** `backend/sdk/llm_observer.py`

**Responsibilities:**
- Wrap LLM client calls (Claude, OpenAI, etc.)
- Extract metadata (tokens, latency, cost)
- Batch requests for efficiency
- Handle network retries
- Local caching

**Key Methods:**
```python
observer = LLMObserver("http://localhost:8000")
observer.wrap_claude_client(client)
observer.log_completion(prompt, response, model, ...)
```

**Benefits:**
- Non-intrusive integration (drop-in wrapper)
- Handles retries & failures
- Async logging (doesn't block user code)
- Local buffering for reliability

---

### 2. FastAPI Backend (API & Logic Layer)

**Location:** `backend/main.py`

**Responsibilities:**
- Expose REST API endpoints
- Validate incoming data
- Persist to database
- Run evaluation pipeline
- Cache hot metrics
- Serve real-time data

**Routes:**
- `POST /logs` - Single completion
- `POST /logs/batch` - Batch ingestion
- `GET /metrics/*` - Various metrics queries
- `POST /evals` - Evaluation submission
- `GET /evals` - Evaluation retrieval

**Performance Characteristics:**
- Log ingestion: ~1000 logs/second
- Metrics query: <500ms
- Batch size: 1-1000 items

---

### 3. Database Layer

**Technology:** PostgreSQL 15 + TimescaleDB (optional)

**Core Tables:**

#### `completions` (Primary)
```sql
id SERIAL PRIMARY KEY
conversation_id VARCHAR(255)
prompt TEXT
response TEXT
model VARCHAR(100)
tokens_in INT
tokens_out INT
latency_ms FLOAT
cost_usd FLOAT
user_id VARCHAR(100)
success BOOLEAN
timestamp TIMESTAMP (indexed)
```

**Indexes:**
- `idx_completions_timestamp` - For time-range queries
- `idx_completions_model` - For model filtering
- `idx_completions_user_timestamp` - For user analytics
- Composite indexes for common patterns

#### `eval_results` (Evaluations)
```sql
id SERIAL PRIMARY KEY
completion_id INT (FK)
eval_type VARCHAR(50)  -- llm_judge, bleu, rouge
score FLOAT  -- 0-1 normalized
criteria VARCHAR(255)
explanation TEXT
timestamp TIMESTAMP
```

#### `metrics` (Time-Series)
```sql
id SERIAL PRIMARY KEY
metric_name VARCHAR(100)
metric_type VARCHAR(50)  -- gauge, counter, histogram
metric_value FLOAT
model VARCHAR(100)
user_id VARCHAR(100)
window_start TIMESTAMP
window_end TIMESTAMP
recorded_at TIMESTAMP
```

**Materialized Views (Analytics):**

```sql
-- model_daily_performance
SELECT
  DATE(timestamp),
  model,
  COUNT(*) as request_count,
  AVG(latency_ms) as avg_latency,
  SUM(cost_usd) as total_cost,
  ...
FROM completions
GROUP BY DATE(timestamp), model;

-- user_daily_usage
SELECT
  DATE(timestamp),
  user_id,
  COUNT(*) as request_count,
  SUM(cost_usd) as total_cost,
  ...
FROM completions
WHERE user_id IS NOT NULL
GROUP BY DATE(timestamp), user_id;
```

**Storage:**
- 5,000 logs: ~5 MB
- 100,000 logs: ~100 MB
- 1M logs: ~1 GB

---

### 4. Cache Layer

**Technology:** Redis 7

**Usage:**
- Hot metrics (updated every 30s)
- Session data
- Rate limiting counters
- Job queues (for evaluations)

**TTLs:**
- Metrics: 5 minutes
- Sessions: 24 hours
- Temp data: 1 hour

**Performance Impact:**
- Metrics API: <100ms (vs. 500ms from DB)
- Saves ~90% database queries

---

### 5. Evaluation Engine

**Location:** `backend/evals/`

**Supported Methods:**

#### LLM Judge (Claude)
```python
from backend.evals.llm_judge import LLMJudge

judge = LLMJudge()
score = judge.evaluate(
    prompt="What is ML?",
    response="Machine learning is...",
    criteria="helpfulness, accuracy"
)
# Returns: 0.0-1.0
```

#### Text Metrics (NLTK/sentence-transformers)
```python
from backend.evals.text_metrics import TextMetrics

metrics = TextMetrics()
bleu = metrics.bleu_score(reference, hypothesis)
rouge = metrics.rouge_score(reference, hypothesis)
similarity = metrics.semantic_similarity(response1, response2)
```

**Integration:**
- Async evaluation job queue
- Results stored in `eval_results` table
- Accessed via `/evals` endpoint

---

## Data Flow

### Request Logging Flow

```
1. User's LLM App calls Claude API
2. SDK wrapper intercepts call
3. SDK extracts: prompt, response, tokens, latency, cost
4. SDK buffers (batches up to 100)
5. SDK POSTs to /api/v1/logs/batch
6. Backend validates & persists to DB
7. Evaluation triggered (async job)
8. Results stored in eval_results table
9. Dashboard queries metrics (via cache)
```

### Query Flow

```
1. User opens dashboard at http://localhost:3000
2. Frontend requests /api/v1/metrics/summary
3. Backend checks Redis cache
4. If cached, returns immediately (<100ms)
5. If not cached:
   a. Queries PostgreSQL aggregates
   b. Computes summary stats
   c. Stores in Redis (5 min TTL)
6. Frontend receives JSON
7. React re-renders with new data
```

---

## Technology Stack

| Layer | Component | Technology | Purpose |
|-------|-----------|-----------|---------|
| **Frontend** | Web App | React 18 + Vite | Dashboard UI |
| **Frontend** | Charts | Recharts | Data visualization |
| **Frontend** | Styling | Tailwind CSS | UI styling |
| **Backend** | API | FastAPI | REST endpoints |
| **Backend** | ORM | SQLAlchemy | Database abstraction |
| **Backend** | Validation | Pydantic | Schema validation |
| **Backend** | Async | AsyncIO | Concurrent operations |
| **Database** | Primary | PostgreSQL 15 | Request logging, metrics |
| **Database** | Cache | Redis 7 | Hot data caching |
| **Evaluation** | LLM Judge | Claude API | Quality assessment |
| **Evaluation** | Text Metrics | NLTK + sentence-transformers | BLEU/ROUGE/similarity |
| **DevOps** | Containers | Docker | Packaging |
| **DevOps** | Orchestration | Docker Compose | Local development |
| **DevOps** | CI/CD | GitHub Actions | Testing & deployment |

---

## Scalability Considerations

### Current (Development)

- **Scale:** ~1000 logs/hour
- **Users:** Single developer
- **Database:** SQLite or local PostgreSQL

### Small Production

- **Scale:** ~100,000 logs/day
- **Database:** PostgreSQL with standard indexes
- **Cache:** Redis for hot metrics
- **Deployment:** Single server or small cluster

### Large Production

- **Scale:** ~10M+ logs/day
- **Database:** PostgreSQL + TimescaleDB (time-series compression)
- **Sharding:** Partition by user_id or time window
- **Cache:** Redis cluster or Memcached
- **Metrics:** Separate analytics database
- **Queues:** Kafka for reliable ingestion
- **Monitoring:** Prometheus + Grafana

### Optimization Strategies

1. **Database:**
   - Enable TimescaleDB hypertables
   - Partition by date
   - Archive old data
   - Compression

2. **Caching:**
   - Cache computed metrics
   - Use Redis Streams for events
   - Implement cache-aside pattern

3. **API:**
   - Pagination for large result sets
   - Filtering on write-time
   - Async evaluation jobs

4. **Frontend:**
   - Lazy load charts
   - Virtual scrolling for tables
   - Background data refresh

---

## Security Architecture

### Authentication

Currently unauthenticated (development mode).

For production:
- JWT tokens with exp/iat claims
- API key per user
- Rate limiting per key
- HTTPS required

### Authorization

- User can only see their own data
- Admin can see all data
- Evaluation engine (internal service)

### Data Privacy

- Optional prompt/response hashing
- Sensitive data masking
- Audit logging (optional)

### Network

- HTTPS/TLS for external APIs
- Firewall rules for database
- Private Redis (no auth in dev, auth in prod)

---

## Monitoring & Observability

### Metrics Collected

- Request count by model
- Latency percentiles
- Cost per model
- Error rates
- Evaluation scores

### Logging

- Access logs (FastAPI)
- Application logs (app.log)
- Database slow queries
- Error tracking

### Health Checks

- Backend: `GET /health`
- Database: pg_isready
- Redis: PING
- API test: sample request

---

## Deployment Topology

### Docker Compose (Development)

```
┌─────────────────────────────────────────┐
│         Docker Network                  │
│  ┌──────────┐  ┌──────────┐  ┌───────┐ │
│  │ Postgres │  │ Redis    │  │Backend│ │
│  │ :5432    │  │ :6379    │  │ :8000 │ │
│  └──────────┘  └──────────┘  └───────┘ │
│  ┌──────────┐  ┌──────────────────────┐ │
│  │ pgAdmin  │  │     Frontend        │ │
│  │ :5050    │  │      :3000          │ │
│  └──────────┘  └──────────────────────┘ │
└─────────────────────────────────────────┘
```

### Kubernetes (Production)

```
┌─────────────────────────────────────────┐
│      Kubernetes Cluster                 │
│  ┌──────────────────────────────────┐   │
│  │  Frontend Deployment (2 replicas)│   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │  Backend Deployment (3 replicas) │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │   PostgreSQL StatefulSet         │   │
│  │   (with persistent volume)       │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │   Redis StatefulSet              │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## Performance Targets

| Operation | Target | Current |
|-----------|--------|---------|
| Log ingestion | <100ms | ~50ms |
| Batch ingest (100) | <500ms | ~200ms |
| Metrics query | <500ms | ~300ms |
| Eval processing | <5s | ~2s |
| Dashboard load | <2s | ~1.5s |
| Real-time refresh | 30s | 30s |

---

## Future Enhancements

1. **Time-Series Optimization** - Enable TimescaleDB
2. **Distributed Tracing** - OpenTelemetry integration
3. **Advanced Evals** - Custom evaluator plugins
4. **Real-time Alerts** - WebSocket notifications
5. **Multi-tenancy** - Isolation per organization
6. **GraphQL API** - Alternative query language
7. **Mobile Dashboard** - React Native app

---

**Last Updated:** 2026-06-11
