"""
Tests for Redis cache layer and OpenTelemetry setup.
Cache tests use a fake Redis via unittest.mock; OTEL tests verify
the tracer is returned and telemetry setup runs without errors.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ---------------------------------------------------------------------------
# Cache tests (Redis mocked)
# ---------------------------------------------------------------------------

def _make_mock_redis(get_return=None, ping_ok=True):
    """Return a mock Redis client."""
    m = MagicMock()
    m.ping.return_value = True if ping_ok else (_ for _ in ()).throw(Exception("down"))
    m.get.return_value = json.dumps(get_return) if get_return is not None else None
    m.setex.return_value = True
    m.delete.return_value = 1
    m.keys.return_value = []
    return m


def test_cache_get_miss():
    import backend.cache as cache_mod
    cache_mod.reset_client()
    mock_r = _make_mock_redis(get_return=None)
    with patch("backend.cache._get_client", return_value=mock_r):
        result = cache_mod.cache_get("missing:key")
    assert result is None


def test_cache_get_hit():
    import backend.cache as cache_mod
    cache_mod.reset_client()
    mock_r = _make_mock_redis(get_return={"total": 42})
    with patch("backend.cache._get_client", return_value=mock_r):
        result = cache_mod.cache_get("metrics:summary:None:None")
    assert result == {"total": 42}


def test_cache_set():
    import backend.cache as cache_mod
    mock_r = _make_mock_redis()
    with patch("backend.cache._get_client", return_value=mock_r):
        cache_mod.cache_set("some:key", {"x": 1}, ttl=30)
    mock_r.setex.assert_called_once_with("some:key", 30, json.dumps({"x": 1}))


def test_cache_delete():
    import backend.cache as cache_mod
    mock_r = _make_mock_redis()
    with patch("backend.cache._get_client", return_value=mock_r):
        cache_mod.cache_delete("some:key")
    mock_r.delete.assert_called_once_with("some:key")


def test_invalidate_prefix_no_keys():
    import backend.cache as cache_mod
    mock_r = _make_mock_redis()
    mock_r.keys.return_value = []
    with patch("backend.cache._get_client", return_value=mock_r):
        count = cache_mod.invalidate_prefix("metrics")
    assert count == 0


def test_invalidate_prefix_with_keys():
    import backend.cache as cache_mod
    mock_r = _make_mock_redis()
    mock_r.keys.return_value = ["metrics:summary:None:None", "metrics:summary:a:b"]
    mock_r.delete.return_value = 2
    with patch("backend.cache._get_client", return_value=mock_r):
        count = cache_mod.invalidate_prefix("metrics")
    assert count == 2


def test_cache_get_returns_none_when_no_client():
    import backend.cache as cache_mod
    with patch("backend.cache._get_client", return_value=None):
        assert cache_mod.cache_get("k") is None


def test_cache_set_noop_when_no_client():
    import backend.cache as cache_mod
    with patch("backend.cache._get_client", return_value=None):
        cache_mod.cache_set("k", "v")  # should not raise


def test_cache_delete_noop_when_no_client():
    import backend.cache as cache_mod
    with patch("backend.cache._get_client", return_value=None):
        cache_mod.cache_delete("k")  # should not raise


def test_invalidate_prefix_noop_when_no_client():
    import backend.cache as cache_mod
    with patch("backend.cache._get_client", return_value=None):
        assert cache_mod.invalidate_prefix("x") == 0


def test_reset_client():
    import backend.cache as cache_mod
    cache_mod._redis_client = MagicMock()
    cache_mod.reset_client()
    assert cache_mod._redis_client is None


# ---------------------------------------------------------------------------
# Metrics endpoint uses cache
# ---------------------------------------------------------------------------

def test_summary_endpoint_cache_hit(reset_db):
    """When cache returns data, DB is not queried."""
    from fastapi.testclient import TestClient
    from backend.main import app
    cached_data = {"total_requests": 999, "cached": True}
    with patch("backend.routes.metrics.cache_get", return_value=cached_data):
        with patch("backend.routes.metrics.query_summary") as mock_qs:
            client = TestClient(app)
            resp = client.get("/api/v1/metrics/summary")
    assert resp.status_code == 200
    assert resp.json()["total_requests"] == 999
    mock_qs.assert_not_called()


def test_summary_endpoint_cache_miss_stores(reset_db):
    """On cache miss, result is stored in cache."""
    from fastapi.testclient import TestClient
    from backend.main import app
    with patch("backend.routes.metrics.cache_get", return_value=None):
        with patch("backend.routes.metrics.cache_set") as mock_cs:
            client = TestClient(app)
            resp = client.get("/api/v1/metrics/summary")
    assert resp.status_code == 200
    mock_cs.assert_called_once()


# ---------------------------------------------------------------------------
# OpenTelemetry setup
# ---------------------------------------------------------------------------

def test_get_tracer_returns_object():
    from backend.telemetry import get_tracer
    tracer = get_tracer()
    assert tracer is not None


def test_setup_telemetry_no_app():
    from backend.telemetry import setup_telemetry
    setup_telemetry(app=None)  # should not raise


def test_setup_telemetry_with_app():
    from backend.telemetry import setup_telemetry
    from fastapi import FastAPI
    dummy_app = FastAPI()
    setup_telemetry(app=dummy_app)  # should not raise
