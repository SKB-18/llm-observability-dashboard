"""
Tests for /api/v1/metrics/* endpoints.
Uses the shared in-memory SQLite DB from tests/conftest.py.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Completion
from tests.conftest import _Session

client = TestClient(app)

NOW = datetime(2024, 6, 11, 12, 0, 0)


def _make_completion(model="gpt-4", latency=400.0, cost=0.01, hour_offset=0):
    return Completion(
        prompt="Q",
        response="A",
        model=model,
        tokens_in=10,
        tokens_out=5,
        latency_ms=latency,
        cost_usd=cost,
        timestamp=NOW + timedelta(hours=hour_offset),
    )


@pytest.fixture(autouse=True)
def seed_db(reset_db):
    db = _Session()
    db.add_all([
        _make_completion("gpt-4",           latency=400,  cost=0.02, hour_offset=0),
        _make_completion("gpt-4",           latency=600,  cost=0.03, hour_offset=0),
        _make_completion("gpt-4",           latency=800,  cost=0.04, hour_offset=1),
        _make_completion("gpt-4",           latency=200,  cost=0.01, hour_offset=1),
        _make_completion("gpt-4",           latency=1000, cost=0.05, hour_offset=2),
        _make_completion("claude-3-5-sonnet", latency=300, cost=0.01, hour_offset=0),
        _make_completion("claude-3-5-sonnet", latency=500, cost=0.02, hour_offset=1),
        _make_completion("claude-3-5-sonnet", latency=700, cost=0.03, hour_offset=2),
    ])
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# /summary
# ---------------------------------------------------------------------------

def test_summary_default_dates():
    resp = client.get("/api/v1/metrics/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_requests"] == 8
    assert body["total_cost_usd"] > 0
    assert body["avg_latency_ms"] > 0
    assert set(body["models"]) == {"gpt-4", "claude-3-5-sonnet"}


def test_summary_date_range():
    start = NOW.isoformat()
    end = (NOW + timedelta(minutes=59)).isoformat()
    resp = client.get(f"/api/v1/metrics/summary?start_date={start}&end_date={end}")
    assert resp.status_code == 200
    assert resp.json()["total_requests"] == 3


def test_summary_empty_range():
    far_future = (NOW + timedelta(days=365)).isoformat()
    resp = client.get(f"/api/v1/metrics/summary?start_date={far_future}")
    assert resp.status_code == 200
    assert resp.json()["total_requests"] == 0


# ---------------------------------------------------------------------------
# /by-model
# ---------------------------------------------------------------------------

def test_by_model_sorted():
    resp = client.get("/api/v1/metrics/by-model")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["model"] == "gpt-4"
    assert body[0]["request_count"] == 5
    assert body[1]["model"] == "claude-3-5-sonnet"
    assert body[1]["request_count"] == 3


def test_by_model_has_percentiles():
    row = client.get("/api/v1/metrics/by-model").json()[0]
    for key in ("p50_latency_ms", "p95_latency_ms", "p99_latency_ms"):
        assert key in row
        assert row[key] >= 0


# ---------------------------------------------------------------------------
# /by-hour
# ---------------------------------------------------------------------------

def test_by_hour_sorted_asc():
    body = client.get("/api/v1/metrics/by-hour").json()
    assert len(body) == 3
    hours = [r["hour"] for r in body]
    assert hours == sorted(hours)


def test_by_hour_structure():
    for row in client.get("/api/v1/metrics/by-hour").json():
        for key in ("hour", "requests", "avg_cost_usd", "avg_latency_ms", "success_count"):
            assert key in row


# ---------------------------------------------------------------------------
# /latency-percentiles
# ---------------------------------------------------------------------------

def test_latency_percentiles_all_models():
    body = client.get("/api/v1/metrics/latency-percentiles").json()
    for key in ("p50", "p75", "p90", "p95", "p99", "min", "max"):
        assert key in body
        assert body[key] >= 0
    assert body["min"] <= body["p50"] <= body["p99"] <= body["max"]


def test_latency_percentiles_single_model():
    body = client.get("/api/v1/metrics/latency-percentiles?model=gpt-4").json()
    assert body["model"] == "gpt-4"
    assert body["min"] == 200.0
    assert body["max"] == 1000.0


def test_latency_percentiles_empty_range():
    far = (NOW + timedelta(days=365)).isoformat()
    body = client.get(f"/api/v1/metrics/latency-percentiles?start_date={far}").json()
    assert body["p50"] == 0


# ---------------------------------------------------------------------------
# /cost-breakdown
# ---------------------------------------------------------------------------

def test_cost_breakdown_total():
    body = client.get("/api/v1/metrics/cost-breakdown").json()
    assert "total_cost" in body
    assert "by_model" in body
    assert "by_hour" in body
    model_sum = sum(body["by_model"].values())
    assert abs(model_sum - body["total_cost"]) < 1e-5


def test_cost_breakdown_by_model_keys():
    body = client.get("/api/v1/metrics/cost-breakdown").json()
    assert "gpt-4" in body["by_model"]
    assert "claude-3-5-sonnet" in body["by_model"]
