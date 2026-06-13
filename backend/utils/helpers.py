"""
Shared utility functions used across the backend.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

# Cost per 1 000 tokens in USD – (input_cost, output_cost)
_MODEL_COSTS: dict[str, tuple[float, float]] = {
    "claude-3-5-sonnet":         (0.003,  0.015),
    "claude-3-5-sonnet-20241022": (0.003,  0.015),
    "claude-3-opus":             (0.015,  0.075),
    "claude-haiku-4-5-20251001": (0.00025, 0.00125),
    "claude-sonnet-4-6":         (0.003,  0.015),
    "gpt-4":                     (0.03,   0.06),
    "gpt-4-turbo":               (0.01,   0.03),
    "gpt-3.5-turbo":             (0.0005, 0.0015),
    "gemini-pro":                (0.0005, 0.0015),
    "llama-2-70b":               (0.0,    0.0),
    "mistral-large":             (0.0,    0.0),
    "palm-2":                    (0.001,  0.002),
    "davinci-003":               (0.002,  0.002),
}
_DEFAULT_COST = (0.001, 0.002)


def calculate_cost(tokens_in: int, tokens_out: int, model: str) -> float:
    """
    Estimate USD cost for a completion.

    Uses per-model pricing table; falls back to a generic rate for unknown models.
    """
    in_rate, out_rate = _MODEL_COSTS.get(model.lower(), _DEFAULT_COST)
    cost = (tokens_in / 1000) * in_rate + (tokens_out / 1000) * out_rate
    return round(cost, 8)


def estimate_tokens(text: str) -> int:
    """
    Rough token count estimate: ~4 characters per token (OpenAI rule of thumb).
    Returns at least 1.
    """
    return max(1, len(text) // 4)


def parse_iso_date(date_str: str) -> datetime:
    """
    Parse an ISO-8601 datetime string.

    Handles both Z-suffix and +00:00 offsets, and naive datetimes.
    """
    cleaned = date_str.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        # Last-resort: strip timezone info and parse as naive
        return datetime.fromisoformat(cleaned[:19])


def generate_request_id() -> str:
    """Return a UUID4 string suitable for request tracing."""
    return str(uuid.uuid4())
