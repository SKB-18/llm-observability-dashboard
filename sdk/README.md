# llm-observer

Python SDK for the LLM Observability Dashboard. Automatically logs every LLM API call with zero code changes.

## Install

```bash
pip install llm-observer
# with Anthropic support:
pip install "llm-observer[anthropic]"
# with OpenAI support:
pip install "llm-observer[openai]"
```

## Quick start

```python
from llm_observer import LLMObserver

observer = LLMObserver("http://localhost:8001")

# --- Manual logging ---
observer.log_completion(
    prompt="What is Python?",
    response="Python is a high-level programming language.",
    model="gpt-4",
    tokens_in=10,
    tokens_out=12,
    latency_ms=340.5,
    cost_usd=0.0003,
)

# --- Auto-wrap Anthropic client ---
from anthropic import Anthropic
client = observer.wrap_claude_client(Anthropic())
# All client.messages.create() calls are now logged automatically
```

## Configuration

| Parameter | Default | Description |
|---|---|---|
| `collector_url` | `http://localhost:8001` | Backend URL |
| `api_key` | `None` | Bearer token (JWT from /api/v1/auth/login) |
| `timeout` | `2.0` | HTTP timeout in seconds |

If the backend is unreachable, calls are written to `llm_observer_fallback.jsonl` and never raise.
