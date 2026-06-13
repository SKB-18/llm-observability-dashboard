"""
Tests for evaluation engine and /api/v1/evals endpoints.
All Anthropic API calls are mocked so no real credentials are needed.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Completion
from tests.conftest import _Session

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_db(reset_db):
    db = _Session()
    db.add(Completion(
        id=1,
        prompt="What is the capital of France?",
        response="The capital of France is Paris.",
        model="gpt-4",
        tokens_in=10,
        tokens_out=8,
        latency_ms=200.0,
        cost_usd=0.001,
    ))
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# TextMetrics unit tests
# ---------------------------------------------------------------------------

def test_bleu_score():
    from backend.evals.text_metrics import TextMetrics
    score = TextMetrics.bleu_score(
        "The capital of France is Paris.",
        "Paris is the capital of France.",
    )
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_bleu_non_trivial():
    from backend.evals.text_metrics import TextMetrics
    # Identical text should score higher than clearly different text
    same = TextMetrics.bleu_score("hello world", "hello world")
    diff = TextMetrics.bleu_score("hello world", "completely unrelated text here")
    assert same > diff


def test_bleu_empty_candidate():
    from backend.evals.text_metrics import TextMetrics
    score = TextMetrics.bleu_score("reference text here", "")
    assert score == 0.0


def test_rouge_score():
    from backend.evals.text_metrics import TextMetrics
    result = TextMetrics.rouge_score(
        "The capital of France is Paris.",
        "Paris is the capital of France.",
    )
    assert "rouge1" in result
    assert "rougeL" in result
    assert 0.0 <= result["rouge1"] <= 1.0
    assert 0.0 <= result["rougeL"] <= 1.0


def test_rouge_identical():
    from backend.evals.text_metrics import TextMetrics
    result = TextMetrics.rouge_score("same text", "same text")
    assert result["rouge1"] == 1.0
    assert result["rougeL"] == 1.0


def test_similarity_score():
    from backend.evals.text_metrics import TextMetrics
    score = TextMetrics.similarity_score("Paris is in France", "France contains Paris")
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_similarity_identical():
    from backend.evals.text_metrics import TextMetrics
    score = TextMetrics.similarity_score("hello", "hello")
    assert score == 1.0


def test_similarity_empty():
    from backend.evals.text_metrics import TextMetrics
    score = TextMetrics.similarity_score("", "")
    assert score == 1.0


# ---------------------------------------------------------------------------
# RuleEvaluator unit tests
# ---------------------------------------------------------------------------

def test_rule_engine_match():
    from backend.evals.rule_engine import RuleEvaluator
    ev = RuleEvaluator()
    ev.add_rule("has_greeting", r"\bhello\b", weight=1.0)
    ev.add_rule("has_number", r"\d+", weight=2.0)
    result = ev.evaluate("hello, there are 3 items")
    assert result["rule_matches"]["has_greeting"] is True
    assert result["rule_matches"]["has_number"] is True
    assert result["weighted_score"] == 1.0


def test_rule_engine_partial():
    from backend.evals.rule_engine import RuleEvaluator
    ev = RuleEvaluator()
    ev.add_rule("has_code", r"```", weight=1.0)
    ev.add_rule("has_link", r"https?://", weight=1.0)
    result = ev.evaluate("here is some code ```python``` block")
    assert result["rule_matches"]["has_code"] is True
    assert result["rule_matches"]["has_link"] is False
    assert result["weighted_score"] == 0.5


def test_rule_engine_empty():
    from backend.evals.rule_engine import RuleEvaluator
    ev = RuleEvaluator()
    assert ev.evaluate("anything")["weighted_score"] == 0.0


def test_rule_engine_no_matches():
    from backend.evals.rule_engine import RuleEvaluator
    ev = RuleEvaluator()
    ev.add_rule("has_table", r"\|.*\|", weight=1.0)
    assert ev.evaluate("no table here")["weighted_score"] == 0.0


# ---------------------------------------------------------------------------
# LLMJudge unit tests (mocked Azure OpenAI client)
# ---------------------------------------------------------------------------

def _mock_client(score_value=8, explanation="Good."):
    resp = MagicMock()
    resp.output_text = f'{{"score": {score_value}, "explanation": "{explanation}"}}'
    c = MagicMock()
    c.responses.create.return_value = resp
    return c


def test_llm_judge_scoring():
    from backend.evals.llm_judge import LLMJudge
    judge = LLMJudge.__new__(LLMJudge)
    judge._client = _mock_client(8)
    judge._model = "test"
    score = judge.evaluate_response("What is 2+2?", "4")
    assert isinstance(score, float)
    assert abs(score - 0.8) < 1e-6


def test_llm_judge_caching():
    from backend.evals.llm_judge import LLMJudge, _CACHE
    _CACHE.clear()
    judge = LLMJudge.__new__(LLMJudge)
    judge._client = _mock_client(7)
    judge._model = "test"
    s1 = judge.evaluate_response("p_unique1", "r_unique1", "c_unique1")
    s2 = judge.evaluate_response("p_unique1", "r_unique1", "c_unique1")
    assert s1 == s2
    assert judge._client.responses.create.call_count == 1
    _CACHE.clear()


def test_llm_judge_score_zero():
    from backend.evals.llm_judge import LLMJudge, _CACHE
    _CACHE.clear()
    judge = LLMJudge.__new__(LLMJudge)
    judge._client = _mock_client(0)
    judge._model = "test"
    assert judge.evaluate_response("p0", "r0") == 0.0
    _CACHE.clear()


def test_llm_judge_score_ten():
    from backend.evals.llm_judge import LLMJudge, _CACHE
    _CACHE.clear()
    judge = LLMJudge.__new__(LLMJudge)
    judge._client = _mock_client(10)
    judge._model = "test"
    assert judge.evaluate_response("p10", "r10") == 1.0
    _CACHE.clear()


def test_llm_judge_api_failure_returns_zero():
    from backend.evals.llm_judge import LLMJudge, _CACHE
    _CACHE.clear()
    judge = LLMJudge.__new__(LLMJudge)
    judge._client = MagicMock()
    judge._client.responses.create.side_effect = Exception("timeout")
    judge._model = "test"
    assert judge.evaluate_response("pfail", "rfail") == 0.0
    _CACHE.clear()


# ---------------------------------------------------------------------------
# /api/v1/evals/evaluate endpoint (mocked)
# ---------------------------------------------------------------------------

@patch("backend.routes.evals._run_evals")
def test_evaluate_endpoint(mock_run):
    mock_run.return_value = ({"bleu": 0.75, "rouge": 0.80}, "Looks good.")
    resp = client.post("/api/v1/evals/evaluate", json={
        "completion_id": 1,
        "eval_types": ["bleu", "rouge"],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["completion_id"] == 1
    assert "scores" in body
    assert "timestamp" in body


@patch("backend.routes.evals._run_evals")
def test_evaluate_not_found(mock_run):
    resp = client.post("/api/v1/evals/evaluate", json={
        "completion_id": 9999,
        "eval_types": ["bleu"],
    })
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /api/v1/evals/batch endpoint
# ---------------------------------------------------------------------------

@patch("backend.routes.evals._run_evals")
def test_batch_evaluate(mock_run):
    mock_run.return_value = ({"bleu": 0.7}, "")
    resp = client.post("/api/v1/evals/batch", json={
        "completion_ids": [1],
        "eval_types": ["bleu"],
    })
    assert resp.status_code == 202
    body = resp.json()
    assert body["submitted_count"] == 1
    assert body["status"] == "processing"
    assert body["job_id"].startswith("batch_")
