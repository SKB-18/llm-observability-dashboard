# API Documentation - LLM Observability Dashboard

Complete reference for all API endpoints.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints are currently unauthenticated. Optional: Pass API key as header:

```bash
X-API-Key: <your-api-key>
```

## Content Type

All requests and responses use `application/json`.

---

## Endpoints

### Health Check

**GET** `/health`

Check if backend service is running.

**Response:** 200 OK
```json
{
  "status": "healthy"
}
```

---

### Logging Endpoints

#### Log Single Completion

**POST** `/logs`

Ingest a single LLM completion log.

**Request:**
```json
{
  "prompt": "What is machine learning?",
  "response": "Machine learning is a subset of artificial intelligence...",
  "model": "claude-3-5-sonnet-20241022",
  "tokens_in": 25,
  "tokens_out": 150,
  "latency_ms": 425.3,
  "cost_usd": 0.0015,
  "user_id": "user123",
  "conversation_id": "conv_abc_12345"
}
```

**Field Descriptions:**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `prompt` | string | Yes | User input/question |
| `response` | string | Yes | LLM response |
| `model` | string | Yes | Model name (e.g., claude-3-5-sonnet) |
| `tokens_in` | integer | Yes | Input token count (>0) |
| `tokens_out` | integer | Yes | Output token count (>0) |
| `latency_ms` | float | Yes | Response time in milliseconds (>0) |
| `cost_usd` | float | Yes | Estimated cost in USD (≥0) |
| `user_id` | string | No | User identifier |
| `conversation_id` | string | No | Group related requests |

**Response:** 200 OK
```json
{
  "status": "logged",
  "log_id": 12345,
  "timestamp": "2026-06-11T12:30:00Z"
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/v1/logs \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is ML?",
    "response": "Machine learning...",
    "model": "gpt-4",
    "tokens_in": 10,
    "tokens_out": 50,
    "latency_ms": 500,
    "cost_usd": 0.001,
    "user_id": "user1"
  }'
```

---

#### Log Batch Completions

**POST** `/logs/batch`

Ingest multiple completions at once.

**Request:**
```json
{
  "logs": [
    {
      "prompt": "What is ML?",
      "response": "Machine learning is...",
      "model": "gpt-4",
      "tokens_in": 10,
      "tokens_out": 50,
      "latency_ms": 500,
      "cost_usd": 0.001
    },
    {
      "prompt": "Explain neural networks",
      "response": "Neural networks are...",
      "model": "claude-3-5-sonnet-20241022",
      "tokens_in": 15,
      "tokens_out": 75,
      "latency_ms": 450,
      "cost_usd": 0.0015
    }
  ]
}
```

**Response:** 200 OK
```json
{
  "status": "processed",
  "ingested_count": 2,
  "failed_count": 0,
  "errors": []
}
```

**Performance:**
- Batch size: 1-1000 items
- Throughput: ~1000 logs/second
- Typical batch time: <100ms

---

### Metrics Endpoints

#### Get Summary Metrics

**GET** `/metrics/summary`

Get overall dashboard metrics.

**Query Parameters:**
| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `start_date` | ISO 8601 | 30 days ago | Start of time range |
| `end_date` | ISO 8601 | Now | End of time range |
| `model` | string | - | Filter by model |
| `user_id` | string | - | Filter by user |

**Example:**
```bash
curl "http://localhost:8000/api/v1/metrics/summary?start_date=2026-06-01&model=gpt-4"
```

**Response:** 200 OK
```json
{
  "total_requests": 5247,
  "total_cost_usd": 12.45,
  "total_tokens": 880966,
  "avg_latency_ms": 425.3,
  "median_latency_ms": 380.0,
  "p95_latency_ms": 1200.5,
  "p99_latency_ms": 2500.0,
  "models": ["claude-3-5-sonnet", "gpt-4", "gpt-3.5-turbo"],
  "unique_users": 47,
  "success_rate_percent": 98.5,
  "error_rate_percent": 1.5
}
```

---

#### Get Metrics by Model

**GET** `/metrics/by-model`

Performance breakdown by model.

**Response:** 200 OK
```json
[
  {
    "model": "claude-3-5-sonnet-20241022",
    "request_count": 2100,
    "avg_latency_ms": 450.2,
    "median_latency_ms": 420.0,
    "p95_latency_ms": 1150.0,
    "total_cost_usd": 5.25,
    "success_rate_percent": 99.2,
    "avg_tokens_in": 750,
    "avg_tokens_out": 420
  },
  {
    "model": "gpt-4",
    "request_count": 1850,
    "avg_latency_ms": 380.5,
    "median_latency_ms": 350.0,
    "p95_latency_ms": 950.0,
    "total_cost_usd": 4.20,
    "success_rate_percent": 98.5,
    "avg_tokens_in": 700,
    "avg_tokens_out": 380
  }
]
```

