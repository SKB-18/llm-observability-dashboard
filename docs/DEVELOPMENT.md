# Development Guide - LLM Observability Dashboard

Complete guide for contributing to the project.

## Project Structure

```
llm-observability-dashboard/
├── backend/                    # FastAPI backend
│   ├── main.py                # App entry point
│   ├── config.py              # Configuration
│   ├── models.py              # SQLAlchemy ORM models
│   ├── schemas.py             # Pydantic schemas
│   ├── database.py            # Database connection
│   ├── seed_data.py           # Data loader
│   │
│   ├── routes/                # API endpoints
│   │   ├── logs.py            # Log ingestion
│   │   ├── metrics.py         # Metrics queries
│   │   └── evals.py           # Evaluation endpoints
│   │
│   ├── evals/                 # Evaluation engines
│   │   ├── llm_judge.py       # Claude-based evaluation
│   │   └── text_metrics.py    # BLEU/ROUGE/similarity
│   │
│   ├── utils/                 # Helper functions
│   │   ├── db.py              # Database utilities
│   │   ├── cache.py           # Redis caching
│   │   └── helpers.py         # Common utilities
│   │
│   ├── sdk/                   # Python SDK
│   │   └── llm_observer.py    # Main SDK class
│   │
│   ├── data/                  # Data files
│   │   ├── sample_logs.csv    # 500 sample logs
│   │   ├── lmsys_sample.csv   # 5000 LMSYS logs
│   │   └── evals_dataset.csv  # 100 evaluation samples
│   │
│   ├── migrations/            # Database migrations
│   │   ├── 001_init_schema.sql
│   │   └── runner.py
│   │
│   ├── tests/                 # Backend tests
│   │   ├── test_logs.py
│   │   ├── test_metrics.py
│   │   └── test_evals.py
│   │
│   └── requirements.txt       # Dependencies
│
├── frontend/                  # React app
│   ├── public/
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── Dashboard.jsx
│   │   │   ├── MetricsChart.jsx
│   │   │   └── ...
│   │   ├── hooks/             # Custom hooks
│   │   │   └── useMetrics.js
│   │   ├── services/          # API calls
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── sdk/                       # Python SDK package
│   ├── setup.py
│   └── llm_observer/
│       ├── __init__.py
│       └── client.py
│
├── docker/                    # Docker files
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── pgadmin/
│       └── servers.json
│
├── docs/                      # Documentation
│   ├── SETUP.md
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── DEVELOPMENT.md
│
├── .github/workflows/         # CI/CD
│   └── tests.yml
│
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Makefile
├── README.md
└── requirements.txt
```

---

## Getting Started

### 1. Clone & Setup

```bash
# Clone
git clone <repo>
cd llm-observability-dashboard

# Setup
cp .env.example .env
docker-compose up -d
python backend/seed_data.py --rows 5000

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### 2. Verify Everything Works

```bash
# Backend health
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs

# Frontend
open http://localhost:5173
```

---

## Adding New Features

### Add a New Metric

**Step 1: Database Query** (`backend/utils/db.py`)
```python
def get_metric_percentile_latency(model=None, start_date=None):
    query = """
    SELECT 
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) as p99
    FROM completions
    WHERE 1=1
    """
    if model:
        query += f" AND model = '{model}'"
    if start_date:
        query += f" AND timestamp >= '{start_date}'"
    
    return db.execute(query).fetchone()
```

**Step 2: API Endpoint** (`backend/routes/metrics.py`)
```python
from fastapi import APIRouter, Query
from backend.utils.db import get_metric_percentile_latency

router = APIRouter(prefix="/metrics")

@router.get("/latency-percentiles")
async def get_latency_percentiles(
    model: str = Query(None),
    start_date: str = Query(None)
):
    result = get_metric_percentile_latency(model, start_date)
    return {
        "p95": result[0],
        "p99": result[1]
    }
```

**Step 3: Frontend Hook** (`frontend/src/hooks/useMetrics.js`)
```javascript
export function useLatencyPercentiles() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    fetch(`${API_URL}/metrics/latency-percentiles`)
      .then(r => r.json())
      .then(setData);
  }, []);
  
  return data;
}
```

**Step 4: React Component** (`frontend/src/components/LatencyChart.jsx`)
```jsx
import { useLatencyPercentiles } from '../hooks/useMetrics';

export function LatencyChart() {
  const data = useLatencyPercentiles();
  
  return (
    <div>
      <h3>Latency Percentiles</h3>
      <p>P95: {data?.p95.toFixed(2)}ms</p>
      <p>P99: {data?.p99.toFixed(2)}ms</p>
    </div>
  );
}
```

**Step 5: Add to Dashboard**
```jsx
import { LatencyChart } from './LatencyChart';

export function Dashboard() {
  return (
    <div>
      <LatencyChart />
      {/* Other components */}
    </div>
  );
}
```

**Step 6: Test**
```bash
# Test the endpoint
curl http://localhost:8000/api/v1/metrics/latency-percentiles

# Check frontend
open http://localhost:5173
```

---

### Add a New Evaluator

**Step 1: Create Evaluator Class** (`backend/evals/custom_evaluator.py`)
```python
from abc import ABC, abstractmethod

class BaseEvaluator(ABC):
    @abstractmethod
    def evaluate(self, prompt: str, response: str, **kwargs) -> float:
        """Return score 0-1"""
        pass

class CustomEvaluator(BaseEvaluator):
    def evaluate(self, prompt: str, response: str, criteria=None, **kwargs) -> float:
        # Your evaluation logic
        score = 0.85  # Calculate score
        return score
```

**Step 2: Register Evaluator** (`backend/evals/__init__.py`)
```python
from .custom_evaluator import CustomEvaluator

