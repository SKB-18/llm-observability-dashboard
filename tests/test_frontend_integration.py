"""
Frontend integration tests (Python side).

These test the contract between the backend API and what the frontend
expects to receive – i.e. shape/type checks on every response the
React components will consume.  No browser required.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Completion
from tests.conftest import _Session

client = TestClient(app)

NOW = datetime(2024, 6, 11, 12, 0, 0)

_LOG = dict(
    prompt="Q", response="A", model="claude-3-5-sonnet",
    tokens_in=10, tokens_out=5, latency_ms=200.0, cost_usd=0.003,
)


@pytest.fixture(autouse=True)
def seed(reset_db):
    db = _Session()
    models = ["gpt-4", "claude-3-5-sonnet", "gpt-3.5-turbo"]
    _EXCLUDE = {"model", "cost_usd", "latency_ms"}
    db.add_all([
        Completion(
            **{k: v for k, v in _LOG.items() if k not in _EXCLUDE},
            model=models[i % 3],
            cost_usd=0.001 * (i % 5 + 1),
            latency_ms=100 + i * 10,
            timestamp=NOW + timedelta(hours=i % 3),
        )
        for i in range(30)
    ])
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Dashboard loads – all required summary fields present
# ---------------------------------------------------------------------------

def test_dashboard_summary_shape():
    """Frontend MetricsCards need these exact keys."""
    body = client.get("/api/v1/metrics/summary").json()
    for key in ("total_requests", "total_cost_usd", "avg_latency_ms",
                "models", "success_rate_percent", "unique_users"):
        assert key in body, f"Missing key: {key}"
    assert isinstance(body["models"], list)
    assert body["total_requests"] == 30


# ---------------------------------------------------------------------------
# Charts data shapes
# ---------------------------------------------------------------------------

def test_cost_chart_data_shape():
    """CostChart expects hour + avg_cost_usd fields."""
    rows = client.get("/api/v1/metrics/by-hour").json()
    assert len(rows) > 0
    for row in rows:
        assert "hour" in row
        assert "avg_cost_usd" in row
        assert "requests" in row
        assert row["requests"] >= 0
        assert row["avg_cost_usd"] >= 0


def test_latency_chart_data_shape():
    """LatencyChart expects p50/p95/p99 fields from latency-percentiles."""
    body = client.get("/api/v1/metrics/latency-percentiles").json()
    for key in ("p50", "p75", "p90", "p95", "p99", "min", "max"):
        assert key in body
        assert isinstance(body[key], (int, float))


def test_model_comparison_data_shape():
    """ModelComparison table needs these fields per row."""
    rows = client.get("/api/v1/metrics/by-model").json()
    assert len(rows) == 3  # seeded 3 models
    for row in rows:
        for key in ("model", "request_count", "avg_latency_ms",
                    "total_cost_usd", "avg_tokens_in", "avg_tokens_out"):
            assert key in row, f"Missing key {key} in row {row}"


# ---------------------------------------------------------------------------
# Filters update the charts
# ---------------------------------------------------------------------------

def test_filter_applies_date_range():
    """Restricting to the first hour should return ~10 rows (30 ÷ 3 hours)."""
    start = NOW.isoformat()
    end   = (NOW + timedelta(minutes=59)).isoformat()
    body = client.get(
        f"/api/v1/metrics/summary?start_date={start}&end_date={end}"
    ).json()
    # Seeded 10 rows at hour 0
    assert body["total_requests"] == 10


def test_filter_by_model():
    """Latency percentiles filtered to one model should only reflect that model."""
    body = client.get("/api/v1/metrics/latency-percentiles?model=gpt-4").json()
    assert body["model"] == "gpt-4"
    assert body["min"] > 0


def test_empty_filter_range():
    """Future date range → zero requests, empty model list."""
    future = (NOW + timedelta(days=365)).isoformat()
    body = client.get(f"/api/v1/metrics/summary?start_date={future}").json()
    assert body["total_requests"] == 0
    assert body["models"] == []


# ---------------------------------------------------------------------------
# Cost breakdown matches what the frontend renders
# ---------------------------------------------------------------------------

def test_cost_breakdown_shape():
    body = client.get("/api/v1/metrics/cost-breakdown").json()
    assert "total_cost" in body
    assert "by_model" in body
    assert "by_hour" in body
    assert isinstance(body["by_model"], dict)
    assert isinstance(body["by_hour"], list)

    # Model keys match those in by-model
    by_model_keys = {r["model"] for r in client.get("/api/v1/metrics/by-model").json()}
    assert set(body["by_model"].keys()) == by_model_keys


# ---------------------------------------------------------------------------
# Health check (frontend ping)
# ---------------------------------------------------------------------------

def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_request_id_header_present():
    """Frontend uses X-Request-Id for correlating errors."""
    r = client.get("/health")
    assert "x-request-id" in r.headers
    assert len(r.headers["x-request-id"]) == 36   # UUID4 length
