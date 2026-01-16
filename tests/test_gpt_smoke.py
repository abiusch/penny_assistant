"""Simple smoke test for the GPT client.

This script instantiates the :class:`~src.ai.gpt_client.GPTClient` and
sends a minimal prompt to verify that your OpenAI API key is valid and
that the client can communicate with the chat completion endpoint.

To run the test, ensure that the ``OPENAI_API_KEY`` environment
variable is set in your shell, then execute:

    python test_gpt_smoke.py

If successful, the script will print a short reply from the model.
If an error occurs (e.g. due to an invalid API key or network issue),
the exception will be displayed instead.
"""

from __future__ import annotations

import sys

from src.ai.gpt_client import GPTClient


def main() -> None:
    try:
        client = GPTClient()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    messages = [
        {"role": "user", "content": "Hello!"},
    ]
    try:
        reply = client.chat(messages)
    except Exception as exc:
        print(f"Error connecting to OpenAI: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Model replied: {reply}")


if __name__ == "__main__":
    main()
