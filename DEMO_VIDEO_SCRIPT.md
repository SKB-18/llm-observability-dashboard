# Demo Video Script

## LLM Observability Dashboard — 3-minute walkthrough

---

### Scene 1: Cold start (0:00 – 0:20)

**Narration:**
"Let's spin up the entire stack with a single command."

```bash
docker-compose up -d        # starts PostgreSQL + backend + frontend
python backend/seed_data.py # loads 5 000 LLM completion logs
```

Open browser → `http://localhost:5173`

---

### Scene 2: Dashboard overview (0:20 – 0:50)

**Show:** The live dashboard loading.

**Point out:**
- Six metric cards: Total Requests, Total Cost (USD), Avg Latency, Quality Score, Success Rate, Active Models
- The "Live" green dot in the header — auto-refreshes every 30 seconds
- Charts: Request Volume (hourly), Cost Over Time, Latency Percentiles, Quality Scores

**Narration:**
"We can see 5 000 requests across four different models over the last week. Cost sits at $12.40, average latency around 320 ms."

---

### Scene 3: Filtering (0:50 – 1:20)

**Action:** Click the Filters bar → expand.

- Set date range to last 24 hours
- Select only `gpt-4` and `claude-3-5-sonnet`
- Click **Apply Filters**

**Show:** Charts and cards update instantly.

**Narration:**
"Filters propagate to every chart and card simultaneously — no page reload, no stale data."

---

### Scene 4: Model comparison (1:20 – 1:50)

**Show:** Scroll down to Model Comparison table.

**Point out:**
- `claude-3-5-sonnet` highlighted as cheapest (green badge)
- `gpt-4` highlighted as fastest (⚡ badge)
- Toggle chart between Latency / Cost / Requests

**Narration:**
"The comparison table makes it easy to see which model gives you the best cost–performance trade-off for your use case."

---

### Scene 5: SDK usage (1:50 – 2:20)

**Show:** Terminal window with the demo script.

```bash
cd examples && python demo.py
```

**Code shown:**
```python
from sdk.llm_observer import LLMObserver
import anthropic

obs = LLMObserver(collector_url="http://localhost:8000")
client = anthropic.Anthropic()
obs.wrap_claude_client(client)

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Explain quantum entanglement."}],
    max_tokens=200,
)
print(response.content[0].text)
```

Switch back to browser → refresh → new request appears in the dashboard.

**Narration:**
"Two lines of code — `LLMObserver` + `wrap_claude_client` — and every API call is automatically logged, with zero impact on response latency."

---

### Scene 6: Evaluations (2:20 – 2:50)

**Show:** Postman / curl hitting the eval endpoint.

```bash
curl -s -X POST http://localhost:8000/api/v1/evals/evaluate \
  -H "Content-Type: application/json" \
  -d '{"completion_id": 42, "eval_types": ["bleu", "rouge"]}'
```

Response:
```json
{
  "completion_id": 42,
  "scores": { "bleu": 0.81, "rouge": 0.79 },
  "explanation": "High lexical overlap with reference.",
  "timestamp": "2024-06-11T14:32:00Z"
}
```

**Narration:**
"The evaluation engine supports BLEU, ROUGE, semantic similarity, and LLM-as-judge scoring — all via a single API call."

---

### Scene 7: Wrap-up (2:50 – 3:00)

**Show:** Repository structure briefly.

**Narration:**
"165 tests passing, Docker Compose for one-command setup, full API documentation at `/docs`.
The stack is production-ready — swap SQLite for Postgres and set your `ANTHROPIC_API_KEY` and you're live."

---

## Key talking points

| Feature | Highlight |
|---------|-----------|
| Ingestion | Single + batch endpoints, up to 1 000 rows/request |
| Auto-logging SDK | `wrap_claude_client` — zero-change integration |
| Evaluations | BLEU / ROUGE / LLM judge / rule engine |
| Metrics | 5 endpoints, all filterable by date + model |
| Performance | <500 ms queries on 5 000-row dataset |
| Tests | 165 tests, all passing |
| DevOps | Docker Compose, GitHub Actions CI/CD |
