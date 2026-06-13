"""
Final coverage tests — no external API key, no Postgres, no large models needed.

Every gap is plugged via mocking:
  - anthropic.Anthropic()   → MagicMock
  - sentence_transformers   → sys.modules patch
  - requests.Timeout        → side_effect
  - open()                  → PermissionError
  - TextMetrics.bleu_score  → RuntimeError
"""
from __future__ import annotations

import sys
import time
import os
import requests

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Completion
from tests.conftest import _Session

client = TestClient(app, raise_server_exceptions=False)

_LOG = dict(
    prompt="Hello", response="Hi", model="gpt-4",
    tokens_in=10, tokens_out=5, latency_ms=150.0, cost_usd=0.002,
)

# SDK path setup (same as other SDK tests)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))
import llm_observer as sdk_module
from llm_observer import LLMObserver


@pytest.fixture(autouse=True)
def clean(reset_db):
    pass


# ─────────────────────────────────────────────────────────────────────────────
# main.py lines 32-36, 123 — lifespan startup/shutdown + root endpoint
# ─────────────────────────────────────────────────────────────────────────────

def test_lifespan_startup_and_shutdown():
    """Using TestClient as context manager fires the lifespan on enter/exit."""
    with TestClient(app) as lifespan_client:
        r = lifespan_client.get("/health")
        assert r.status_code == 200
    # Startup (lines 32-35) and shutdown (line 36) both ran.


def test_root_endpoint():
    """GET / returns the API info dict — covers main.py:123."""
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert "version" in body
    assert "docs" in body


# ─────────────────────────────────────────────────────────────────────────────
# main.py lines 105-106 — generic Exception handler
# ─────────────────────────────────────────────────────────────────────────────

def test_generic_exception_handler_returns_500():
    """An unhandled RuntimeError inside a route triggers the global handler."""
    db = _Session()
    db.add(Completion(
        id=900, prompt="p", response="r", model="gpt-4",
        tokens_in=5, tokens_out=5, latency_ms=100.0, cost_usd=0.001,
    ))
    db.commit()
    db.close()

    # _run_evals has no try/except in evaluate_completion — a bare RuntimeError
    # bubbles to FastAPI's global Exception handler (main.py:103-109).
    with patch("backend.routes.evals._run_evals", side_effect=RuntimeError("deliberate crash")):
        r = client.post("/api/v1/evals/evaluate", json={
            "completion_id": 900,
            "eval_types": ["bleu"],
        })
    assert r.status_code == 500
    assert r.json()["detail"] == "Internal server error"


# ─────────────────────────────────────────────────────────────────────────────
# llm_judge.py lines 34-36 — LLMJudge.__init__
# ─────────────────────────────────────────────────────────────────────────────

def test_llm_judge_init_mocked_azure():
    """LLMJudge.__init__ runs with a mocked AzureOpenAI client — no API key needed."""
    from backend.evals.llm_judge import LLMJudge, _CACHE
    _CACHE.clear()

    mock_resp = MagicMock()
    mock_resp.output_text = '{"score": 7, "explanation": "ok"}'
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_resp

    with patch("openai.AzureOpenAI", return_value=mock_client):
        judge = LLMJudge()
        score = judge.evaluate_response("What is 2+2?", "4")
        assert 0.0 <= score <= 1.0
    _CACHE.clear()


# ─────────────────────────────────────────────────────────────────────────────
# routes/evals.py lines 86-97 — llm_judge branch inside _run_evals
# ─────────────────────────────────────────────────────────────────────────────

def test_run_evals_llm_judge_branch_via_http():
    """Calling POST /evaluate with eval_type=llm_judge runs the llm_judge branch."""
    from backend.evals.llm_judge import _CACHE
    _CACHE.clear()

    db = _Session()
    db.add(Completion(
        id=901, prompt="What is the capital of France?",
        response="Paris", model="gpt-4",
        tokens_in=8, tokens_out=3, latency_ms=200.0, cost_usd=0.001,
    ))
    db.commit()
    db.close()

    mock_resp = MagicMock()
    mock_resp.output_text = '{"score": 9, "explanation": "Correct answer."}'
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_resp

    with patch("openai.AzureOpenAI", return_value=mock_client):
        r = client.post("/api/v1/evals/evaluate", json={
            "completion_id": 901,
            "eval_types": ["llm_judge"],
        })
    assert r.status_code == 200
    assert "llm_judge" in r.json()["scores"]
    _CACHE.clear()


