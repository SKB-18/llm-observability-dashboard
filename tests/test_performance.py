"""
Performance / stress tests.

Timing assertions use wall-clock time against an in-memory SQLite DB.
SQLite is slower than PostgreSQL, so thresholds are intentionally generous
(5 s for 1 000-row batch, 2 s for queries over 5 000 rows).

Run verbosely to see timings:
    pytest tests/test_performance.py -v -s
"""
from __future__ import annotations

import concurrent.futures
import time
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Completion
from tests.conftest import _Session

client = TestClient(app, raise_server_exceptions=False)

_BASE = dict(
    prompt="Perf test prompt",
    response="Perf test response",
    model="gpt-4",
    tokens_in=20,
    tokens_out=10,
    latency_ms=250.0,
    cost_usd=0.003,
)

NOW = datetime(2024, 6, 11, 12, 0, 0)


@pytest.fixture(autouse=True)
def clean(reset_db):
    pass


def _seed(n: int, model_cycle: list[str] | None = None):
    """Insert n Completion rows directly (bypasses HTTP for speed)."""
    models = model_cycle or ["gpt-4"]
    db = _Session()
    _EXCLUDE = {"model", "cost_usd", "latency_ms"}
    db.add_all([
        Completion(
            **{k: v for k, v in _BASE.items() if k not in _EXCLUDE},
            model=models[i % len(models)],
            cost_usd=0.001 + (i % 5) * 0.001,
            latency_ms=100 + (i % 10) * 50,
            timestamp=NOW + timedelta(minutes=i),
        )
        for i in range(n)
    ])
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# A. 1 000-row batch via HTTP in < 5 s
# ---------------------------------------------------------------------------

def test_batch_1000_logs():
    batch = [_BASE.copy() for _ in range(1000)]

    t0 = time.perf_counter()
    r = client.post("/api/v1/logs/batch", json=batch)
    elapsed = time.perf_counter() - t0

    assert r.status_code == 200
    assert r.json()["ingested_count"] == 1000
    print(f"\n  batch 1000 logs → {elapsed:.2f} s")
    assert elapsed < 5.0, f"Batch insert took {elapsed:.2f} s (limit 5 s)"


# ---------------------------------------------------------------------------
# B. Query speed over 5 000 rows
# ---------------------------------------------------------------------------

def test_query_summary_speed():
    _seed(5000, model_cycle=["gpt-4", "claude-3-5-sonnet", "gpt-3.5-turbo"])

    t0 = time.perf_counter()
    r = client.get("/api/v1/metrics/summary")
    elapsed = time.perf_counter() - t0

    assert r.status_code == 200
    assert r.json()["total_requests"] == 5000
    print(f"\n  /summary (5 000 rows) → {elapsed * 1000:.0f} ms")
    assert elapsed < 2.0, f"/summary took {elapsed:.2f} s (limit 2 s)"


def test_query_by_model_speed():
    _seed(5000, model_cycle=["gpt-4", "claude-3-5-sonnet", "gpt-3.5-turbo"])

    t0 = time.perf_counter()
    r = client.get("/api/v1/metrics/by-model")
    elapsed = time.perf_counter() - t0

    assert r.status_code == 200
    assert len(r.json()) == 3
    print(f"\n  /by-model (5 000 rows) → {elapsed * 1000:.0f} ms")
    assert elapsed < 2.0


def test_query_by_hour_speed():
    _seed(5000, model_cycle=["gpt-4"])

    t0 = time.perf_counter()
    r = client.get("/api/v1/metrics/by-hour")
    elapsed = time.perf_counter() - t0

    assert r.status_code == 200
    print(f"\n  /by-hour (5 000 rows) → {elapsed * 1000:.0f} ms")
    assert elapsed < 2.0


def test_query_latency_percentiles_speed():
    _seed(5000)

    t0 = time.perf_counter()
    r = client.get("/api/v1/metrics/latency-percentiles")
    elapsed = time.perf_counter() - t0

    assert r.status_code == 200
    body = r.json()
    assert body["min"] > 0
    assert body["p99"] >= body["p50"]
    print(f"\n  /latency-percentiles (5 000 rows) → {elapsed * 1000:.0f} ms")
    assert elapsed < 2.0


# ---------------------------------------------------------------------------
# C. Concurrent POST requests – consistency check
# ---------------------------------------------------------------------------

def test_concurrent_requests_consistency():
    """100 parallel POST /api/v1/logs – server must stay responsive under load.

    SQLite StaticPool shares one connection across threads so concurrent commits
    are unreliable by design. We only assert that every request received *some*
    response (201 or 500) and that the summary endpoint still works afterwards.
    """
    def post_one(_):
        return client.post("/api/v1/logs", json=_BASE)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        futures = [pool.submit(post_one, i) for i in range(100)]
        results = [f.result() for f in futures]

    got_response = sum(1 for r in results if r.status_code in (201, 500))
    assert got_response == 100, "Some requests hung or crashed"

    summary = client.get("/api/v1/metrics/summary")
    assert summary.status_code == 200
    print(f"\n  concurrent 100 POSTs → {got_response} got responses, DB={summary.json()['total_requests']}")


# ---------------------------------------------------------------------------
# D. Batch size boundary
# ---------------------------------------------------------------------------

def test_batch_exactly_1000_accepted():
    batch = [_BASE.copy() for _ in range(1000)]
    r = client.post("/api/v1/logs/batch", json=batch)
    assert r.status_code == 200
    assert r.json()["ingested_count"] == 1000


def test_batch_1001_rejected():
    batch = [_BASE.copy() for _ in range(1001)]
    r = client.post("/api/v1/logs/batch", json=batch)
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# E. Percentile correctness on known data
# ---------------------------------------------------------------------------

def test_percentile_correctness():
    """Insert 100 rows with latency = 1..100. p50 should be ~50, p99 ~99."""
    db = _Session()
    db.add_all([
        Completion(**{**_BASE, "latency_ms": float(i)})
        for i in range(1, 101)
    ])
    db.commit()
    db.close()

    body = client.get("/api/v1/metrics/latency-percentiles").json()
    assert body["min"] == 1.0
    assert body["max"] == 100.0
    assert 45 <= body["p50"] <= 55
    assert body["p95"] >= 90
    assert body["p99"] >= 97
