"""
Full-stack API integration tests.

Each test follows the same pattern:
  1. Insert data via POST endpoints
  2. Read it back via GET endpoints
  3. Assert the round-trip is consistent

All tests share the single in-memory SQLite engine from conftest.py.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Completion
from tests.conftest import _Session

client = TestClient(app)

_BASE = dict(
    prompt="What is 2+2?",
    response="4",
    model="gpt-4",
    tokens_in=10,
    tokens_out=5,
    latency_ms=200.0,
    cost_usd=0.002,
)


@pytest.fixture(autouse=True)
def clean(reset_db):
    pass


# ---------------------------------------------------------------------------
# A. Complete workflow: POST → GET metrics/summary
# ---------------------------------------------------------------------------

def test_complete_workflow():
    """Ingest a single log then verify it appears in the summary."""
    r = client.post("/api/v1/logs", json=_BASE)
    assert r.status_code == 201
    log_id = r.json()["log_id"]

    summary = client.get("/api/v1/metrics/summary").json()
    assert summary["total_requests"] >= 1

    # Retrieve the specific log
    get_r = client.get(f"/api/v1/logs/{log_id}")
    assert get_r.status_code == 200
    assert get_r.json()["model"] == "gpt-4"


# ---------------------------------------------------------------------------
# B. Batch then query by model
# ---------------------------------------------------------------------------

def test_batch_then_query():
    """POST 100 logs split across two models, verify by-model breakdown."""
    claude_log = {**_BASE, "model": "claude-3-5-sonnet", "cost_usd": 0.003}
    gpt_log    = {**_BASE, "model": "gpt-4",             "cost_usd": 0.005}

    batch = [claude_log] * 60 + [gpt_log] * 40
    r = client.post("/api/v1/logs/batch", json=batch)
    assert r.status_code == 200
    assert r.json()["ingested_count"] == 100

    by_model = client.get("/api/v1/metrics/by-model").json()
    counts = {row["model"]: row["request_count"] for row in by_model}
    assert counts.get("claude-3-5-sonnet") == 60
    assert counts.get("gpt-4") == 40

    # Sorted DESC
    assert by_model[0]["request_count"] >= by_model[-1]["request_count"]


# ---------------------------------------------------------------------------
# C. Date filter
# ---------------------------------------------------------------------------

def test_filters_work():
    """Logs with different timestamps – only those in range should appear."""
    db = _Session()
    now = datetime(2024, 6, 11, 12, 0, 0)

    # 5 in-range (hour 12) and 5 out-of-range (hour 23)
    for h in [12] * 5 + [23] * 5:
        db.add(Completion(
            **{k: v for k, v in _BASE.items() if k != "cost_usd"},
            cost_usd=0.001,
            timestamp=now.replace(hour=h),
        ))
    db.commit()
    db.close()

    start = now.replace(hour=11).isoformat()
    end   = now.replace(hour=13).isoformat()

    summary = client.get(f"/api/v1/metrics/summary?start_date={start}&end_date={end}").json()
    assert summary["total_requests"] == 5


# ---------------------------------------------------------------------------
# D. Model filtering on latency percentiles
# ---------------------------------------------------------------------------

def test_model_filtering():
    """POST logs for two models; latency-percentiles filtered by model should
    only reflect that model's data."""
    db = _Session()
    for lat in [100, 200, 300]:
        db.add(Completion(**{**_BASE, "model": "claude-3-5-sonnet", "latency_ms": lat}))
    for lat in [1000, 2000, 3000]:
        db.add(Completion(**{**_BASE, "model": "gpt-4", "latency_ms": lat}))
    db.commit()
    db.close()

    claude_p = client.get("/api/v1/metrics/latency-percentiles?model=claude-3-5-sonnet").json()
    gpt_p    = client.get("/api/v1/metrics/latency-percentiles?model=gpt-4").json()

    assert claude_p["max"] <= 300.0
    assert gpt_p["min"]  >= 1000.0


# ---------------------------------------------------------------------------
# E. Cost calculation
# ---------------------------------------------------------------------------

def test_cost_calculation():
    """Known per-model costs must sum correctly in the breakdown."""
    db = _Session()
    for _ in range(5):
        db.add(Completion(**{**_BASE, "model": "gpt-4",           "cost_usd": 0.01}))
    for _ in range(5):
        db.add(Completion(**{**_BASE, "model": "claude-3-5-sonnet", "cost_usd": 0.005}))
    db.commit()
    db.close()

    breakdown = client.get("/api/v1/metrics/cost-breakdown").json()
    assert abs(breakdown["total_cost"] - 0.075) < 1e-5
    assert abs(breakdown["by_model"]["gpt-4"]           - 0.05)  < 1e-5
    assert abs(breakdown["by_model"]["claude-3-5-sonnet"] - 0.025) < 1e-5


# ---------------------------------------------------------------------------
# F. Pagination / large dataset summary consistency
# ---------------------------------------------------------------------------

def test_summary_counts_match_by_model_total():
    """summary.total_requests must equal the sum of all by-model request_counts."""
    batch = [{**_BASE, "model": ["gpt-4", "claude-3-5-sonnet", "gpt-3.5-turbo"][i % 3]}
             for i in range(90)]
    r = client.post("/api/v1/logs/batch", json=batch)
    assert r.json()["ingested_count"] == 90

    summary  = client.get("/api/v1/metrics/summary").json()
    by_model = client.get("/api/v1/metrics/by-model").json()

    model_total = sum(row["request_count"] for row in by_model)
    assert summary["total_requests"] == model_total == 90
