"""
Demo: automatic logging of Claude API calls via LLMObserver SDK.

Prerequisites:
    pip install -e sdk/
    export ANTHROPIC_API_KEY=sk-ant-...
    # Start the observability backend on http://localhost:8000

Usage:
    python examples/demo.py
"""
import sys
import os

# Allow running from project root without installing the SDK
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))

from anthropic import Anthropic
from llm_observer import LLMObserver


def main():
    observer = LLMObserver("http://localhost:8000")
    client = Anthropic()
    client = observer.wrap_claude_client(client)

    questions = [
        "What is machine learning?",
        "Explain neural networks in one sentence.",
        "What is the difference between AI and ML?",
        "Name three popular LLM providers.",
        "What does 'token' mean in the context of LLMs?",
    ]

    print("Making 50 API calls – all automatically logged to the dashboard…\n")

    for i in range(50):
        question = questions[i % len(questions)]
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",   # cheapest model for demo
                messages=[{"role": "user", "content": f"Q{i + 1}: {question}"}],
                max_tokens=80,
            )
            snippet = response.content[0].text[:60].replace("\n", " ")
            print(f"  Call {i + 1:02d}/50: {snippet}…")
        except Exception as exc:
            print(f"  Call {i + 1:02d}/50: ERROR – {exc}", file=sys.stderr)

    print("\nAll calls logged to dashboard!")
    print("Open http://localhost:3000 to see the metrics.")


if __name__ == "__main__":
    main()
