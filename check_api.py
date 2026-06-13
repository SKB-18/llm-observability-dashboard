"""
API health-check script — tests all real backend routes with correct paths.
Run:  python check_api.py
Requires the backend to be running on http://localhost:8001.
"""
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8001/api/v1"
passed = failed = 0


def get(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=10) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code


def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code


def check(label, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  [PASS] {label}")
    else:
        failed += 1
        print(f"  [FAIL] {label}  →  {detail}")


print("=== /logs ===")
d, c = get("/logs?page=1&limit=5")
check("GET /logs pagination", c == 200 and d["total"] > 10000, d)
check("GET /logs has items", len(d.get("items", [])) > 0)

d, c = get("/logs?source=lmsys&page=1&limit=1")
check("GET /logs?source=lmsys", c == 200 and d["total"] >= 10000)

d, c = get("/logs?source=evals_benchmark&page=1&limit=1")
check("GET /logs?source=evals_benchmark", c == 200 and d["total"] == 1000)

d, c = post("/logs", {
    "prompt": "test", "response": "ok", "model": "gpt-4",
    "tokens_in": 5, "tokens_out": 2, "latency_ms": 100.0, "cost_usd": 0.001
})
check("POST /logs single", c == 201 and "log_id" in d)

print("\n=== /metrics ===")
d, c = get("/metrics/summary")
check("GET /metrics/summary requests", c == 200 and d.get("total_requests", 0) > 10000)
check("GET /metrics/summary cost > 0", d.get("total_cost_usd", 0) > 0,
      f"total_cost_usd={d.get('total_cost_usd')}")
check("GET /metrics/summary latency > 0", d.get("avg_latency_ms", 0) > 0)

d, c = get("/metrics/by-model")
check("GET /metrics/by-model not empty", c == 200 and len(d) > 0, f"got {len(d)} models")
check("GET /metrics/by-model has fields",
      all(k in d[0] for k in ["model", "request_count", "avg_latency_ms"]) if d else False)

d, c = get("/metrics/latency-percentiles")
check("GET /metrics/latency-percentiles p50", c == 200 and d.get("p50") is not None, d)
check("GET /metrics/latency-percentiles p99", d.get("p99") is not None)

d, c = get("/metrics/cost-breakdown")
check("GET /metrics/cost-breakdown total > 0", c == 200 and d.get("total_cost", 0) > 0)
check("GET /metrics/cost-breakdown by_model", isinstance(d.get("by_model"), dict) and len(d["by_model"]) > 0)

d, c = get("/metrics/model-comparison")
check("GET /metrics/model-comparison battles", c == 200 and d.get("total_battles", 0) > 0)
check("GET /metrics/model-comparison models", len(d.get("models", [])) > 0)
if d.get("models"):
    m = d["models"][0]
    check("GET /metrics/model-comparison fields",
          all(k in m for k in ["model", "win_rate", "win_tie_rate_pct", "battles"]))

d, c = get("/metrics/evals")
check("GET /metrics/evals total", c == 200 and d.get("total_evals", 0) > 0)
check("GET /metrics/evals avg_score", d.get("overall_avg_score", 0) > 0,
      f"avg={d.get('overall_avg_score')}")
check("GET /metrics/evals by_type", len(d.get("by_type", [])) > 0)
check("GET /metrics/evals win_rates", len(d.get("win_rates", [])) > 0)

d, c = get("/metrics/eval-summary")
check("GET /metrics/eval-summary has lmsys", c == 200 and "lmsys" in d)
check("GET /metrics/eval-summary has evals_benchmark", "evals_benchmark" in d)
qs = d.get("evals_benchmark", {}).get("quality_scores", {})
check("GET /metrics/eval-summary quality_scores", len(qs) > 0)

d, c = get("/metrics/by-hour")
check("GET /metrics/by-hour not empty", c == 200 and len(d) > 0, f"got {len(d)} hours")

print("\n=== /evals ===")
d, c = post("/evals/batch", {"completion_ids": [1, 2, 3]})
check("POST /evals/batch", c == 202 and d.get("submitted_count") == 3, d)

print(f"\n{'=' * 40}")
total = passed + failed
print(f"RESULT: {passed}/{total} passed  {failed} failed")
if failed == 0:
    print("All endpoints healthy [OK]")
