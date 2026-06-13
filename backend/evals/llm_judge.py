"""
LLM-as-judge evaluation using Azure OpenAI (Responses API).
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
import concurrent.futures
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Simple in-process cache: sha256(prompt+response+criteria) → score
_CACHE: dict[str, float] = {}

# Seconds to wait between retry attempts. Patch to () in tests for instant failure.
_RETRY_DELAYS: Tuple[int, ...] = (1, 2, 4)


def _cache_key(prompt: str, response: str, criteria: str) -> str:
    raw = f"{prompt}||{response}||{criteria}"
    return hashlib.sha256(raw.encode()).hexdigest()


class LLMJudge:
    """Evaluate LLM responses using Azure OpenAI as an impartial judge."""

    SCORE_PROMPT = (
        "You are an impartial evaluator. Score the following response on a scale "
        "from 0 to 10 based on this criteria: {criteria}\n\n"
        "Prompt: {prompt}\n\nResponse: {response}\n\n"
        "Reply with JSON only: {{\"score\": <number 0-10>, \"explanation\": \"<one sentence>\"}}"
    )

    def __init__(self, model: Optional[str] = None):
        from openai import AzureOpenAI
        from backend.config import settings
        self._client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        self._model = model or settings.AZURE_OPENAI_DEPLOYMENT

    def evaluate_response(
        self,
        prompt: str,
        response: str,
        criteria: str = "Is this response helpful and accurate?",
    ) -> float:
        """Score a single response. Retries on stream/timeout errors. Returns [0, 1]."""
        key = _cache_key(prompt, response, criteria)
        if key in _CACHE:
            return _CACHE[key]

        message_text = self.SCORE_PROMPT.format(
            criteria=criteria, prompt=prompt, response=response
        )

        last_exc: Optional[Exception] = None
        for attempt, delay in enumerate((*_RETRY_DELAYS, None)):
            try:
                result = self._client.responses.create(
                    model=self._model,
                    input=message_text,
                )
                raw = result.output_text.strip()
                data = json.loads(raw)
                score = float(data["score"]) / 10.0
                score = max(0.0, min(1.0, score))
                _CACHE[key] = score
                return score
            except Exception as exc:
                last_exc = exc
                if delay is not None:
                    logger.warning(
                        "LLMJudge attempt %d/%d failed: %s — retrying in %ds",
                        attempt + 1, len(_RETRY_DELAYS) + 1, exc, delay,
                    )
                    time.sleep(delay)

        logger.warning(
            "LLMJudge evaluation failed after %d attempts: %s",
            len(_RETRY_DELAYS) + 1, last_exc,
        )
        score = 0.0
        _CACHE[key] = score
        return score

    def batch_evaluate(self, completions: List[dict]) -> List[float]:
        """Evaluate multiple completions in parallel (thread pool)."""
        def _eval(item: dict) -> float:
            return self.evaluate_response(
                item.get("prompt", ""),
                item.get("response", ""),
                item.get("criteria", "Is this response helpful and accurate?"),
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            return list(pool.map(_eval, completions))

    def get_evaluation_explanation(self, prompt: str, response: str, criteria: str = "") -> str:
        """Return a detailed explanation string from the model."""
        message_text = (
            f"Explain in detail why the following response is good or bad.\n\n"
            f"Prompt: {prompt}\nResponse: {response}"
        )
        if criteria:
            message_text += f"\nCriteria: {criteria}"
        try:
            result = self._client.responses.create(
                model=self._model,
                input=message_text,
            )
            return result.output_text.strip()
        except Exception as exc:
            logger.warning("Explanation request failed: %s", exc)
            return ""
