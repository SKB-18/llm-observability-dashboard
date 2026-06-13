"""
LLM Observer SDK – automatic logging for LLM API calls.

Quick start::

    from anthropic import Anthropic
    from llm_observer import LLMObserver

    observer = LLMObserver("http://localhost:8000")
    client = observer.wrap_claude_client(Anthropic())

    # Every call is now automatically logged:
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Hello!"}],
        max_tokens=200,
    )
"""
from __future__ import annotations

import functools
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fallback local log file used when the collector is unreachable
# ---------------------------------------------------------------------------
_FALLBACK_LOG = Path(os.getenv("LLM_OBSERVER_FALLBACK_LOG", "llm_observer_fallback.jsonl"))


def _write_fallback(payload: dict) -> None:
    """Append a JSON line to the fallback log file (thread-safe via append mode)."""
    try:
        with _FALLBACK_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception as exc:
        logging.getLogger(__name__).warning("[LLMObserver] fallback write failed: %s", exc)


# ---------------------------------------------------------------------------
# HTTP session with retry + timeout
# ---------------------------------------------------------------------------
def _build_session(retries: int = 3, backoff: float = 0.5) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[502, 503, 504],
        allowed_methods=["POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------
class LLMObserver:
    """Automatic logging for LLM completions.

    Args:
        collector_url: Base URL of the observability backend.
        api_key: Optional bearer token sent as ``Authorization: Bearer <key>``.
        timeout: HTTP request timeout in seconds (default 2 s – never block the app).
    """

    def __init__(
        self,
        collector_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 2.0,
    ) -> None:
        self._base = collector_url.rstrip("/")
        self._timeout = timeout
        self._session = _build_session()
        if api_key:
            self._session.headers["Authorization"] = f"Bearer {api_key}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_completion(
        self,
        prompt: str,
        response: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        latency_ms: float,
        cost_usd: float,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log a single LLM completion.

        Returns the server response dict, or a local fallback dict on failure.
        Never raises.
        """
        payload = {
            "prompt": prompt,
            "response": response,
            "model": model,
            "tokens_in": max(1, int(tokens_in)),
            "tokens_out": max(1, int(tokens_out)),
            "latency_ms": max(0.001, float(latency_ms)),
            "cost_usd": max(0.0, float(cost_usd)),
            "user_id": user_id,
            "conversation_id": conversation_id,
        }
        return self._post("/api/v1/logs", payload)

    def log_batch(self, completions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Log a batch of completions (up to 1 000).

        Returns the server response dict, or a local fallback dict on failure.
        Never raises.
        """
        return self._post("/api/v1/logs/batch", completions)

    def wrap_claude_client(self, client: Any) -> Any:
        """Transparently wrap an Anthropic client so every call is auto-logged.

        The original ``messages.create`` is replaced with a thin wrapper that:

        1. Calls the original method (same args/kwargs).
        2. Measures wall-clock latency.
        3. Extracts token counts from ``response.usage``.
        4. Calls :meth:`log_completion` in the background (does not block).
        5. Returns the original response unchanged.

        Args:
            client: An ``anthropic.Anthropic`` instance.

        Returns:
            The same client object, mutated in-place (also returned for chaining).
        """
        original_create = client.messages.create
        observer = self

        @functools.wraps(original_create)
        def _wrapped_create(*args, **kwargs):
            t0 = time.perf_counter()
            response = original_create(*args, **kwargs)
            latency_ms = (time.perf_counter() - t0) * 1000

            try:
                # Extract fields from the response
                model = getattr(response, "model", kwargs.get("model", "unknown"))
                usage = getattr(response, "usage", None)
                tokens_in  = getattr(usage, "input_tokens",  0) if usage else 0
                tokens_out = getattr(usage, "output_tokens", 0) if usage else 0

                # Best-effort prompt extraction
                messages = kwargs.get("messages") or (args[0] if args else [])
                prompt = " ".join(
                    m.get("content", "") if isinstance(m, dict) else str(m)
                    for m in messages
                )

                # Best-effort response text
                content = getattr(response, "content", [])
                response_text = " ".join(
                    getattr(c, "text", "") for c in content if hasattr(c, "text")
                )

                cost = _estimate_cost(tokens_in, tokens_out, model)

                observer.log_completion(
                    prompt=prompt,
                    response=response_text,
                    model=model,
                    tokens_in=max(1, tokens_in),
                    tokens_out=max(1, tokens_out),
                    latency_ms=latency_ms,
                    cost_usd=cost,
                )
            except Exception as exc:
                logger.warning("[LLMObserver] wrap_claude_client: failed to log: %s", exc)

            return response

        client.messages.create = _wrapped_create
        return client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _post(self, path: str, payload: Any) -> Dict[str, Any]:
        url = self._base + path
        try:
            resp = self._session.post(url, json=payload, timeout=self._timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            logger.warning("[LLMObserver] collector unreachable at %s – writing fallback log", url)
            _write_fallback({"path": path, "payload": payload, "ts": datetime.now(timezone.utc).isoformat()})
            return {"status": "fallback", "error": "collector unreachable"}
        except requests.exceptions.Timeout:
            logger.warning("[LLMObserver] request to %s timed out", url)
            _write_fallback({"path": path, "payload": payload, "ts": datetime.now(timezone.utc).isoformat()})
            return {"status": "fallback", "error": "timeout"}
        except Exception as exc:
            logger.warning("[LLMObserver] unexpected error posting to %s: %s", url, exc)
            return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Cost estimation (mirrors backend/utils/helpers.py)
# ---------------------------------------------------------------------------
_COST_TABLE: Dict[str, tuple[float, float]] = {
    "claude-3-5-sonnet":          (0.003,  0.015),
    "claude-3-5-sonnet-20241022": (0.003,  0.015),
    "claude-3-opus":              (0.015,  0.075),
    "claude-haiku-4-5-20251001":  (0.00025, 0.00125),
    "claude-sonnet-4-6":          (0.003,  0.015),
    "gpt-4":                      (0.03,   0.06),
    "gpt-4-turbo":                (0.01,   0.03),
    "gpt-3.5-turbo":              (0.0005, 0.0015),
}
_DEFAULT_COST = (0.001, 0.002)


def _estimate_cost(tokens_in: int, tokens_out: int, model: str) -> float:
    in_rate, out_rate = _COST_TABLE.get(model.lower(), _DEFAULT_COST)
    return round((tokens_in / 1000) * in_rate + (tokens_out / 1000) * out_rate, 8)
