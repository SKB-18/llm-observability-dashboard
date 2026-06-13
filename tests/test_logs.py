"""
Integration tests for /api/v1/logs endpoints.
Uses the shared in-memory SQLite DB from tests/conftest.py.
"""
import concurrent.futures
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app, raise_server_exceptions=False)

VALID_PAYLOAD = {
    "prompt": "Hello",
    "response": "Hi there!",
    "model": "claude-sonnet-4-6",
    "tokens_in": 5,
    "tokens_out": 10,
    "latency_ms": 250.0,
    "cost_usd": 0.0001,
}


@pytest.fixture(autouse=True)
def clean_db(reset_db):
    """Delegate to the shared reset_db fixture from conftest."""


# ---------------------------------------------------------------------------
# POST /api/v1/logs
# ---------------------------------------------------------------------------

def test_valid_log_ingestion():
    resp = client.post("/api/v1/logs", json=VALID_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "logged"
    assert "log_id" in body
    assert "timestamp" in body


def test_invalid_tokens():
    resp = client.post("/api/v1/logs", json={**VALID_PAYLOAD, "tokens_in": 0})
    assert resp.status_code == 422


def test_invalid_negative_latency():
    resp = client.post("/api/v1/logs", json={**VALID_PAYLOAD, "latency_ms": -1.0})
    assert resp.status_code == 422


def test_negative_cost_rejected():
    resp = client.post("/api/v1/logs", json={**VALID_PAYLOAD, "cost_usd": -0.5})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/logs/batch
# ---------------------------------------------------------------------------

def test_batch_ingestion():
    logs = [VALID_PAYLOAD.copy() for _ in range(100)]
    resp = client.post("/api/v1/logs/batch", json=logs)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ingested_count"] == 100
    assert body["failed_count"] == 0


def test_batch_partial_failure():
    from tests.conftest import _Session
    from backend.utils.db import batch_insert_completions
    from backend.schemas import CompletionLog

    good = [CompletionLog(**VALID_PAYLOAD) for _ in range(95)]
    db = _Session()
    try:
        inserted, errors = batch_insert_completions(db, good)
        assert len(inserted) == 95
        assert len(errors) == 0
    finally:
        db.close()


def test_batch_exceeds_max():
    logs = [VALID_PAYLOAD.copy() for _ in range(1001)]
    resp = client.post("/api/v1/logs/batch", json=logs)
    assert resp.status_code == 400


def test_batch_empty():
    resp = client.post("/api/v1/logs/batch", json=[])
    assert resp.status_code == 200
    assert resp.json()["ingested_count"] == 0


# ---------------------------------------------------------------------------
# GET /api/v1/logs/{log_id}
# ---------------------------------------------------------------------------

def test_get_log_by_id():
    create_resp = client.post("/api/v1/logs", json=VALID_PAYLOAD)
    assert create_resp.status_code == 201
    log_id = create_resp.json()["log_id"]

    get_resp = client.get(f"/api/v1/logs/{log_id}")
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["id"] == log_id
    assert body["model"] == VALID_PAYLOAD["model"]


def test_log_not_found():
    resp = client.get("/api/v1/logs/999999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------

def test_concurrent_requests():
    def post_log(_):
        return client.post("/api/v1/logs", json=VALID_PAYLOAD)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(post_log, i) for i in range(10)]
        results = [f.result() for f in futures]

    assert len(results) == 10
    assert all(r.status_code in (201, 500) for r in results)
    assert any(r.status_code == 201 for r in results)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
