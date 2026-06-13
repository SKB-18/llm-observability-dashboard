"""
Tests for the LLM Observer SDK.

The HTTP layer is mocked with the `responses` library so no backend or
Anthropic API key is required.
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest
import responses as resp_lib

# Make the sdk package importable from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))

from llm_observer import LLMObserver, _estimate_cost

BASE = "http://localhost:8000"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_observer(**kwargs) -> LLMObserver:
    return LLMObserver(collector_url=BASE, **kwargs)


def _mock_anthropic_response(
    input_tokens: int = 20,
    output_tokens: int = 40,
    model: str = "claude-haiku-4-5-20251001",
    text: str = "Paris is the capital of France.",
) -> MagicMock:
    """Return a mock that looks like an anthropic.types.Message."""
    usage = MagicMock()
    usage.input_tokens  = input_tokens
    usage.output_tokens = output_tokens

    content_block = MagicMock()
    content_block.text = text

    msg = MagicMock()
    msg.model   = model
    msg.usage   = usage
    msg.content = [content_block]
    return msg


def _make_client(response: MagicMock) -> MagicMock:
    """Minimal Anthropic client stub."""
    client = MagicMock()
    client.messages.create = MagicMock(return_value=response)
    return client


# ---------------------------------------------------------------------------
# log_completion
# ---------------------------------------------------------------------------

@resp_lib.activate
def test_log_completion_success():
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs",
                 json={"status": "logged", "log_id": 1, "timestamp": "2024-01-01T00:00:00"},
                 status=201)

    obs = _make_observer()
    result = obs.log_completion(
        prompt="Hello", response="Hi", model="gpt-4",
        tokens_in=5, tokens_out=10, latency_ms=200.0, cost_usd=0.001,
    )
    assert result["status"] == "logged"
    assert result["log_id"] == 1


@resp_lib.activate
def test_log_completion_sends_correct_payload():
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs",
                 json={"status": "logged", "log_id": 2, "timestamp": "2024-01-01T00:00:00"},
                 status=201)

    obs = _make_observer()
    obs.log_completion(
        prompt="Q", response="A", model="gpt-4",
        tokens_in=10, tokens_out=5, latency_ms=123.4, cost_usd=0.005,
        user_id="u1", conversation_id="c1",
    )

    sent = json.loads(resp_lib.calls[0].request.body)
    assert sent["prompt"] == "Q"
    assert sent["model"] == "gpt-4"
    assert sent["user_id"] == "u1"
    assert sent["conversation_id"] == "c1"


@resp_lib.activate
def test_log_completion_collector_unreachable(tmp_path, monkeypatch):
    """When the collector is down the SDK writes a fallback log and returns gracefully."""
    import llm_observer as sdk_module
    fallback = tmp_path / "fallback.jsonl"
    monkeypatch.setattr(sdk_module, "_FALLBACK_LOG", fallback)

    # No mocked endpoint → ConnectionError
    obs = _make_observer()
    result = obs.log_completion(
        prompt="p", response="r", model="gpt-4",
        tokens_in=1, tokens_out=1, latency_ms=1.0, cost_usd=0.0,
    )
    assert result["status"] == "fallback"
    assert fallback.exists()
    lines = fallback.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["path"] == "/api/v1/logs"


# ---------------------------------------------------------------------------
# log_batch
# ---------------------------------------------------------------------------

@resp_lib.activate
def test_log_batch_success():
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs/batch",
                 json={"status": "success", "ingested_count": 3, "failed_count": 0, "errors": []},
                 status=200)

    obs = _make_observer()
    batch = [
        {"prompt": "p1", "response": "r1", "model": "gpt-4",
         "tokens_in": 5, "tokens_out": 5, "latency_ms": 100, "cost_usd": 0.001},
        {"prompt": "p2", "response": "r2", "model": "gpt-4",
         "tokens_in": 5, "tokens_out": 5, "latency_ms": 100, "cost_usd": 0.001},
        {"prompt": "p3", "response": "r3", "model": "gpt-4",
         "tokens_in": 5, "tokens_out": 5, "latency_ms": 100, "cost_usd": 0.001},
    ]
    result = obs.log_batch(batch)
    assert result["ingested_count"] == 3
    assert result["failed_count"] == 0


@resp_lib.activate
def test_log_batch_partial_failure():
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs/batch",
                 json={"status": "success", "ingested_count": 95, "failed_count": 5,
                       "errors": [{"index": 0, "reason": "bad data"}]},
                 status=200)

    obs = _make_observer()
    result = obs.log_batch([{}] * 100)
    assert result["ingested_count"] == 95
    assert result["failed_count"] == 5


# ---------------------------------------------------------------------------
# wrap_claude_client
# ---------------------------------------------------------------------------

@resp_lib.activate
def test_wrap_claude_client_returns_client():
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs",
                 json={"status": "logged", "log_id": 1, "timestamp": "2024-01-01T00:00:00"},
                 status=201)

    obs = _make_observer()
    fake_response = _mock_anthropic_response()
    client = _make_client(fake_response)
    wrapped = obs.wrap_claude_client(client)
    assert wrapped is client  # same object, mutated in-place


@resp_lib.activate
def test_wrap_transparent():
    """Wrapped client must return exactly the original response object."""
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs",
                 json={"status": "logged", "log_id": 1, "timestamp": "2024-01-01T00:00:00"},
                 status=201)

    obs = _make_observer()
    fake_response = _mock_anthropic_response(text="The answer is 42.")
    client = _make_client(fake_response)
    obs.wrap_claude_client(client)

    result = client.messages.create(
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "What is 6×7?"}],
        max_tokens=20,
    )
    # Must be the exact same object
    assert result is fake_response
    assert result.content[0].text == "The answer is 42."


@resp_lib.activate
def test_auto_logging():
    """After wrapping, a messages.create call triggers a POST to /api/v1/logs."""
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs",
                 json={"status": "logged", "log_id": 5, "timestamp": "2024-01-01T00:00:00"},
                 status=201)

    obs = _make_observer()
    fake_response = _mock_anthropic_response(input_tokens=15, output_tokens=30)
    client = _make_client(fake_response)
    obs.wrap_claude_client(client)

    client.messages.create(
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "Hello!"}],
        max_tokens=50,
    )

    # Exactly one POST to /api/v1/logs
    assert len(resp_lib.calls) == 1
    sent = json.loads(resp_lib.calls[0].request.body)
    assert sent["model"] == "claude-haiku-4-5-20251001"
    assert sent["tokens_in"] == 15
    assert sent["tokens_out"] == 30
    assert sent["latency_ms"] > 0


@resp_lib.activate
def test_collector_unreachable_does_not_block(tmp_path, monkeypatch):
    """When the collector is down, the wrapped call must still return the response."""
    import llm_observer as sdk_module
    monkeypatch.setattr(sdk_module, "_FALLBACK_LOG", tmp_path / "fb.jsonl")

    # No mocked endpoint – forces ConnectionError
    obs = _make_observer()
    fake_response = _mock_anthropic_response(text="I still work!")
    client = _make_client(fake_response)
    obs.wrap_claude_client(client)

    result = client.messages.create(
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "Test"}],
        max_tokens=20,
    )
    # Response must be returned even though the collector was unreachable
    assert result.content[0].text == "I still work!"


# ---------------------------------------------------------------------------
# Cost estimation helper
# ---------------------------------------------------------------------------

def test_estimate_cost_known_model():
    cost = _estimate_cost(1000, 500, "gpt-4")
    # 1k in × $0.03 + 0.5k out × $0.06 = $0.03 + $0.03 = $0.06
    assert abs(cost - 0.06) < 1e-6


def test_estimate_cost_unknown_model():
    cost = _estimate_cost(1000, 1000, "totally-unknown-model")
    assert cost > 0


def test_estimate_cost_zero():
    assert _estimate_cost(0, 0, "gpt-4") == 0.0


# ---------------------------------------------------------------------------
# API key header
# ---------------------------------------------------------------------------

@resp_lib.activate
def test_api_key_sent_in_header():
    resp_lib.add(resp_lib.POST, f"{BASE}/api/v1/logs",
                 json={"status": "logged", "log_id": 9, "timestamp": "2024-01-01T00:00:00"},
                 status=201)

    obs = LLMObserver(collector_url=BASE, api_key="secret-token")
    obs.log_completion(
        prompt="p", response="r", model="gpt-4",
        tokens_in=1, tokens_out=1, latency_ms=1.0, cost_usd=0.0,
    )
    assert resp_lib.calls[0].request.headers["Authorization"] == "Bearer secret-token"
