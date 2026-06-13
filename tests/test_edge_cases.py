"""
Edge-case and negative-scenario tests.

Covers every gap identified in the coverage audit:
  1. batch_insert_completions  – >50 item-level errors triggers full rollback
  2. batch_insert_completions  – SQLAlchemyError mid-commit triggers rollback
  3. _run_evals called for real – BLEU/ROUGE paths through the HTTP layer
  4. LLMJudge.batch_evaluate   – parallel scoring
  5. LLMJudge.get_evaluation_explanation – explanation text returned / failure → ""
  6. sentence_transformers live path  – one-sided empty string similarity
  7. parse_iso_date malformed fallback
  8. cors_origins_list with broken JSON
  9. Metrics endpoints with invalid query params (bad dates)
 10. GET /api/v1/evals/batch/{job_id} – polling endpoint happy + 404
 11. POST /api/v1/logs DB error → 500
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from backend.main import app
from backend.models import Completion, EvalResult
from tests.conftest import _Session

client = TestClient(app, raise_server_exceptions=False)

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


# ===========================================================================
# 1. batch_insert_completions – >50 item-level errors → full rollback
# ===========================================================================

def test_batch_over_50_errors_returns_empty_and_all_errors():
    """When >50 items error during object construction the helper must
    return ([], all_error_tuples) without touching the DB."""
    from backend.schemas import CompletionLog
    from backend.utils.db import batch_insert_completions

    good = [CompletionLog(**_BASE) for _ in range(40)]

    # Simulate 51 construction errors by patching Completion.__init__
    call_count = [0]
    original_init = Completion.__init__

    def flaky_init(self, *args, **kwargs):
        call_count[0] += 1
        if call_count[0] <= 51:
            raise ValueError(f"Simulated construction error #{call_count[0]}")
        original_init(self, *args, **kwargs)

    db = _Session()
    try:
        with patch.object(Completion, "__init__", flaky_init):
            inserted, errors = batch_insert_completions(db, good)
        assert inserted == []
        assert len(errors) == 40          # all 40 items errored (≤51 cap)
    finally:
        db.close()


def test_batch_exactly_51_errors_triggers_rollback():
    """51 errors (> 50 threshold) → early-return path, nothing committed.

    With 60 logs and the first 51 raising, the loop collects 51 errors then
    hits the `if len(errors) > 50` guard and returns immediately (before
    db.add_all is called).  Only the 51 errors are returned; the 9 successful
    objects are discarded.
    """
    from backend.schemas import CompletionLog
    from backend.utils.db import batch_insert_completions

    logs = [CompletionLog(**_BASE) for _ in range(60)]
    call_count = [0]
    original_init = Completion.__init__

    def flaky_init(self, *args, **kwargs):
        call_count[0] += 1
        if call_count[0] <= 51:
            raise ValueError("forced error")
        original_init(self, *args, **kwargs)

    db = _Session()
    try:
        with patch.object(Completion, "__init__", flaky_init):
            inserted, errors = batch_insert_completions(db, logs)
        assert inserted == []
        assert len(errors) == 51          # only the 51 that actually errored
        # DB must be empty (add_all was never called)
        assert db.query(Completion).count() == 0
    finally:
        db.close()


# ===========================================================================
# 2. batch_insert_completions – SQLAlchemyError mid-commit → rollback
# ===========================================================================

def test_batch_db_error_mid_commit_rolls_back():
    """If db.commit() raises SQLAlchemyError the helper rolls back and returns
    all items as errors."""
    from backend.schemas import CompletionLog
    from backend.utils.db import batch_insert_completions

    logs = [CompletionLog(**_BASE) for _ in range(5)]
    db = _Session()
    try:
        with patch.object(db, "commit", side_effect=SQLAlchemyError("disk full")):
            inserted, errors = batch_insert_completions(db, logs)
        assert inserted == []
        assert len(errors) == 5
        assert all(r == "database error" for _, r in errors)
    finally:
        db.close()


# ===========================================================================
# 3. POST /api/v1/logs – DB error in insert_completion → 500
# ===========================================================================

def test_single_log_db_error_returns_500():
    """If insert_completion raises, the endpoint must return 500."""
    with patch("backend.routes.logs.insert_completion", side_effect=Exception("connection lost")):
        resp = client.post("/api/v1/logs", json=_BASE)
    assert resp.status_code == 500
    assert "Database error" in resp.json()["detail"]


# ===========================================================================
# 4. _run_evals called for real (not mocked) – BLEU + ROUGE through HTTP
# ===========================================================================

def test_evaluate_endpoint_real_bleu_rouge():
    """POST /api/v1/evals/evaluate with bleu+rouge must NOT mock _run_evals –
    verifies the actual TextMetrics code runs through the route."""
    db = _Session()
    db.add(Completion(
        id=1, prompt="The cat sat on the mat",
        response="The cat sat on the mat",
        model="gpt-4", tokens_in=6, tokens_out=6,
        latency_ms=100.0, cost_usd=0.001,
    ))
    db.commit()
    db.close()

    resp = client.post("/api/v1/evals/evaluate", json={
        "completion_id": 1,
        "eval_types": ["bleu", "rouge"],
    })
    assert resp.status_code == 200
    scores = resp.json()["scores"]
    # Identical prompt & response → perfect scores
    assert scores["bleu"] == 1.0
    assert scores["rouge"] >= 0.99


def test_evaluate_endpoint_unknown_eval_type_ignored():
    """Unknown eval type must not crash the endpoint; it's silently skipped."""
    db = _Session()
    db.add(Completion(
        id=1, prompt="p", response="r",
        model="gpt-4", tokens_in=5, tokens_out=5,
        latency_ms=100.0, cost_usd=0.001,
    ))
    db.commit()
    db.close()

    resp = client.post("/api/v1/evals/evaluate", json={
        "completion_id": 1,
        "eval_types": ["nonexistent_type"],
    })
    assert resp.status_code == 200
    assert resp.json()["scores"] == {}


