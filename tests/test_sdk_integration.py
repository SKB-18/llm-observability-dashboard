"""
SDK integration tests.

All HTTP calls are mocked with `responses`; no real Anthropic API key needed.
The SDK is imported directly from sdk/ so these tests also validate the
packaging path.
"""
from __future__ import annotations

import json
import sys
import os
import time

import pytest
import responses as resp_lib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))
from llm_observer import LLMObserver

BASE = "http://testcollector:8000"

_LOG = dict(
    prompt="Hello", response="Hi", model="claude-3-5-sonnet",
    tokens_in=10, tokens_out=5, latency_ms=150.0, cost_usd=0.002,
)


def _observer(**kw) -> LLMObserver:
    return LLMObserver(collector_url=BASE, **kw)


def _fake_response(log_id: int = 1):
    from unittest.mock import MagicMock
    usage = MagicMock(); usage.input_tokens = 20; usage.output_tokens = 40
    content = MagicMock(); content.text = "Paris."
    msg = MagicMock()
    msg.model   = "claude-3-5-sonnet-20241022"
    msg.usage   = usage
    msg.content = [content]
    return msg


# ---------------------------------------------------------------------------
# A. log_completion reaches the API
# ---------------------------------------------------------------------------

@resp_lib.activate
def test_sdk_logs_to_api():
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs",
                 json={"status": "logged", "log_id": 42, "timestamp": "2024-01-01T00:00:00"},
                 status=201)

    obs = _observer()
    result = obs.log_completion(**_LOG)

    assert result["status"] == "logged"
    assert result["log_id"] == 42
    assert len(resp_lib.calls) == 1

    payload = json.loads(resp_lib.calls[0].request.body)
    assert payload["prompt"] == "Hello"
    assert payload["tokens_in"] == 10


# ---------------------------------------------------------------------------
# B. wrap_claude_client auto-logs the call
# ---------------------------------------------------------------------------

@resp_lib.activate
def test_wrap_claude_client():
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs",
                 json={"status": "logged", "log_id": 1, "timestamp": "2024-01-01T00:00:00"},
                 status=201)

    from unittest.mock import MagicMock
    fake_resp = _fake_response()
    client = MagicMock()
    client.messages.create = MagicMock(return_value=fake_resp)

    obs = _observer()
    obs.wrap_claude_client(client)

    result = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Capital of France?"}],
        max_tokens=50,
    )
    # Original response returned unchanged
    assert result is fake_resp

    # One log call made
    assert len(resp_lib.calls) == 1
    body = json.loads(resp_lib.calls[0].request.body)
    assert body["model"] == "claude-3-5-sonnet-20241022"
    assert body["tokens_in"] == 20
    assert body["tokens_out"] == 40


# ---------------------------------------------------------------------------
# C. 50 mock calls – all logged
# ---------------------------------------------------------------------------

@resp_lib.activate
def test_50_calls_logged():
    # Allow any number of calls to the logs endpoint
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs",
                 json={"status": "logged", "log_id": 1, "timestamp": "2024-01-01T00:00:00"},
                 status=201)

    from unittest.mock import MagicMock
    obs = _observer()
    client = MagicMock()
    call_count = [0]

    def create_side_effect(*args, **kwargs):
        call_count[0] += 1
        return _fake_response(call_count[0])

    client.messages.create = MagicMock(side_effect=create_side_effect)
    obs.wrap_claude_client(client)

    for i in range(50):
        client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": f"Q{i}"}],
            max_tokens=20,
        )

    assert call_count[0] == 50
    # One log POST per call
    assert len(resp_lib.calls) == 50

    # Verify each payload has the right model
    for call in resp_lib.calls:
        body = json.loads(call.request.body)
        assert body["model"] == "claude-3-5-sonnet-20241022"
        assert body["tokens_in"] > 0
        assert body["tokens_out"] > 0


# ---------------------------------------------------------------------------
# D. Collector unreachable – must not raise
# ---------------------------------------------------------------------------

@resp_lib.activate
def test_collector_unreachable(tmp_path, monkeypatch):
    import llm_observer as sdk_module
    monkeypatch.setattr(sdk_module, "_FALLBACK_LOG", tmp_path / "fb.jsonl")

    # No mock registered → ConnectionError
    obs = _observer()
    # Should not raise
    result = obs.log_completion(**_LOG)
    assert result["status"] == "fallback"

    # Fallback written
    lines = (tmp_path / "fb.jsonl").read_text().strip().splitlines()
    assert len(lines) >= 1


@resp_lib.activate
def test_wrapped_client_unreachable_still_returns_response(tmp_path, monkeypatch):
    import llm_observer as sdk_module
    monkeypatch.setattr(sdk_module, "_FALLBACK_LOG", tmp_path / "fb2.jsonl")

    from unittest.mock import MagicMock
    fake_resp = _fake_response()
    client = MagicMock()
    client.messages.create = MagicMock(return_value=fake_resp)

    obs = _observer()
    obs.wrap_claude_client(client)

    # Even with no collector, the wrapped call must return the response
    result = client.messages.create(
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=10,
    )
    assert result is fake_resp


# ---------------------------------------------------------------------------
# E. log_batch – correct payload shape
# ---------------------------------------------------------------------------

@resp_lib.activate
def test_sdk_log_batch():
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs/batch",
                 json={"status": "success", "ingested_count": 5, "failed_count": 0, "errors": []},
                 status=200)

    obs = _observer()
    batch = [_LOG.copy() for _ in range(5)]
    result = obs.log_batch(batch)

    assert result["ingested_count"] == 5
    sent = json.loads(resp_lib.calls[0].request.body)
    assert isinstance(sent, list)
    assert len(sent) == 5


# ---------------------------------------------------------------------------
# F. API key is forwarded
# ---------------------------------------------------------------------------

@resp_lib.activate
def test_api_key_forwarded():
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs",
                 json={"status": "logged", "log_id": 1, "timestamp": "2024-01-01T00:00:00"},
                 status=201)

    obs = LLMObserver(collector_url=BASE, api_key="my-secret")
    obs.log_completion(**_LOG)

    assert resp_lib.calls[0].request.headers.get("Authorization") == "Bearer my-secret"
