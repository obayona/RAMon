"""Token counting via tiktoken."""
from __future__ import annotations

import tiktoken


_CACHE: dict[str, tiktoken.Encoding] = {}


def _get_encoding(model: str) -> tiktoken.Encoding:
    """Get (and cache) the tiktoken encoding for a model name."""
    if model not in _CACHE:
        _CACHE[model] = tiktoken.encoding_for_model(model)
    return _CACHE[model]


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Count the number of tokens in a plain text string.

    Args:
        text: The text to tokenize.
        model: OpenAI model name (determines the tokenizer).

    Returns:
        Number of tokens.
    """
    enc = _get_encoding(model)
    return len(enc.encode(text))


def count_message_tokens(
    messages: list[dict[str, str]],
    model: str = "gpt-4o-mini",
) -> int:
    """Estimate token count for a list of chat messages.

    Accounts for the per-message framing overhead that the Chat Completions
    API adds (≈4 tokens per message for role/name separators).

    Args:
        messages: List of dicts with at least a "role" and "content" key.
        model: OpenAI model name.

    Returns:
        Estimated total tokens.
    """
    enc = _get_encoding(model)
    total = 0
    for msg in messages:
        total += 4  # message framing: <|start|>{role}\n ...
        for key, value in msg.items():
            if isinstance(value, str):
                total += len(enc.encode(value))
    total += 2  # priming reply: <|start|>assistant
    return total