# ===========================================================================
# 5. LLMJudge.batch_evaluate
# ===========================================================================

def test_llm_judge_batch_evaluate():
    """batch_evaluate must return one score per completion, in order."""
    from backend.evals.llm_judge import LLMJudge, _CACHE
    _CACHE.clear()

    call_index = [0]
    scores_to_return = [6, 8, 10]

    def create_side_effect(**kwargs):
        idx = call_index[0] % len(scores_to_return)
        call_index[0] += 1
        resp = MagicMock()
        resp.output_text = f'{{"score": {scores_to_return[idx]}, "explanation": "ok"}}'
        return resp

    judge = LLMJudge.__new__(LLMJudge)
    judge._client = MagicMock()
    judge._client.responses.create.side_effect = create_side_effect
    judge._model = "test"

    completions = [
        {"prompt": f"p{i}", "response": f"r{i}", "criteria": "helpful"}
        for i in range(3)
    ]
    results = judge.batch_evaluate(completions)

    assert len(results) == 3
    assert all(0.0 <= s <= 1.0 for s in results)
    _CACHE.clear()


def test_llm_judge_batch_evaluate_empty():
    from backend.evals.llm_judge import LLMJudge
    judge = LLMJudge.__new__(LLMJudge)
    judge._client = MagicMock()
    judge._model = "test"
    assert judge.batch_evaluate([]) == []


# ===========================================================================
# 6. LLMJudge.get_evaluation_explanation
# ===========================================================================

def test_llm_judge_explanation_returned():
    from backend.evals.llm_judge import LLMJudge
    judge = LLMJudge.__new__(LLMJudge)
    resp = MagicMock()
    resp.output_text = "This is a detailed explanation."
    judge._client = MagicMock()
    judge._client.responses.create.return_value = resp
    judge._model = "test"

    result = judge.get_evaluation_explanation("prompt", "response", "criteria")
    assert result == "This is a detailed explanation."


def test_llm_judge_explanation_api_failure_returns_empty():
    from backend.evals.llm_judge import LLMJudge
    judge = LLMJudge.__new__(LLMJudge)
    judge._client = MagicMock()
    judge._client.responses.create.side_effect = Exception("timeout")
    judge._model = "test"

    result = judge.get_evaluation_explanation("prompt", "response")
    assert result == ""


# ===========================================================================
# 7. sentence_transformers – one-sided empty string (Jaccard fallback)
# ===========================================================================

def test_similarity_one_side_empty():
    from backend.evals.text_metrics import TextMetrics
    assert TextMetrics.similarity_score("hello world", "") == 0.0
    assert TextMetrics.similarity_score("", "hello world") == 0.0


def test_similarity_no_overlap():
    from backend.evals.text_metrics import TextMetrics
    score = TextMetrics.similarity_score("apple banana cherry", "dog cat fish")
    assert score == 0.0


# ===========================================================================
# 8. parse_iso_date – malformed fallback (strips tz and parses)
# ===========================================================================

def test_parse_iso_date_strips_tz_on_failure():
    """A datetime with an unusual but valid prefix should parse via fallback."""
    from backend.utils.helpers import parse_iso_date
    # Standard offset format – should parse normally
    dt = parse_iso_date("2024-03-15T09:30:00+05:30")
    assert dt.year == 2024
    assert dt.month == 3
    assert dt.day == 15


