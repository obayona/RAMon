"""Streaming parser for extracting product markers from LLM output."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, TypedDict


class TextEvent(TypedDict):
    """Event representing plain text content."""

    type: str  # "text"
    content: str


class ProductsEvent(TypedDict):
    """Event representing parsed product recommendations."""

    type: str  # "products"
    data: List[Dict[str, Any]]


ParsedEvent = TextEvent | ProductsEvent

_MARKER = "<products/>"
_MARKER_LEN = len(_MARKER)


@dataclass
class ProductMarkerParser:
    """Detects <products/> markers in streaming text and emits product events.

    The parser looks for the self-closing <products/> tag. When found, it emits
    a products event with the data provided to the constructor. This allows
    fast streaming since the LLM only needs to output a short marker.

    Usage:
        parser = ProductMarkerParser(products=[{"name": "Laptop", "price": 999}])
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
            idx = self._buffer.find(_MARKER)
            if idx != -1:
                # Emit text before marker
                if idx > 0:
                    events.append({"type": "text", "content": self._buffer[:idx]})
                # Emit products
                events.append({"type": "products", "data": self.products})
                self._buffer = self._buffer[idx + _MARKER_LEN:]
            else:
                # No marker found - emit text except last N chars to avoid splitting tag
                if len(self._buffer) > _MARKER_LEN:
                    emit = self._buffer[:-_MARKER_LEN]
                    self._buffer = self._buffer[-_MARKER_LEN:]
                    if emit:
                        events.append({"type": "text", "content": emit})
                break

        return events

    def flush(self) -> List[ParsedEvent]:
        """Flush remaining buffer at end of stream."""
        events: List[ParsedEvent] = []
        if self._buffer:
            events.append({"type": "text", "content": self._buffer})
            self._buffer = ""
        return events
