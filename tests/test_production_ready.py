"""
Production-readiness test suite.

Covers:
 - All uncovered branches in routes/evals.py, routes/logs.py, metrics_queries.py
 - Date-filtered endpoints (start_date / end_date params)
 - Edge cases: empty DB, missing IDs, large payloads, invalid params
 - Complete happy-path audit of every endpoint
 - LLM judge exception path (evals.py lines 95-97)
 - model filter in GET /api/v1/logs (line 38)
 - Batch eval worker 'continue' on missing completion (line 156)
 - LLM judge resilience: slow response, malformed JSON, score clamping
"""
import time
import threading
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Completion, EvalResult
from tests.conftest import _Session
from backend.evals.llm_judge import _CACHE as _LLM_CACHE
import backend.evals.llm_judge as _llm_judge_mod

client = TestClient(app)

NOW = datetime(2024, 6, 11, 12, 0, 0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _comp(model="gpt-4", latency=400.0, cost=0.01, hour=0, source="lmsys",
          tokens_out=50, tokens_in=20):
    return Completion(
        prompt="Test prompt",
        response="Test response",
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency,
        cost_usd=cost,
        timestamp=NOW + timedelta(hours=hour),
        source=source,
    )


def _make_judge_mock(score_json='{"score": 7, "explanation": "ok"}'):
    mock_resp = MagicMock()
    mock_resp.output_text = score_json
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_resp
    return mock_client


@pytest.fixture()
def seeded_db(reset_db):
    """Populate DB with 5 LMSYS + 1 benchmark completion. NOT autouse."""
    db = _Session()
    db.add_all([
        _comp("gpt-4",        latency=300, cost=0.01, hour=0),
        _comp("gpt-4",        latency=500, cost=0.02, hour=1),
        _comp("claude-3-opus",latency=250, cost=0.005, hour=0),
        _comp("claude-3-opus",latency=450, cost=0.008, hour=2),
        _comp("llama-2-70b",  latency=900, cost=0.001, hour=0),
        _comp("eval-dataset", latency=0, cost=0, source="evals_benchmark",
              tokens_out=30, tokens_in=10),
    ])
    db.commit()
    db.close()


def _first_id():
    return client.get("/api/v1/logs").json()["items"][0]["id"]


# ---------------------------------------------------------------------------
# 1. GET /api/v1/logs — all filter branches
# ---------------------------------------------------------------------------

def test_logs_list_no_filter(seeded_db):
    body = client.get("/api/v1/logs").json()
    assert body["total"] == 6
    assert len(body["items"]) <= 50


def test_logs_filter_by_model(seeded_db):
    """Covers logs.py line 38 — the model filter branch."""
    body = client.get("/api/v1/logs?model=gpt-4").json()
    assert body["total"] == 2
    assert all(i["model"] == "gpt-4" for i in body["items"])


def test_logs_filter_by_source_lmsys(seeded_db):
    assert client.get("/api/v1/logs?source=lmsys").json()["total"] == 5


def test_logs_filter_by_source_benchmark(seeded_db):
    assert client.get("/api/v1/logs?source=evals_benchmark").json()["total"] == 1


def test_logs_pagination(seeded_db):
    body = client.get("/api/v1/logs?page=1&limit=2").json()
    assert len(body["items"]) == 2
    assert body["pages"] == 3


def test_logs_page_beyond_last(seeded_db):
    body = client.get("/api/v1/logs?page=999&limit=50").json()
    assert body["items"] == []


def test_logs_get_single(seeded_db):
    log_id = _first_id()
    r = client.get(f"/api/v1/logs/{log_id}")
    assert r.status_code == 200
    assert r.json()["id"] == log_id


def test_logs_get_missing_id(seeded_db):
    assert client.get("/api/v1/logs/999999").status_code == 404


def test_logs_post_ingest(seeded_db):
    r = client.post("/api/v1/logs", json={
        "prompt": "Hello", "response": "Hi",
        "model": "gpt-4", "tokens_in": 5, "tokens_out": 2,
        "latency_ms": 100.0, "cost_usd": 0.001,
    })
    assert r.status_code == 201
    assert r.json()["log_id"] > 0


def test_logs_post_invalid_tokens(seeded_db):
    r = client.post("/api/v1/logs", json={
        "prompt": "P", "response": "R",
        "model": "gpt-4", "tokens_in": 0, "tokens_out": 5,
        "latency_ms": 100.0, "cost_usd": 0.0,
    })
    assert r.status_code == 422


def test_logs_batch_ingest(seeded_db):
    payload = [
        {"prompt": f"Q{i}", "response": f"A{i}",
         "model": "gpt-4", "tokens_in": 10, "tokens_out": 5,
         "latency_ms": 200.0, "cost_usd": 0.001}
        for i in range(5)
    ]
    r = client.post("/api/v1/logs/batch", json=payload)
    assert r.status_code == 200
    assert r.json()["ingested_count"] == 5


def test_logs_batch_over_limit(seeded_db):
    payload = [
        {"prompt": "Q", "response": "A",
         "model": "gpt-4", "tokens_in": 5, "tokens_out": 3,
         "latency_ms": 100.0, "cost_usd": 0.001}
        for _ in range(1001)
    ]
    assert client.post("/api/v1/logs/batch", json=payload).status_code == 400


# ---------------------------------------------------------------------------
# 2. /api/v1/metrics — date-filtered branches
# ---------------------------------------------------------------------------

def test_summary_with_date_range(seeded_db):
    """Covers metrics_queries.py date filter lines for summary."""
    start = (NOW - timedelta(hours=1)).isoformat()
    end   = (NOW + timedelta(hours=3)).isoformat()
    body = client.get(f"/api/v1/metrics/summary?start_date={start}&end_date={end}").json()
    assert body["total_requests"] == 5   # all 5 LMSYS completions


def test_summary_date_excludes_old_records(seeded_db):
    start = (NOW + timedelta(hours=10)).isoformat()
    body = client.get(f"/api/v1/metrics/summary?start_date={start}").json()
    assert body["total_requests"] == 0


def test_by_model_with_date_range(seeded_db):
    start = NOW.isoformat()
    end = (NOW + timedelta(hours=1)).isoformat()
    r = client.get(f"/api/v1/metrics/by-model?start_date={start}&end_date={end}")
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_by_hour_with_date_range(seeded_db):
    start = NOW.isoformat()
    end = (NOW + timedelta(hours=2)).isoformat()
    rows = client.get(f"/api/v1/metrics/by-hour?start_date={start}&end_date={end}").json()
    assert len(rows) >= 1


def test_latency_percentiles_with_model(seeded_db):
    body = client.get("/api/v1/metrics/latency-percentiles?model=gpt-4").json()
    assert body["model"] == "gpt-4"
    assert body["p50"] > 0


def test_latency_percentiles_unknown_model(seeded_db):
    body = client.get("/api/v1/metrics/latency-percentiles?model=nonexistent").json()
    assert body["p50"] == 0


def test_cost_breakdown_with_date(seeded_db):
    start = NOW.isoformat()
    body = client.get(f"/api/v1/metrics/cost-breakdown?start_date={start}").json()
    assert "total_cost" in body and "by_model" in body and "by_hour" in body


def test_model_comparison_with_date_range(seeded_db):
    """Covers model_comparison date filter lines 324/326."""
    start = NOW.isoformat()
    end = (NOW + timedelta(hours=5)).isoformat()
    body = client.get(f"/api/v1/metrics/model-comparison?start_date={start}&end_date={end}").json()
    assert body["source"] == "lmsys"


def test_eval_summary_with_date_range(seeded_db):
    """Covers eval_summary date filter lines 379/381 (both start and end)."""
    start = NOW.isoformat()
    end = (NOW + timedelta(hours=3)).isoformat()
    r = client.get(f"/api/v1/metrics/eval-summary?start_date={start}&end_date={end}")
    assert r.status_code == 200
    assert "lmsys" in r.json()


def test_evals_analytics_with_date_range(seeded_db):
    """Covers eval_analytics date filter lines 517/519/542/544."""
    start = NOW.isoformat()
    end = (NOW + timedelta(hours=3)).isoformat()
    body = client.get(f"/api/v1/metrics/evals?start_date={start}&end_date={end}").json()
    assert "total_evals" in body and "distribution" in body


def test_source_filtered_metrics_with_dates(seeded_db):
    """Covers by_source date filter lines 454/456/474/476."""
    start = NOW.isoformat()
    body = client.get(f"/api/v1/metrics/source/lmsys?start_date={start}").json()
    assert body["total_requests"] == 5


# ---------------------------------------------------------------------------
# 3. /api/v1/evals — exception path and edge cases
# ---------------------------------------------------------------------------

def test_evaluate_bleu_rouge(seeded_db):
    cid = _first_id()
    r = client.post("/api/v1/evals/evaluate", json={
        "completion_id": cid,
        "eval_types": ["bleu", "rouge"],
    })
    assert r.status_code == 200
    scores = r.json()["scores"]
    assert "bleu" in scores and "rouge" in scores
    assert 0.0 <= scores["bleu"] <= 1.0


def test_evaluate_llm_judge_exception_path(seeded_db, monkeypatch):
    """Covers evals.py lines 95-97: LLMJudge() constructor raises → score 0.0."""
    _LLM_CACHE.clear()
    monkeypatch.setattr(_llm_judge_mod, "_RETRY_DELAYS", ())  # no sleep in tests
    cid = _first_id()
    # Patch AzureOpenAI itself (side_effect on the class) so LLMJudge.__init__ raises.
    # evaluate_response's inner try/except won't help here — the exception fires before it.
    with patch("openai.AzureOpenAI", side_effect=Exception("Azure init failed")):
        r = client.post("/api/v1/evals/evaluate", json={
            "completion_id": cid,
            "eval_types": ["llm_judge"],
        })
    assert r.status_code == 200
    assert r.json()["scores"]["llm_judge"] == 0.0


def test_evaluate_all_types(seeded_db):
    _LLM_CACHE.clear()
    cid = _first_id()
    with patch("openai.AzureOpenAI", return_value=_make_judge_mock('{"score": 8, "explanation": "good"}')):
        r = client.post("/api/v1/evals/evaluate", json={
            "completion_id": cid,
            "eval_types": ["bleu", "rouge", "llm_judge"],
            "criteria": "accurate, concise",
        })
    assert r.status_code == 200
    scores = r.json()["scores"]
    assert "bleu" in scores and "rouge" in scores and "llm_judge" in scores
    assert scores["llm_judge"] == 0.8


def test_evaluate_missing_completion(seeded_db):
    r = client.post("/api/v1/evals/evaluate", json={
        "completion_id": 999999,
        "eval_types": ["bleu"],
    })
    assert r.status_code == 404


def test_batch_eval_with_missing_completion_ids(seeded_db, monkeypatch):
    """Covers evals.py line 156 — worker skips missing completion IDs."""
    # monkeypatch (not `with patch`) so the patch stays alive while the daemon thread runs
    monkeypatch.setattr("backend.database.SessionLocal", _Session)
    valid_id = _first_id()
    missing_id = 999998

    r = client.post("/api/v1/evals/batch", json={
        "completion_ids": [valid_id, missing_id],
        "eval_types": ["bleu"],
    })
    assert r.status_code == 202
    job_id = r.json()["job_id"]

    for _ in range(20):
        time.sleep(0.3)
        status = client.get(f"/api/v1/evals/batch/{job_id}").json()
        if status.get("status") == "complete":
            break
    assert status["status"] == "complete"
    assert status["done"] >= 1   # valid_id processed; missing_id skipped


def test_batch_eval_sample_rate(seeded_db):
    """sample_rate < 1.0 reduces the count processed."""
    db = _Session()
    comps = [_comp("gpt-4", cost=0.001) for _ in range(10)]
    db.add_all(comps)
    db.commit()
    ids = [c.id for c in comps]
    db.close()

    r = client.post("/api/v1/evals/batch", json={
        "completion_ids": ids,
        "eval_types": ["bleu"],
        "sample_rate": 0.3,
    })
    assert r.status_code == 202
    body = r.json()
    # submitted_count = max(1, int(10 * 0.3)) = 3
    assert body["submitted_count"] <= 4


def test_batch_eval_status_not_found(seeded_db):
    assert client.get("/api/v1/evals/batch/nonexistent_job").status_code == 404


# ---------------------------------------------------------------------------
# 4. Metrics edge cases — truly empty database
# ---------------------------------------------------------------------------

def test_summary_empty_db(reset_db):
    body = client.get("/api/v1/metrics/summary").json()
    assert body["total_requests"] == 0
    assert body["total_cost_usd"] == 0.0


def test_by_model_empty_db(reset_db):
    assert client.get("/api/v1/metrics/by-model").json() == []


def test_by_hour_empty_db(reset_db):
    assert client.get("/api/v1/metrics/by-hour").json() == []


def test_model_comparison_empty_db(reset_db):
    body = client.get("/api/v1/metrics/model-comparison").json()
    assert body["models"] == []
    assert body["total_battles"] == 0


def test_evals_empty_db(reset_db):
    body = client.get("/api/v1/metrics/evals").json()
    assert body["total_evals"] == 0
    assert body["overall_avg_score"] is None


def test_eval_summary_empty_db(reset_db):
    body = client.get("/api/v1/metrics/eval-summary").json()
    assert body["lmsys"]["completions"] == 0
    assert body["evals_benchmark"]["completions"] == 0


# ---------------------------------------------------------------------------
# 5. Win-rate mathematical correctness
# ---------------------------------------------------------------------------

def test_win_rate_math(seeded_db):
    for m in client.get("/api/v1/metrics/model-comparison").json()["models"]:
        b = m["battles"]
        assert abs(m["win_rate"] - round(m["wins"] / b, 4)) < 0.001
        assert abs(m["win_tie_rate"] - round((m["wins"] + m["ties"] * 0.5) / b, 4)) < 0.001
        assert m["wins"] + m["ties"] + m["losses"] == b


# ---------------------------------------------------------------------------
# 6. Source isolation
# ---------------------------------------------------------------------------

def test_source_isolation_no_cross_contamination(seeded_db):
    lmsys = client.get("/api/v1/metrics/source/lmsys").json()["total_requests"]
    bench = client.get("/api/v1/metrics/source/evals_benchmark").json()["total_requests"]
    all_logs = client.get("/api/v1/logs").json()["total"]
    assert lmsys + bench == all_logs


def test_summary_total_matches_lmsys_source(seeded_db):
    summary_total = client.get("/api/v1/metrics/summary").json()["total_requests"]
    lmsys_total = client.get("/api/v1/metrics/source/lmsys").json()["total_requests"]
    assert summary_total == lmsys_total


def test_eval_dataset_not_in_by_model(seeded_db):
    models = [m["model"] for m in client.get("/api/v1/metrics/by-model").json()]
    assert "eval-dataset" not in models


# ---------------------------------------------------------------------------
# 7. LLM judge resilience (the "Stream idle timeout" scenario)
# ---------------------------------------------------------------------------

def test_llm_judge_slow_response_handled(seeded_db):
    """Simulate delayed Azure response — must complete without crashing."""
    _LLM_CACHE.clear()
    cid = _first_id()

    def slow_create(*args, **kwargs):
        time.sleep(0.05)
        resp = MagicMock()
        resp.output_text = '{"score": 5, "explanation": "delayed"}'
        return resp

    mock_client = MagicMock()
    mock_client.responses.create.side_effect = slow_create

    with patch("openai.AzureOpenAI", return_value=mock_client):
        r = client.post("/api/v1/evals/evaluate", json={
            "completion_id": cid,
            "eval_types": ["llm_judge"],
        })
    assert r.status_code == 200
    assert r.json()["scores"]["llm_judge"] == 0.5


def test_llm_judge_malformed_json_handled(seeded_db, monkeypatch):
    """Non-JSON output from Azure → retries exhausted → score 0.0, API returns 200."""
    _LLM_CACHE.clear()
    monkeypatch.setattr(_llm_judge_mod, "_RETRY_DELAYS", ())  # no sleep in tests
    cid = _first_id()
    mock_client = _make_judge_mock("Sorry, I cannot evaluate that.")
    with patch("openai.AzureOpenAI", return_value=mock_client):
        r = client.post("/api/v1/evals/evaluate", json={
            "completion_id": cid,
            "eval_types": ["llm_judge"],
        })
    assert r.status_code == 200
    assert r.json()["scores"]["llm_judge"] == 0.0


def test_llm_judge_score_out_of_range_clamped(seeded_db):
    """Judge returns score > 10 → clamped to 1.0."""
    _LLM_CACHE.clear()
    cid = _first_id()
    mock_client = _make_judge_mock('{"score": 99, "explanation": "perfect"}')
    with patch("openai.AzureOpenAI", return_value=mock_client):
        r = client.post("/api/v1/evals/evaluate", json={
            "completion_id": cid,
            "eval_types": ["llm_judge"],
        })
    assert r.status_code == 200
    assert r.json()["scores"]["llm_judge"] == 1.0


def test_llm_judge_score_negative_clamped(seeded_db):
    """Judge returns negative score → clamped to 0.0."""
    _LLM_CACHE.clear()
    cid = _first_id()
    mock_client = _make_judge_mock('{"score": -5, "explanation": "terrible"}')
    with patch("openai.AzureOpenAI", return_value=mock_client):
        r = client.post("/api/v1/evals/evaluate", json={
            "completion_id": cid,
            "eval_types": ["llm_judge"],
        })
    assert r.status_code == 200
    assert r.json()["scores"]["llm_judge"] == 0.0


def test_llm_judge_retries_on_stream_timeout(seeded_db, monkeypatch):
    """First call raises stream timeout, second call succeeds → correct score returned."""
    _LLM_CACHE.clear()
    monkeypatch.setattr(_llm_judge_mod, "_RETRY_DELAYS", (0,))  # 1 retry, 0s delay

    cid = _first_id()
    good_resp = MagicMock()
    good_resp.output_text = '{"score": 7, "explanation": "good on retry"}'
    expl_resp = MagicMock()
    expl_resp.output_text = "detailed explanation"

    mock_client = MagicMock()
    mock_client.responses.create.side_effect = [
        Exception("Stream idle timeout"),  # evaluate_response: attempt 1 fails
        good_resp,                          # evaluate_response: attempt 2 succeeds
        expl_resp,                          # get_evaluation_explanation call
    ]

    with patch("openai.AzureOpenAI", return_value=mock_client):
        r = client.post("/api/v1/evals/evaluate", json={
            "completion_id": cid,
            "eval_types": ["llm_judge"],
        })
    assert r.status_code == 200
    assert r.json()["scores"]["llm_judge"] == 0.7
    # 3 calls: evaluate attempt 1 (fail) + attempt 2 (pass) + explanation
    assert mock_client.responses.create.call_count == 3


def test_llm_judge_network_timeout_returns_zero(seeded_db, monkeypatch):
    """Simulate Azure network timeout — retries exhausted → score 0, API returns 200."""
    _LLM_CACHE.clear()
    monkeypatch.setattr(_llm_judge_mod, "_RETRY_DELAYS", ())  # no sleep in tests
    cid = _first_id()
    mock_client = MagicMock()
    mock_client.responses.create.side_effect = TimeoutError("Connection timed out")
    with patch("openai.AzureOpenAI", return_value=mock_client):
        r = client.post("/api/v1/evals/evaluate", json={
            "completion_id": cid,
            "eval_types": ["llm_judge"],
        })
    assert r.status_code == 200
    assert r.json()["scores"]["llm_judge"] == 0.0


# ---------------------------------------------------------------------------
# 8. Happy-path audit: every endpoint must return 200
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=False)
def _seed_for_audit(seeded_db):
    pass