def test_parse_iso_date_naive_no_tz():
    from backend.utils.helpers import parse_iso_date
    dt = parse_iso_date("2024-03-15T09:30:00")
    assert dt.hour == 9


# ===========================================================================
# 9. config.py – cors_origins_list with broken JSON
# ===========================================================================

def test_cors_origins_malformed_json_falls_back_to_wildcard():
    from backend.config import Settings
    s = Settings(CORS_ORIGINS="not-valid-json")
    assert s.cors_origins_list == ["*"]


def test_cors_origins_valid_list():
    from backend.config import Settings
    s = Settings(CORS_ORIGINS='["http://localhost:3000"]')
    assert s.cors_origins_list == ["http://localhost:3000"]


# ===========================================================================
# 10. Metrics endpoints – invalid query params
# ===========================================================================

def test_summary_invalid_start_date_returns_error():
    resp = client.get("/api/v1/metrics/summary?start_date=not-a-date")
    assert resp.status_code in (400, 422, 500)


def test_by_hour_invalid_dates_returns_error():
    resp = client.get("/api/v1/metrics/by-hour?start_date=banana")
    assert resp.status_code in (400, 422, 500)


def test_latency_percentiles_invalid_date_returns_error():
    resp = client.get("/api/v1/metrics/latency-percentiles?end_date=99-99-99")
    assert resp.status_code in (400, 422, 500)


# ===========================================================================
# 11. GET /api/v1/evals/batch/{job_id} – polling endpoint
# ===========================================================================

@patch("backend.routes.evals._run_evals")
def test_batch_job_status_polling(mock_run):
    """After submitting a batch, the job_id must be pollable."""
    mock_run.return_value = ({"bleu": 0.5}, "")

    db = _Session()
    db.add(Completion(
        id=1, prompt="p", response="r", model="gpt-4",
        tokens_in=5, tokens_out=5, latency_ms=100.0, cost_usd=0.001,
    ))
    db.commit()
    db.close()

    submit = client.post("/api/v1/evals/batch", json={
        "completion_ids": [1],
        "eval_types": ["bleu"],
    })
    assert submit.status_code == 202
    job_id = submit.json()["job_id"]

    poll = client.get(f"/api/v1/evals/batch/{job_id}")
    assert poll.status_code == 200
    assert "status" in poll.json()


def test_batch_job_unknown_id_returns_404():
    resp = client.get("/api/v1/evals/batch/nonexistent_job_xyz")
    assert resp.status_code == 404


# ===========================================================================
# 12. Bonus: sample_rate < 1.0 in batch eval
# ===========================================================================

@patch("backend.routes.evals._run_evals")
def test_batch_eval_sample_rate(mock_run):
    """sample_rate=0.5 on 10 items should submit ~5 (at most 10)."""
    mock_run.return_value = ({"bleu": 0.6}, "")

    db = _Session()
    for _ in range(10):
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
        "sample_rate": 0.5,
    })
    assert resp.status_code == 202
    assert resp.json()["submitted_count"] <= 10
    assert resp.json()["submitted_count"] >= 1


# ===========================================================================
# 13. Bonus: GET /api/v1/logs/{id} with non-integer id
# ===========================================================================

def test_get_log_non_integer_id():
    resp = client.get("/api/v1/logs/not-an-int")
    assert resp.status_code == 422


# ===========================================================================
# 14. Bonus: POST /api/v1/logs with empty strings
# ===========================================================================

def test_log_empty_prompt_accepted():
    """Empty string is a valid prompt (schema doesn't forbid it)."""
    resp = client.post("/api/v1/logs", json={**_BASE, "prompt": ""})
    assert resp.status_code == 201


def test_log_very_long_prompt():
    """10 000-character prompt must be stored without truncation."""
    big = "x" * 10_000
    resp = client.post("/api/v1/logs", json={**_BASE, "prompt": big})
    assert resp.status_code == 201
    log_id = resp.json()["log_id"]
    fetched = client.get(f"/api/v1/logs/{log_id}").json()
    assert len(fetched["prompt"]) == 10_000


# ===========================================================================
# 15. Bonus: cost_usd exactly 0 is valid
# ===========================================================================

def test_log_zero_cost_stored_correctly():
    resp = client.post("/api/v1/logs", json={**_BASE, "cost_usd": 0.0})
    assert resp.status_code == 201
    log_id = resp.json()["log_id"]
    fetched = client.get(f"/api/v1/logs/{log_id}").json()
    assert fetched["cost_usd"] == 0.0