EVALUATORS = {
    "custom": CustomEvaluator(),
    "llm_judge": LLMJudge(),
    "bleu": BLEUEvaluator(),
}

def evaluate(eval_type: str, prompt: str, response: str, **kwargs):
    if eval_type not in EVALUATORS:
        raise ValueError(f"Unknown evaluator: {eval_type}")
    return EVALUATORS[eval_type].evaluate(prompt, response, **kwargs)
```

**Step 3: Add Endpoint** (`backend/routes/evals.py`)
```python
@router.post("/evaluate")
async def run_evaluation(
    completion_id: int,
    eval_type: str
):
    completion = get_completion(completion_id)
    score = evaluate(eval_type, completion.prompt, completion.response)
    
    # Store result
    result = EvalResult(
        completion_id=completion_id,
        eval_type=eval_type,
        score=score
    )
    db.add(result)
    db.commit()
    
    return {"score": score}
```

**Step 4: Test**
```bash
# Test endpoint
curl -X POST http://localhost:8000/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{"completion_id": 1, "eval_type": "custom"}'
```

---

## Testing

### Backend Tests

```bash
cd backend

# All tests
pytest tests/ -v

# Specific test
pytest tests/test_logs.py::test_log_creation -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# By marker
pytest -m unit      # Unit tests only
pytest -m integration  # Integration tests
```

### Frontend Tests

```bash
cd frontend

# All tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

### Integration Tests

```bash
# Full end-to-end test
make test

# Or manually
pytest backend/tests/ -m integration
npm test -- --testMatch="**/e2e/**"
```

### Test Structure

```python
# backend/tests/test_logs.py
import pytest
from backend.routes.logs import router
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.unit
def test_log_creation(client):
    response = client.post("/logs", json={
        "prompt": "What is ML?",
        "response": "Machine learning is...",
        "model": "gpt-4",
        "tokens_in": 10,
        "tokens_out": 50,
        "latency_ms": 500,
        "cost_usd": 0.001
    })
    
    assert response.status_code == 200
    assert response.json()["status"] == "logged"

@pytest.mark.integration
def test_log_stored_in_db(client):
    client.post("/logs", json={...})
    
    # Verify in database
    count = db.query(Completion).count()
    assert count > 0
```

---

## Code Style

### Python

**Format with Black:**
```bash
black backend/ --line-length=120
```

**Lint with Flake8:**
```bash
flake8 backend/ --max-line-length=120
```

**Type check:**
```bash
mypy backend/
```

**Sort imports:**
```bash
isort backend/
```

### JavaScript

**Format:**
```bash
npm run format  # Prettier
```

**Lint:**
```bash
npm run lint    # ESLint
```

---

## Debugging

### Backend

**View logs:**
```bash
docker-compose logs backend
docker-compose logs -f backend  # Follow
```

**Debug specific route:**
```python
from fastapi import FastAPI
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.get("/debug")
async def debug():
    logger.debug("Debug message")
    return {"status": "ok"}
```

**Use pdb:**
```python
import pdb; pdb.set_trace()
```

**Test in isolation:**
```python
# In test file
from backend.models import Completion
from backend.database import SessionLocal

def test_isolation():
    db = SessionLocal()
    
    # Test code here
    
    db.close()
```

### Frontend

**Browser DevTools:**
- F12 for Developer Tools
- React DevTools extension
- Network tab for API calls

**Debug in VS Code:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "chrome",
      "request": "launch",
      "name": "Launch Chrome",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/frontend/src"
    }
  ]
}
```

### Database

```bash
# Connect
docker-compose exec postgres psql -U postgres -d llm_obs

# View schema
\dt

# Run query
SELECT * FROM completions LIMIT 5;

# View indexes
\di

# Exit
\q
```

---

## Common Tasks

### Reset Database

```bash
# Remove all data
docker-compose exec postgres psql -U postgres -d llm_obs -c "TRUNCATE completions CASCADE;"

# Or complete reset
docker-compose down -v
docker-compose up -d
python backend/seed_data.py
```

### Create Database Migration

```bash
# Create schema change
# backend/migrations/002_add_feature.sql
CREATE TABLE new_table (...);

# Run migration
python backend/migrations/runner.py
```

### Add Python Dependency

```bash
# Add to requirements.txt
pip install new-package

# Or
pip install new-package
pip freeze | grep new-package >> backend/requirements.txt

# Update environment
pip install -r backend/requirements.txt
```

### Add JavaScript Package

```bash
cd frontend
npm install new-package

# Or dev dependency
npm install --save-dev new-package
```

---

## CI/CD

### GitHub Actions

All tests run automatically on push/PR:

1. **Backend Tests** - Python 3.9, 3.10, 3.11
2. **Frontend Tests** - Node 16, 18, 20
3. **Code Quality** - Lint checks
4. **Docker Build** - Image build validation

**View results:** GitHub → Actions tab

### Local CI Check

```bash
# Replicate CI locally
make lint
make test

# Or specific
pytest backend/tests/ --cov=backend
npm test -- --coverage
```

---

## Deployment

### Docker Build

```bash
# Build images
docker-compose build

# Push to registry
docker tag backend:latest myregistry/backend:latest
docker push myregistry/backend:latest
```

### Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for full guide.

---

## Troubleshooting Development

### Port Already in Use

```bash
# Find process
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

### Database Lock

```bash
# Kill stuck connections
docker-compose exec postgres psql -U postgres -d llm_obs -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'llm_obs';"
```

### Memory Issues

```bash
# Check Docker stats
docker stats

# Increase Docker memory limit in preferences
```

### Dependency Conflicts

```bash
# Fresh install
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

---

## Resources

- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- SQLAlchemy: https://www.sqlalchemy.org/
- PostgreSQL: https://www.postgresql.org/docs/

---

**Last Updated:** 2026-06-11