---

#### Get Metrics by User

**GET** `/metrics/by-user`

Usage breakdown by user.

**Response:** 200 OK
```json
[
  {
    "user_id": "user_001",
    "request_count": 324,
    "total_cost_usd": 0.81,
    "total_tokens": 125400,
    "avg_latency_ms": 425.0
  },
  {
    "user_id": "user_002",
    "request_count": 287,
    "total_cost_usd": 0.72,
    "total_tokens": 112300,
    "avg_latency_ms": 418.5
  }
]
```

---

#### Get Latency Percentiles

**GET** `/metrics/latency-percentiles`

Latency distribution.

**Response:** 200 OK
```json
{
  "p50": 380.0,
  "p75": 650.0,
  "p90": 950.0,
  "p95": 1200.5,
  "p99": 2500.0,
  "min": 50.2,
  "max": 5234.1,
  "mean": 425.3,
  "stddev": 380.5
}
```

---

#### Get Cost Breakdown

**GET** `/metrics/cost-breakdown`

Cost analysis by model.

**Response:** 200 OK
```json
{
  "total_cost_usd": 12.45,
  "by_model": {
    "claude-3-5-sonnet-20241022": {
      "amount": 5.25,
      "percent": 42.1,
      "request_count": 2100
    },
    "gpt-4": {
      "amount": 4.20,
      "percent": 33.7,
      "request_count": 1850
    },
    "gpt-3.5-turbo": {
      "amount": 3.00,
      "percent": 24.1,
      "request_count": 1297
    }
  },
  "by_user": {
    "user_001": {
      "amount": 0.81,
      "percent": 6.5
    }
  }
}
```

---

### Evaluation Endpoints

#### Get Evaluation Results

**GET** `/evals`

Retrieve evaluation scores for completions.

**Query Parameters:**
| Parameter | Type | Notes |
|-----------|------|-------|
| `eval_type` | string | Filter by type: llm_judge, bleu, rouge |
| `min_score` | float | Minimum score (0-1) |
| `max_score` | float | Maximum score (0-1) |
| `limit` | integer | Results per page (default: 100) |
| `offset` | integer | Pagination offset (default: 0) |

**Response:** 200 OK
```json
{
  "total": 5247,
  "evals": [
    {
      "id": 1,
      "completion_id": 12345,
      "eval_type": "llm_judge",
      "score": 0.85,
      "criteria": "helpfulness, clarity",
      "explanation": "Response is clear and helpful...",
      "created_at": "2026-06-11T12:30:00Z"
    }
  ]
}
```

---

#### Post Evaluation Result

**POST** `/evals`

Submit evaluation score for a completion.

**Request:**
```json
{
  "completion_id": 12345,
  "eval_type": "llm_judge",
  "score": 0.85,
  "criteria": "helpfulness, accuracy",
  "explanation": "Response accurately answers the question..."
}
```

**Response:** 201 Created
```json
{
  "id": 1,
  "completion_id": 12345,
  "status": "recorded"
}
```

---

## Error Handling

All errors follow standard HTTP status codes:

| Code | Meaning | Example |
|------|---------|---------|
| 400 | Bad Request | Invalid JSON or missing required fields |
| 401 | Unauthorized | Invalid API key |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable | Validation failed (tokens > 0, etc.) |
| 500 | Server Error | Internal database error |

**Error Response Format:**
```json
{
  "error": "Invalid request",
  "detail": "Field 'tokens_in' must be > 0",
  "status": 400
}
```

---

## Rate Limiting

Currently no rate limits. In production:
- 1000 requests/minute per API key
- 10,000 requests/day per API key

---

## Examples

### Python Integration

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Log a single completion
completion = {
    "prompt": "What is ML?",
    "response": "Machine learning is...",
    "model": "gpt-4",
    "tokens_in": 10,
    "tokens_out": 50,
    "latency_ms": 500,
    "cost_usd": 0.001,
    "user_id": "user123"
}

response = requests.post(f"{BASE_URL}/logs", json=completion)
print(response.json())  # {"status": "logged", "log_id": 12345, ...}

# Get metrics
metrics = requests.get(f"{BASE_URL}/metrics/summary")
print(metrics.json())
```

### JavaScript Integration

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Log completion
async function logCompletion(data) {
  const response = await fetch(`${BASE_URL}/logs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return response.json();
}

// Get metrics
async function getMetrics() {
  const response = await fetch(`${BASE_URL}/metrics/summary`);
  return response.json();
}

// Usage
logCompletion({
  prompt: "What is ML?",
  response: "Machine learning is...",
  model: "gpt-4",
  tokens_in: 10,
  tokens_out: 50,
  latency_ms: 500,
  cost_usd: 0.001
});
```

---

## OpenAPI/Swagger

Full interactive documentation available at:
```
http://localhost:8000/docs
```

---

**Last Updated:** 2026-06-11
