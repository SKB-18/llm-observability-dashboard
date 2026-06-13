"""
Tests for dual-source data strategy:
- LMSYS source: production metrics, win rates, human_preference evals
- evals_benchmark source: quality scores (BLEU, ROUGE, human)
- Source isolation: no cross-contamination in aggregates
- New endpoints: /metrics/model-comparison, /metrics/source/{source}, /metrics/eval-summary
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Completion, EvalResult
from tests.conftest import _Session

client = TestClient(app)

NOW = datetime(2024, 6, 11, 12, 0, 0)


def _lmsys(model_a, model_b, winner, latency=500.0, cost=0.005):
    """Create a pair of LMSYS completions (one per model) with human_preference evals."""
    score_a = 1.0 if winner == "model_a" else (0.5 if winner == "tie" else 0.0)
    score_b = 1.0 if winner == "model_b" else (0.5 if winner == "tie" else 0.0)
    return [
        (
            Completion(
                prompt=f"Arena {model_a} vs {model_b}",
                response=f"Winner: {winner}",
                model=model_a, tokens_in=100, tokens_out=50,
                latency_ms=latency, cost_usd=cost,
                timestamp=NOW, source="lmsys",
            ),
            score_a,
        ),
        (
            Completion(
                prompt=f"Arena {model_a} vs {model_b}",
                response=f"Winner: {winner}",
                model=model_b, tokens_in=100, tokens_out=50,
                latency_ms=latency * 0.9, cost_usd=cost * 0.8,
                timestamp=NOW, source="lmsys",
            ),
            score_b,
        ),
    ]


def _bench(prompt, response, bleu=0.3, rouge=0.4, human=0.8):
    """Create a benchmark completion with quality eval results."""
    return (
        Completion(
            prompt=prompt, response=response,
            model="eval-dataset", tokens_in=20, tokens_out=30,
            latency_ms=0.0, cost_usd=0.0,
            timestamp=NOW, source="evals_benchmark",
        ),
        [("bleu", bleu), ("rouge", rouge), ("human", human)],
    )


@pytest.fixture(autouse=True)
def seed_dual(reset_db):
    db = _Session()
    try:
        # 3 LMSYS battles: gpt-4 wins 2, claude wins 1, 1 tie
        pairs = [
            *_lmsys("gpt-4", "claude-3-opus", "model_a"),   # gpt-4 wins
            *_lmsys("gpt-4", "claude-3-opus", "model_a"),   # gpt-4 wins again
            *_lmsys("gpt-4", "claude-3-opus", "model_b"),   # claude wins
            *_lmsys("gpt-4", "llama-2-70b",   "tie"),       # tie
        ]
        for comp, score in pairs:
            db.add(comp)
            db.flush()
            db.add(EvalResult(
                completion_id=comp.id,
                eval_type="human_preference",
                score=score,
                source="human_preference",
            ))

        # 2 benchmark items
        bench_items = [
            _bench("What is ML?", "Machine learning is...", bleu=0.2, rouge=0.3, human=0.8),
            _bench("Explain AI?", "AI stands for...",       bleu=0.1, rouge=0.2, human=0.6),
        ]
        for comp, evals in bench_items:
            db.add(comp)
            db.flush()
            for et, score in evals:
                db.add(EvalResult(
                    completion_id=comp.id,
                    eval_type=et,
                    score=score,
                    source="benchmark",
                ))

        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Source isolation: summary / by-model must exclude evals_benchmark
# ---------------------------------------------------------------------------

def test_summary_excludes_benchmark():
    """Summary counts only LMSYS completions."""
    resp = client.get("/api/v1/metrics/summary")
    assert resp.status_code == 200
    body = resp.json()
    # 4 battles × 2 models = 8 LMSYS completions; 2 benchmark completions excluded
    assert body["total_requests"] == 8
    # eval-dataset model must NOT appear in the models list
    assert "eval-dataset" not in body["models"]


def test_by_model_excludes_benchmark():
    """by-model must not include the eval-dataset model."""
    resp = client.get("/api/v1/metrics/by-model")
    assert resp.status_code == 200
    models = [m["model"] for m in resp.json()]
    assert "eval-dataset" not in models
    # LMSYS models are present
    assert "gpt-4" in models


# ---------------------------------------------------------------------------
# /metrics/model-comparison — LMSYS win rates
# ---------------------------------------------------------------------------

def test_model_comparison_returns_win_rates():
    resp = client.get("/api/v1/metrics/model-comparison")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "lmsys"
    assert "models" in body
    assert body["total_battles"] > 0

    by_model = {m["model"]: m for m in body["models"]}
    assert "gpt-4" in by_model
    gpt4 = by_model["gpt-4"]
    assert gpt4["wins"] == 2       # won 2 of 3 vs claude, plus tie vs llama
    assert gpt4["ties"] == 1
    assert gpt4["losses"] == 1
    assert 0 <= gpt4["win_rate"] <= 1
    assert 0 <= gpt4["win_tie_rate"] <= 1


def test_model_comparison_sorted_by_win_tie_rate():
    """Models are returned sorted by win_tie_rate descending."""
    resp = client.get("/api/v1/metrics/model-comparison")
    models = resp.json()["models"]
    rates = [m["win_tie_rate"] for m in models]
    assert rates == sorted(rates, reverse=True)


def test_model_comparison_benchmark_model_excluded():
    """eval-dataset must not appear in model-comparison results."""
    resp = client.get("/api/v1/metrics/model-comparison")
    models = [m["model"] for m in resp.json()["models"]]
    assert "eval-dataset" not in models


# ---------------------------------------------------------------------------
# /metrics/source/{source}
# ---------------------------------------------------------------------------

def test_source_lmsys():
    resp = client.get("/api/v1/metrics/source/lmsys")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "lmsys"
    assert body["total_requests"] == 8
    assert body["model_count"] == 3   # gpt-4, claude-3-opus, llama-2-70b


def test_source_evals_benchmark():
    resp = client.get("/api/v1/metrics/source/evals_benchmark")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "evals_benchmark"
    assert body["total_requests"] == 2


def test_source_unknown_returns_empty():
    resp = client.get("/api/v1/metrics/source/nonexistent_source")
    assert resp.status_code == 200
    assert resp.json()["total_requests"] == 0


# ---------------------------------------------------------------------------
# /metrics/eval-summary — side-by-side view
# ---------------------------------------------------------------------------

def test_eval_summary_structure():
    resp = client.get("/api/v1/metrics/eval-summary")
    assert resp.status_code == 200
    body = resp.json()
    assert "lmsys" in body
    assert "evals_benchmark" in body


def test_eval_summary_lmsys_counts():
    body = client.get("/api/v1/metrics/eval-summary").json()
    lmsys = body["lmsys"]
    assert lmsys["completions"] == 8
    assert lmsys["human_preference_evals"] == 8
    assert lmsys["models"] == 3


def test_eval_summary_benchmark_quality():
    body = client.get("/api/v1/metrics/eval-summary").json()
    bench = body["evals_benchmark"]
    assert bench["completions"] == 2
    qs = bench["quality_scores"]
    assert "bleu" in qs
    assert "rouge" in qs
    assert "human" in qs
    # bleu avg = (0.2+0.1)/2 = 0.15
    assert abs(qs["bleu"]["avg"] - 0.15) < 0.01
    # human avg = (0.8+0.6)/2 = 0.7
    assert abs(qs["human"]["avg"] - 0.7) < 0.01


# ---------------------------------------------------------------------------
# /api/v1/logs with source filter
# ---------------------------------------------------------------------------

def test_logs_source_filter_lmsys():
    resp = client.get("/api/v1/logs?source=lmsys")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 8
    assert all(i["model"] != "eval-dataset" for i in body["items"])


def test_logs_source_filter_benchmark():
    resp = client.get("/api/v1/logs?source=evals_benchmark")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert all(i["model"] == "eval-dataset" for i in body["items"])


def test_logs_no_source_filter_returns_all():
    resp = client.get("/api/v1/logs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 10   # 8 lmsys + 2 benchmark


# ---------------------------------------------------------------------------
# /metrics/evals — eval analytics uses both sources' evals
# ---------------------------------------------------------------------------

def test_evals_analytics_includes_human_preference():
    resp = client.get("/api/v1/metrics/evals")
    assert resp.status_code == 200
    body = resp.json()
    types = {t["eval_type"] for t in body["by_type"]}
    assert "human_preference" in types


def test_evals_analytics_includes_benchmark_types():
    resp = client.get("/api/v1/metrics/evals")
    body = resp.json()
    types = {t["eval_type"] for t in body["by_type"]}
    assert "bleu" in types
    assert "rouge" in types
    assert "human" in types


def test_win_rates_in_evals_endpoint():
    """The /metrics/evals endpoint includes win_rates from LMSYS."""
    resp = client.get("/api/v1/metrics/evals")
    body = resp.json()
    assert "win_rates" in body
    models = [w["model"] for w in body["win_rates"]]
    assert "gpt-4" in models
