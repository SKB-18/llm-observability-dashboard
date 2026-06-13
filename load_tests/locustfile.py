"""
Locust load test for the LLM Observability Dashboard API.

Run:
    locust -f load_tests/locustfile.py --host=http://localhost:8001

Web UI:  http://localhost:8089
Headless: locust -f load_tests/locustfile.py --host=http://localhost:8001 \
              --headless -u 50 -r 10 --run-time 60s
"""
from __future__ import annotations

import random
import string

from locust import HttpUser, task, between, events


def _rand_str(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=n))


class MetricsUser(HttpUser):
    """
    Simulates a dashboard user polling analytics endpoints.
    Weight 3 – the most common access pattern.
    """
    weight = 3
    wait_time = between(0.5, 2.0)

    @task(5)
    def get_summary(self):
        self.client.get("/api/v1/metrics/summary", name="/api/v1/metrics/summary")

    @task(3)
    def get_by_model(self):
        self.client.get("/api/v1/metrics/by-model", name="/api/v1/metrics/by-model")

    @task(3)
    def get_by_hour(self):
        self.client.get("/api/v1/metrics/by-hour", name="/api/v1/metrics/by-hour")

    @task(2)
    def get_latency_percentiles(self):
        self.client.get("/api/v1/metrics/latency-percentiles", name="/api/v1/metrics/latency-percentiles")

    @task(2)
    def get_cost_breakdown(self):
        self.client.get("/api/v1/metrics/cost-breakdown", name="/api/v1/metrics/cost-breakdown")

    @task(2)
    def get_evals(self):
        self.client.get("/api/v1/metrics/evals", name="/api/v1/metrics/evals")

    @task(1)
    def get_model_comparison(self):
        self.client.get("/api/v1/metrics/model-comparison", name="/api/v1/metrics/model-comparison")

    @task(1)
    def get_eval_summary(self):
        self.client.get("/api/v1/metrics/eval-summary", name="/api/v1/metrics/eval-summary")

    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")


class LogIngestionUser(HttpUser):
    """
    Simulates SDK clients writing completions.
    Weight 1 – less frequent than reads.
    """
    weight = 1
    wait_time = between(0.2, 1.0)

    MODELS = ["gpt-4", "gpt-3.5-turbo", "claude-3-5-sonnet", "claude-3-opus"]

    @task(4)
    def log_completion(self):
        payload = {
            "prompt": f"What is {_rand_str(6)}?",
            "response": f"It is {_rand_str(12)}.",
            "model": random.choice(self.MODELS),
            "tokens_in": random.randint(5, 200),
            "tokens_out": random.randint(10, 500),
            "latency_ms": random.uniform(50, 3000),
            "cost_usd": round(random.uniform(0.0001, 0.05), 6),
        }
        self.client.post("/api/v1/logs", json=payload, name="/api/v1/logs")

    @task(1)
    def log_batch(self):
        batch = [
            {
                "prompt": f"Q{i}: {_rand_str(5)}?",
                "response": f"A{i}: {_rand_str(10)}.",
                "model": random.choice(self.MODELS),
                "tokens_in": random.randint(5, 100),
                "tokens_out": random.randint(10, 300),
                "latency_ms": random.uniform(50, 2000),
                "cost_usd": round(random.uniform(0.0001, 0.02), 6),
            }
            for i in range(random.randint(2, 10))
        ]
        self.client.post("/api/v1/logs/batch", json=batch, name="/api/v1/logs/batch")

    @task(1)
    def get_logs(self):
        self.client.get("/api/v1/logs?limit=20", name="/api/v1/logs")


class EvalUser(HttpUser):
    """
    Simulates eval pipeline reads.
    Weight 1.
    """
    weight = 1
    wait_time = between(1.0, 3.0)

    @task(3)
    def list_evals(self):
        self.client.get("/api/v1/evals?limit=50", name="/api/v1/evals")

    @task(1)
    def list_uploads(self):
        self.client.get("/api/v1/upload/datasets", name="/api/v1/upload/datasets")


# ---------------------------------------------------------------------------
# Summary hook – prints P99 latency at end of run
# ---------------------------------------------------------------------------
@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    stats = environment.runner.stats
    total = stats.total
    print("\n=== Load Test Summary ===")
    print(f"  Requests:  {total.num_requests}")
    print(f"  Failures:  {total.num_failures} ({100*total.fail_ratio:.1f}%)")
    print(f"  RPS:       {total.current_rps:.1f}")
    print(f"  P50:       {total.get_response_time_percentile(0.5):.0f} ms")
    print(f"  P95:       {total.get_response_time_percentile(0.95):.0f} ms")
    print(f"  P99:       {total.get_response_time_percentile(0.99):.0f} ms")
    if total.fail_ratio > 0.01:
        print("  WARN: failure rate > 1%")