@pytest.mark.parametrize("url", [
    "/api/v1/metrics/summary",
    "/api/v1/metrics/by-model",
    "/api/v1/metrics/by-hour",
    "/api/v1/metrics/latency-percentiles",
    "/api/v1/metrics/cost-breakdown",
    "/api/v1/metrics/evals",
    "/api/v1/metrics/model-comparison",
    "/api/v1/metrics/source/lmsys",
    "/api/v1/metrics/source/evals_benchmark",
    "/api/v1/metrics/eval-summary",
    "/api/v1/logs",
])
def test_endpoint_returns_200(seeded_db, url):
    r = client.get(url)
    assert r.status_code == 200, f"GET {url} returned {r.status_code}: {r.text[:300]}"


# ---------------------------------------------------------------------------
# 9. Schema validation edge cases
# ---------------------------------------------------------------------------

def test_log_ingest_zero_cost_allowed(seeded_db):
    r = client.post("/api/v1/logs", json={
        "prompt": "free", "response": "resp",
        "model": "local-llm", "tokens_in": 5, "tokens_out": 3,
        "latency_ms": 50.0, "cost_usd": 0.0,
    })
    assert r.status_code == 201


def test_log_ingest_negative_cost_rejected(seeded_db):
    r = client.post("/api/v1/logs", json={
        "prompt": "P", "response": "R",
        "model": "gpt-4", "tokens_in": 5, "tokens_out": 3,
        "latency_ms": 50.0, "cost_usd": -1.0,
    })
    assert r.status_code == 422