# ─────────────────────────────────────────────────────────────────────────────
# routes/evals.py lines 73-75 and 81-83 — BLEU/ROUGE exception handlers
# ─────────────────────────────────────────────────────────────────────────────

def test_run_evals_bleu_exception_handler():
    """If bleu_score raises, the except branch records 0.0 instead of crashing."""
    db = _Session()
    db.add(Completion(
        id=902, prompt="p", response="r", model="gpt-4",
        tokens_in=5, tokens_out=5, latency_ms=100.0, cost_usd=0.001,
    ))
    db.commit()
    db.close()

    with patch("backend.evals.text_metrics.TextMetrics.bleu_score",
               side_effect=RuntimeError("bleu exploded")):
        r = client.post("/api/v1/evals/evaluate", json={
            "completion_id": 902,
            "eval_types": ["bleu"],
        })
    assert r.status_code == 200
    assert r.json()["scores"]["bleu"] == 0.0


def test_run_evals_rouge_exception_handler():
    """If rouge_score raises, the except branch records 0.0."""
    db = _Session()
    db.add(Completion(
        id=903, prompt="p", response="r", model="gpt-4",
        tokens_in=5, tokens_out=5, latency_ms=100.0, cost_usd=0.001,
    ))
    db.commit()
    db.close()

    with patch("backend.evals.text_metrics.TextMetrics.rouge_score",
               side_effect=RuntimeError("rouge exploded")):
        r = client.post("/api/v1/evals/evaluate", json={
            "completion_id": 903,
            "eval_types": ["rouge"],
        })
    assert r.status_code == 200
    assert r.json()["scores"]["rouge"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# routes/evals.py lines 157-163 — batch worker thread real execution
# ─────────────────────────────────────────────────────────────────────────────

@patch("backend.database.SessionLocal", new=_Session)
def test_worker_thread_runs_real_bleu():
    """Batch eval without mocking _run_evals covers the worker try/finally body.

    We patch SessionLocal so the daemon thread reads from the same in-memory
    SQLite DB (StaticPool) that the test inserts into.
    """
    db = _Session()
    db.add(Completion(
        id=904, prompt="The cat sat on the mat",
        response="The cat sat on the mat",
        model="gpt-4", tokens_in=6, tokens_out=6,
        latency_ms=100.0, cost_usd=0.001,
    ))
    db.commit()
    db.close()

    resp = client.post("/api/v1/evals/batch", json={
        "completion_ids": [904],
        "eval_types": ["bleu"],        # no llm_judge → no API key needed
    })
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    # Poll until worker finishes (usually < 200 ms)
    for _ in range(100):
        status = client.get(f"/api/v1/evals/batch/{job_id}").json()
        if status["status"] == "complete":
            break
        time.sleep(0.05)

    assert status["status"] == "complete"
    assert status["done"] == 1


@patch("backend.routes.evals._run_evals", side_effect=RuntimeError("worker crash"))
@patch("backend.database.SessionLocal", new=_Session)
def test_worker_thread_exception_handler(mock_run):
    """RuntimeError inside the worker covers the except branch (line 161)."""
    db = _Session()
    db.add(Completion(
        id=905, prompt="p", response="r", model="gpt-4",
        tokens_in=5, tokens_out=5, latency_ms=100.0, cost_usd=0.001,
    ))
    db.commit()
    db.close()

    resp = client.post("/api/v1/evals/batch", json={
        "completion_ids": [905],
        "eval_types": ["bleu"],
    })
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    for _ in range(100):
        status = client.get(f"/api/v1/evals/batch/{job_id}").json()
        if status["status"] == "complete":
            break
        time.sleep(0.05)

    # finally block still ran even though _run_evals raised
    assert status["status"] == "complete"
    assert status["done"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# text_metrics.py lines 55-59 — sentence_transformers live path
# ─────────────────────────────────────────────────────────────────────────────

def test_similarity_sentence_transformers_path():
    """Mocking sentence_transformers in sys.modules forces the try branch."""
    mock_st = MagicMock()
    mock_tensor = MagicMock()
    mock_st.SentenceTransformer.return_value.encode.return_value = mock_tensor
    # cos_sim must return something indexable as [[float]]
    mock_st.util.cos_sim.return_value = [[0.92]]

    with patch.dict(sys.modules, {"sentence_transformers": mock_st}):
        # Re-import forces the function to see the mocked module
        import importlib
        import backend.evals.text_metrics as tm
        importlib.reload(tm)
        score = tm.TextMetrics.similarity_score("hello world", "hello world")

    # Restore original module state for other tests
    import importlib
    import backend.evals.text_metrics as tm
    importlib.reload(tm)

    assert 0.0 <= score <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# helpers.py lines 59-61 — parse_iso_date ValueError fallback
# ─────────────────────────────────────────────────────────────────────────────

def test_parse_iso_date_fallback_branch():
    """A string that fails fromisoformat but whose first 19 chars are valid."""
    from backend.utils.helpers import parse_iso_date
    # "BADTZ" at the end causes fromisoformat to raise ValueError,
    # but cleaned[:19] = "2024-06-15T10:30:00" parses fine.
    dt = parse_iso_date("2024-06-15T10:30:00BADTZ")
    assert dt.year == 2024
    assert dt.hour == 10
    assert dt.minute == 30


# ─────────────────────────────────────────────────────────────────────────────
# sdk/llm_observer.py lines 48-49 — _write_fallback open() failure
# ─────────────────────────────────────────────────────────────────────────────

def test_write_fallback_open_failure_is_logged():
    """PermissionError on file open is caught and logged, not raised.

    We replace _FALLBACK_LOG with a full MagicMock so that .open() can have a
    side_effect — WindowsPath.open is a read-only slot on Path instances.
    """
    mock_path = MagicMock()
    mock_path.open.side_effect = PermissionError("disk read-only")
    with patch.object(sdk_module, "_FALLBACK_LOG", mock_path):
        # Must not raise — just logs a warning
        sdk_module._write_fallback({"test": "payload"})


# ─────────────────────────────────────────────────────────────────────────────
# sdk/llm_observer.py lines 192-193 — wrap_claude_client exception handler
# ─────────────────────────────────────────────────────────────────────────────

def test_wrap_claude_client_log_failure_still_returns_response():
    """If log_completion raises inside the wrapper, the original response is still returned."""
    fake_resp = MagicMock()
    fake_resp.model = "gpt-4"
    fake_resp.usage = MagicMock(input_tokens=10, output_tokens=5)
    fake_resp.content = [MagicMock(text="answer")]

    mock_create = MagicMock(return_value=fake_resp)
    fake_client = MagicMock()
    fake_client.messages.create = mock_create

    obs = LLMObserver(collector_url="http://nowhere:9999")
    obs.log_completion = MagicMock(side_effect=RuntimeError("log failed"))
    obs.wrap_claude_client(fake_client)

    result = fake_client.messages.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=50,
    )
    # Response returned despite the logging failure
    assert result is fake_resp
    obs.log_completion.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# sdk/llm_observer.py lines 214-220 — Timeout + generic Exception branches
# ─────────────────────────────────────────────────────────────────────────────

def test_sdk_timeout_returns_fallback(tmp_path, monkeypatch):
    """requests.Timeout triggers the Timeout branch and writes fallback log."""
    monkeypatch.setattr(sdk_module, "_FALLBACK_LOG", tmp_path / "fb_timeout.jsonl")
    obs = LLMObserver(collector_url="http://nowhere:9999")

    with patch.object(obs._session, "post",
                      side_effect=requests.exceptions.Timeout("took too long")):
        result = obs.log_completion(**_LOG)

    assert result["status"] == "fallback"
    assert result["error"] == "timeout"
    assert (tmp_path / "fb_timeout.jsonl").exists()


def test_sdk_generic_exception_returns_error():
    """An unexpected exception (not ConnectionError/Timeout) hits the generic branch."""
    obs = LLMObserver(collector_url="http://nowhere:9999")

    with patch.object(obs._session, "post",
                      side_effect=ValueError("unexpected SSL error")):
        result = obs.log_completion(**_LOG)

    assert result["status"] == "error"
    assert "unexpected SSL error" in result["error"]
