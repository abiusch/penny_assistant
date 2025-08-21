"""Abstraction over the OpenAI GPT chat API.

This module provides a small wrapper around the OpenAI Python client
library that is compatible with the v1 API.  It exposes a simple
``GPTClient`` class used to send conversational prompts and retrieve
responses from a language model.  The API key is read from the
``OPENAI_API_KEY`` environment variable.  If you wish to stream
responses, the ``chat`` method will yield chunks of the assistant's
output as they arrive.

Example
-------

```python
from ai.gpt_client import GPTClient

client = GPTClient()
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello"},
]
reply = client.chat(messages)  # non‑streaming
print(reply)

# Streaming example:
for chunk in client.chat(messages, stream=True):
    print(chunk, end="", flush=True)
print()  # newline after streaming completes
```
"""

from __future__ import annotations

import os
from typing import Iterable, List, Dict, Union, Generator, Any

import openai


class GPTClient:
    """Simple wrapper for the OpenAI chat completion endpoint.

    Parameters
    ----------
    model: str, optional
        Identifier of the underlying chat model to use.  Defaults to
        ``"gpt-3.5-turbo"``.
    temperature: float, optional
        Sampling temperature to use for completions.  Higher values
        produce more random outputs.  Defaults to ``0.7``.

    Raises
    ------
    ValueError
        If the ``OPENAI_API_KEY`` environment variable is not set.
    """

    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set; please export it before using GPTClient"
            )
        # Initialise a dedicated OpenAI client.  Instantiating a client
        # avoids having to globally mutate openai.api_key.
        self._client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[str, Generator[str, None, None]]:
        """Send a list of messages to the model and return the assistant's reply.

        Parameters
        ----------
        messages: list of dict
            A list of message dictionaries following the OpenAI chat format,
            each containing ``"role"`` and ``"content"`` keys.  Roles must
            be one of ``"system"``, ``"user"``, or ``"assistant"``.
        stream: bool, optional
            If ``True``, return a generator that yields chunks of the
            response as they arrive.  If ``False``, return the full reply
            as a single string.  Defaults to ``False``.
        **kwargs: any
            Additional keyword arguments passed directly to the underlying
            OpenAI API call.  These may be used to customise the request
            further (for example, to set ``max_tokens``, ``stop`` sequences,
            or ``top_p``).

        Returns
        -------
        str or generator
            If ``stream`` is ``False``, returns the assistant's reply as a
            single string.  If ``stream`` is ``True``, returns a generator
            that yields strings containing incremental chunks of the reply.
        """

        # Compose arguments for the OpenAI chat completion endpoint.
        request_params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            **kwargs,
        }

        if stream:
            request_params["stream"] = True
            response = self._client.chat.completions.create(**request_params)
            # The API returns an iterator of `openai.types.chat.CompletionChunk` objects.
            def stream_generator() -> Generator[str, None, None]:
                for chunk in response:
                    # Each chunk contains a list of choices; we're interested in
                    # the incremental delta for the first choice.  The delta may
                    # include ``role`` or ``content`` keys depending on
                    # position in the stream.
                    delta = chunk.choices[0].delta
                    content = getattr(delta, "content", None)
                    if content:
                        yield content
            return stream_generator()
        else:
            # Non-streaming: the API returns a single ChatCompletion object
            response = self._client.chat.completions.create(**request_params)
            return response.choices[0].message.content