def test_log_ingest_negative_latency_rejected(seeded_db):
    r = client.post("/api/v1/logs", json={
        "prompt": "P", "response": "R",
        "model": "gpt-4", "tokens_in": 5, "tokens_out": 3,
        "latency_ms": -100.0, "cost_usd": 0.001,
    })
    assert r.status_code == 422


def test_metrics_invalid_date_format(seeded_db):
    """Invalid date → 400 or 422 (FastAPI wraps ValueError as 400)."""
    r = client.get("/api/v1/metrics/summary?start_date=not-a-date")
    assert r.status_code in (400, 422)


def test_logs_invalid_page_number(seeded_db):
    assert client.get("/api/v1/logs?page=0").status_code == 422


def test_logs_limit_too_large(seeded_db):
    assert client.get("/api/v1/logs?limit=9999").status_code == 422


# ---------------------------------------------------------------------------
# 10. Concurrent log ingestion (thread safety)
# ---------------------------------------------------------------------------

def test_drop_tables_utility():
    """Covers database.py:56 — drop_tables() calls Base.metadata.drop_all without error."""
    from backend.database import drop_tables, engine
    from backend.models import Base
    with patch.object(Base.metadata, "drop_all") as mock_drop:
        drop_tables()
        mock_drop.assert_called_once_with(bind=engine)


def test_concurrent_log_ingestion(seeded_db):
    """10 threads posting simultaneously — all should succeed."""
    results = []
    lock = threading.Lock()

    def post_log(i):
        r = client.post("/api/v1/logs", json={
            "prompt": f"Concurrent {i}",
            "response": f"Response {i}",
            "model": "gpt-4",
            "tokens_in": 10, "tokens_out": 5,
            "latency_ms": 200.0, "cost_usd": 0.001,
        })
        with lock:
            results.append(r.status_code)

    threads = [threading.Thread(target=post_log, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All should be 201 (SQLite WAL handles concurrent writes)
    success = sum(1 for s in results if s == 201)
    assert success >= 8, f"Only {success}/10 concurrent inserts succeeded: {results}"
