"""
Unit tests for Pydantic schemas.
"""
import pytest
from pydantic import ValidationError

from backend.schemas import CompletionLog, EvalResult, MetricsQuery


VALID_LOG = dict(
    prompt="What is 2+2?",
    response="4",
    model="claude-sonnet-4-6",
    tokens_in=10,
    tokens_out=5,
    latency_ms=123.4,
    cost_usd=0.0005,
)


class TestCompletionLog:
    def test_valid(self):
        log = CompletionLog(**VALID_LOG)
        assert log.tokens_in == 10
        assert log.user_id is None

    def test_optional_fields(self):
        log = CompletionLog(**{**VALID_LOG, "user_id": "u1", "conversation_id": "c1"})
        assert log.user_id == "u1"
        assert log.conversation_id == "c1"

    def test_negative_tokens_in_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            CompletionLog(**{**VALID_LOG, "tokens_in": -1})
        assert "tokens_in" in str(exc_info.value)

    def test_zero_tokens_in_rejected(self):
        with pytest.raises(ValidationError):
            CompletionLog(**{**VALID_LOG, "tokens_in": 0})

    def test_negative_tokens_out_rejected(self):
        with pytest.raises(ValidationError):
            CompletionLog(**{**VALID_LOG, "tokens_out": -5})

    def test_zero_tokens_out_rejected(self):
        with pytest.raises(ValidationError):
            CompletionLog(**{**VALID_LOG, "tokens_out": 0})

    def test_negative_cost_rejected(self):
        with pytest.raises(ValidationError):
            CompletionLog(**{**VALID_LOG, "cost_usd": -0.01})

    def test_zero_cost_accepted(self):
        log = CompletionLog(**{**VALID_LOG, "cost_usd": 0.0})
        assert log.cost_usd == 0.0

    def test_negative_latency_rejected(self):
        with pytest.raises(ValidationError):
            CompletionLog(**{**VALID_LOG, "latency_ms": -1.0})

    def test_zero_latency_rejected(self):
        with pytest.raises(ValidationError):
            CompletionLog(**{**VALID_LOG, "latency_ms": 0.0})

    def test_missing_required_field(self):
        data = {k: v for k, v in VALID_LOG.items() if k != "model"}
        with pytest.raises(ValidationError):
            CompletionLog(**data)


class TestEvalResult:
    def test_valid(self):
        ev = EvalResult(completion_id=1, eval_type="bleu", score=0.75)
        assert ev.score == 0.75

    def test_score_above_one_rejected(self):
        with pytest.raises(ValidationError):
            EvalResult(completion_id=1, eval_type="bleu", score=1.5)

    def test_score_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            EvalResult(completion_id=1, eval_type="bleu", score=-0.1)

    def test_invalid_eval_type(self):
        with pytest.raises(ValidationError):
            EvalResult(completion_id=1, eval_type="unknown_type", score=0.5)

    def test_boundary_scores(self):
        assert EvalResult(completion_id=1, eval_type="rouge", score=0.0).score == 0.0
        assert EvalResult(completion_id=1, eval_type="rouge", score=1.0).score == 1.0


class TestMetricsQuery:
    def test_all_optional(self):
        q = MetricsQuery()
        assert q.start_date is None
        assert q.model is None

    def test_with_values(self):
        from datetime import datetime
        q = MetricsQuery(model="gpt-4o", user_id="u42")
        assert q.model == "gpt-4o"
