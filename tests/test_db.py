"""
Tests for database utilities, logging config, and middleware.
"""
import logging
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from backend.main import app
from backend.models import Base, Completion
from backend.utils.logging_config import setup_logging, get_logger
from backend.utils.helpers import (
    calculate_cost,
    estimate_tokens,
    parse_iso_date,
    generate_request_id,
)
from tests.conftest import _Session, _engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean(reset_db):
    pass


# ---------------------------------------------------------------------------
# Database utilities
# ---------------------------------------------------------------------------

def test_get_db_yields_session():
    from backend.database import get_db
    gen = get_db()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass


def test_create_tables_idempotent():
    """Calling create_tables twice must not raise."""
    from backend.database import create_tables
    create_tables()
    create_tables()
    inspector = inspect(_engine)
    assert "completions" in inspector.get_table_names()


def test_tables_have_expected_columns():
    inspector = inspect(_engine)
    cols = {c["name"] for c in inspector.get_columns("completions")}
    for expected in ("id", "prompt", "response", "model", "tokens_in", "tokens_out",
                     "latency_ms", "cost_usd", "timestamp"):
        assert expected in cols, f"Missing column: {expected}"


def test_session_insert_and_query():
    db = _Session()
    obj = Completion(
        prompt="ping", response="pong", model="gpt-4",
        tokens_in=5, tokens_out=5, latency_ms=100.0, cost_usd=0.001,
    )
    db.add(obj)
    db.commit()
    fetched = db.query(Completion).filter_by(id=obj.id).first()
    assert fetched is not None
    assert fetched.response == "pong"
    db.close()


# ---------------------------------------------------------------------------
# Logging config
# ---------------------------------------------------------------------------

def test_logging_setup_does_not_raise():
    # setup_logging is called at import time in main.py; calling again is a no-op
    setup_logging(level="INFO")


def test_get_logger_returns_logger():
    log = get_logger("test.module")
    assert isinstance(log, logging.Logger)
    assert log.name == "test.module"


def test_logger_emits_message(caplog):
    log = get_logger("test.emit")
    with caplog.at_level(logging.INFO, logger="test.emit"):
        log.info("hello from test")
    assert "hello from test" in caplog.text


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def test_calculate_cost_known_model():
    cost = calculate_cost(1000, 500, "gpt-4")
    # 1000 in × $0.03/1k + 500 out × $0.06/1k = $0.03 + $0.03 = $0.06
    assert abs(cost - 0.06) < 1e-6


def test_calculate_cost_unknown_model():
    cost = calculate_cost(1000, 1000, "unknown-model-xyz")
    assert cost > 0


def test_calculate_cost_zero_tokens():
    assert calculate_cost(0, 0, "gpt-4") == 0.0


def test_estimate_tokens_basic():
    # 400 chars ≈ 100 tokens
    assert estimate_tokens("a" * 400) == 100


def test_estimate_tokens_minimum():
    assert estimate_tokens("") == 1


def test_parse_iso_date_z_suffix():
    dt = parse_iso_date("2024-06-11T12:00:00Z")
    assert dt.year == 2024
    assert dt.month == 6
    assert dt.day == 11


def test_parse_iso_date_offset():
    dt = parse_iso_date("2024-06-11T12:00:00+00:00")
    assert dt.hour == 12


def test_parse_iso_date_naive():
    dt = parse_iso_date("2024-06-11T12:00:00")
    assert dt.year == 2024


def test_generate_request_id_unique():
    ids = {generate_request_id() for _ in range(100)}
    assert len(ids) == 100


def test_generate_request_id_format():
    rid = generate_request_id()
    # UUID4 format: 8-4-4-4-12
    parts = rid.split("-")
    assert len(parts) == 5


# ---------------------------------------------------------------------------
# Middleware – verify request_id header is returned
# ---------------------------------------------------------------------------

def test_middleware_attaches_request_id():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "x-request-id" in resp.headers


def test_middleware_attaches_process_time():
    resp = client.get("/health")
    assert "x-process-time-ms" in resp.headers
    assert float(resp.headers["x-process-time-ms"]) >= 0


def test_middleware_logs_requests(caplog):
    with caplog.at_level(logging.INFO, logger="backend.main"):
        client.get("/health")
    assert any("method=GET" in r.message or "/health" in r.message for r in caplog.records)
