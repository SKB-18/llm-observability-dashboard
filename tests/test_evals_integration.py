"""
Evaluation integration tests.

Covers the full POST-log → POST-eval → verify-stored cycle.
All LLM judge calls are mocked; text metric calculations run for real.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Completion, EvalResult
from tests.conftest import _Session

client = TestClient(app, raise_server_exceptions=False)

_LOG = dict(
    prompt="What is the capital of France?",
    response="The capital of France is Paris.",
    model="gpt-4",
    tokens_in=12,
    tokens_out=8,
    latency_ms=180.0,
    cost_usd=0.001,
)


@pytest.fixture(autouse=True)
def clean(reset_db):
    pass


# ---------------------------------------------------------------------------
# A. Evaluate then query stored results
# ---------------------------------------------------------------------------

@patch("backend.routes.evals._run_evals")
def test_evaluate_then_query(mock_run):
    mock_run.return_value = ({"bleu": 0.82, "rouge": 0.75}, "Accurate and concise.")

    # Create a completion
    r = client.post("/api/v1/logs", json=_LOG)
    assert r.status_code == 201
    log_id = r.json()["log_id"]

    # Evaluate it
    ev = client.post("/api/v1/evals/evaluate", json={
        "completion_id": log_id,
        "eval_types": ["bleu", "rouge"],
    })
    assert ev.status_code == 200
    body = ev.json()
    assert body["completion_id"] == log_id
    assert abs(body["scores"]["bleu"] - 0.82) < 1e-6

    # Verify persisted in the DB
    db = _Session()
    stored = db.query(EvalResult).filter_by(completion_id=log_id).all()
    db.close()
    assert len(stored) == 2
    scores = {row.eval_type: row.score for row in stored}
    assert abs(scores["bleu"] - 0.82) < 1e-6
    assert abs(scores["rouge"] - 0.75) < 1e-6


# ---------------------------------------------------------------------------
# B. Text metrics consistency (no mocks)
# ---------------------------------------------------------------------------

def test_text_metrics_bleu_identical():
    from backend.evals.text_metrics import TextMetrics
    assert TextMetrics.bleu_score("hello world test", "hello world test") == 1.0


def test_text_metrics_bleu_low_for_different():
    from backend.evals.text_metrics import TextMetrics
    score = TextMetrics.bleu_score(
        "The sky is blue and beautiful",
        "Quantum mechanics describes subatomic particles",
    )
    assert score < 0.3


def test_text_metrics_rouge_identical():
    from backend.evals.text_metrics import TextMetrics
    r = TextMetrics.rouge_score("same text here", "same text here")
    assert r["rouge1"] == 1.0
    assert r["rougeL"] == 1.0


def test_text_metrics_rouge_partial():
    from backend.evals.text_metrics import TextMetrics
    r = TextMetrics.rouge_score("the cat sat on the mat", "the cat sat")
    assert 0.0 < r["rouge1"] < 1.0


def test_text_metrics_similarity_identical():
    from backend.evals.text_metrics import TextMetrics
    assert TextMetrics.similarity_score("hello", "hello") == 1.0


def test_text_metrics_similarity_empty():
    from backend.evals.text_metrics import TextMetrics
    assert TextMetrics.similarity_score("", "") == 1.0


def test_text_metrics_similarity_order():
    """Similar texts should score higher than unrelated texts."""
    from backend.evals.text_metrics import TextMetrics
    similar   = TextMetrics.similarity_score("The dog ran fast", "The dog was running quickly")
    unrelated = TextMetrics.similarity_score("The dog ran fast", "Quantum physics is complex")
    assert similar > unrelated


# ---------------------------------------------------------------------------
# C. LLM Judge calibration (mocked)
# ---------------------------------------------------------------------------

def test_llm_judge_score_range():
    from backend.evals.llm_judge import LLMJudge, _CACHE
    from unittest.mock import MagicMock
    _CACHE.clear()
    judge = LLMJudge.__new__(LLMJudge)
    resp = MagicMock()
    resp.output_text = '{"score": 7, "explanation": "Good."}'
    judge._client = MagicMock()
    judge._client.responses.create.return_value = resp
    judge._model = "test"

    score = judge.evaluate_response("What is 2+2?", "4")
    assert 0.0 <= score <= 1.0
    _CACHE.clear()


def test_llm_judge_consistent_for_same_input():
    """Same input should always return the same cached score."""
    from backend.evals.llm_judge import LLMJudge, _CACHE
    from unittest.mock import MagicMock
    _CACHE.clear()
    judge = LLMJudge.__new__(LLMJudge)
    resp = MagicMock()
    resp.output_text = '{"score": 8, "explanation": "ok"}'
    judge._client = MagicMock()
    judge._client.responses.create.return_value = resp
    judge._model = "test"

    s1 = judge.evaluate_response("fixed prompt", "fixed response", "fixed criteria")
    s2 = judge.evaluate_response("fixed prompt", "fixed response", "fixed criteria")
    assert s1 == s2
    # Only one real API call (second hits cache)
    assert judge._client.responses.create.call_count == 1
    _CACHE.clear()


# ---------------------------------------------------------------------------
# D. Batch eval endpoint
# ---------------------------------------------------------------------------

@patch("backend.routes.evals._run_evals")
def test_batch_eval_submitted(mock_run):
    mock_run.return_value = ({"bleu": 0.7}, "")

    # Insert two completions
    db = _Session()
    for _ in range(2):
        db.add(Completion(
            prompt="p", response="r", model="gpt-4",
            tokens_in=5, tokens_out=5, latency_ms=100.0, cost_usd=0.001,
        ))
    db.commit()
    ids = [c.id for c in db.query(Completion).all()]
    db.close()

    resp = client.post("/api/v1/evals/batch", json={
        "completion_ids": ids,
        "eval_types": ["bleu"],
    })
    assert resp.status_code == 202
    assert resp.json()["submitted_count"] == len(ids)
    assert resp.json()["status"] == "processing"


# ---------------------------------------------------------------------------
# E. 404 on missing completion
# ---------------------------------------------------------------------------

@patch("backend.routes.evals._run_evals")
def test_eval_missing_completion(mock_run):
    resp = client.post("/api/v1/evals/evaluate", json={
        "completion_id": 99999,
        "eval_types": ["bleu"],
    })
    assert resp.status_code == 404
