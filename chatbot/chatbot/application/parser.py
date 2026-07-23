"""Streaming parser for extracting product markers from LLM output."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, TypedDict

from chatbot.application.relevance import filter_by_ids, parse_relevant_ids


class TextEvent(TypedDict):
    """Event representing plain text content."""

    type: str  # "text"
    content: str


class ProductsEvent(TypedDict):
    """Event representing parsed product recommendations."""

    type: str  # "products"
    data: List[Dict[str, Any]]


ParsedEvent = TextEvent | ProductsEvent

_PRODUCTS_TAG_RE = re.compile(r'<products\s+ids="([^"]*)"\s*/>')


@dataclass
class ProductMarkerParser:
    """Detects <products ids="..."/> markers in streaming text and emits product events.

    The parser receives the full product list and filters it based on the
    IDs found in the tag. Filtering uses ``filter_by_ids`` from the
    ``relevance`` module — the same function used by the process_recommendations
    node for chat history.

    Usage:
        parser = ProductMarkerParser(products=[{"id": 1, "name": "Laptop", "price": 999}])
        for chunk in llm_stream:
            for event in parser.feed(chunk):
                handle_event(event)
        for event in parser.flush():
            handle_event(event)
    """

    products: List[Dict[str, Any]] = field(default_factory=list)
    _buffer: str = field(default="", init=False)

    def feed(self, chunk: str) -> List[ParsedEvent]:
        """Feed a chunk and return parsed events."""
        events: List[ParsedEvent] = []
        self._buffer += chunk

        while True:
            match = _PRODUCTS_TAG_RE.search(self._buffer)
            if match:
                # Emit text before the tag
                start = match.start()
                if start > 0:
                    events.append({"type": "text", "content": self._buffer[:start]})
                # Filter products by IDs in the tag
                relevant_ids = parse_relevant_ids(match.group(0))
                filtered = filter_by_ids(self.products, relevant_ids)
                events.append({"type": "products", "data": filtered})
                self._buffer = self._buffer[match.end():]
            else:
                # No complete tag found — hold back from last '<' to avoid
                # splitting a partial tag across chunks
                last_lt = self._buffer.rfind("<")
                if last_lt >= 0:
                    if last_lt > 0:
                        events.append({"type": "text", "content": self._buffer[:last_lt]})
                    self._buffer = self._buffer[last_lt:]
                else:
                    if self._buffer:
                        events.append({"type": "text", "content": self._buffer})
                        self._buffer = ""
                break

        return events

    def flush(self) -> List[ParsedEvent]:
        """Flush remaining buffer at end of stream."""
        events: List[ParsedEvent] = []
        if self._buffer:
            events.append({"type": "text", "content": self._buffer})
            self._buffer = ""
        return events
