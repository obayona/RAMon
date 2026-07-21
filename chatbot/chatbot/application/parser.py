"""Streaming parser for extracting product markers from LLM output."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, TypedDict


class TextEvent(TypedDict):
    """Event representing plain text content."""

    type: str  # "text"
    content: str


class ProductsEvent(TypedDict):
    """Event representing parsed product recommendations."""

    type: str  # "products"
    data: List[Dict[str, Any]]


ParsedEvent = TextEvent | ProductsEvent

# Tag used to wrap product JSON in LLM output
_START_TAG = "<products>"
_END_TAG = "</products>"
_TAG_MAX_LEN = len(_START_TAG)  # Buffer size to avoid splitting tags


@dataclass
class ProductMarkerParser:
    """Buffers streaming text to detect and extract <products>...</products> markers.

    This parser handles the case where tags may be split across multiple chunks.
    It buffers a small amount of text to ensure tags aren't missed.

    Usage:
        parser = ProductMarkerParser()
        async for chunk in llm_stream:
            for event in parser.feed(chunk):
                handle_event(event)
        for event in parser.flush():
            handle_event(event)

    Or use the helper function for cleaner integration:
        async for event in parse_product_stream(llm_stream):
            handle_event(event)
    """

    _buffer: str = field(default="", init=False)
    _in_products: bool = field(default=False, init=False)
    _products_buffer: str = field(default="", init=False)

    def feed(self, chunk: str) -> List[ParsedEvent]:
        """Feed a chunk and return parsed events.

        Args:
            chunk: Text chunk from the LLM stream.

        Returns:
            List of parsed events (text or products).
        """
        events: List[ParsedEvent] = []
        self._buffer += chunk

        while True:
            if not self._in_products:
                # Look for <products> start tag
                start_idx = self._buffer.find(_START_TAG)
                if start_idx == -1:
                    # No marker found - emit buffered text except last N chars
                    # to avoid splitting the start tag across chunks
                    if len(self._buffer) > _TAG_MAX_LEN:
                        emit = self._buffer[:-_TAG_MAX_LEN]
                        self._buffer = self._buffer[-_TAG_MAX_LEN:]
                        if emit:
                            events.append({"type": "text", "content": emit})
                    break
                else:
                    # Emit text before marker
                    if start_idx > 0:
                        events.append({"type": "text", "content": self._buffer[:start_idx]})
                    self._buffer = self._buffer[start_idx + len(_START_TAG) :]
                    self._in_products = True
                    self._products_buffer = ""

            if self._in_products:
                # Look for </products> end tag
                # Need to check combined buffer in case tag is split
                combined = self._products_buffer + self._buffer
                end_idx = combined.find(_END_TAG)
                if end_idx == -1:
                    # Haven't found end yet - accumulate in products buffer
                    self._products_buffer = combined
                    self._buffer = ""
                    break
                else:
                    # Found end - parse JSON
                    json_content = combined[:end_idx]
                    remaining = combined[end_idx + len(_END_TAG) :]
                    self._buffer = remaining
                    self._products_buffer = ""
                    self._in_products = False

                    try:
                        products = json.loads(json_content)
                        events.append({"type": "products", "data": products})
                    except json.JSONDecodeError:
                        # Fallback: emit as text if JSON is invalid
                        events.append(
                            {
                                "type": "text",
                                "content": f"{_START_TAG}{json_content}{_END_TAG}",
                            }
                        )

        return events

    def flush(self) -> List[ParsedEvent]:
        """Flush remaining buffer at end of stream.

        Returns:
            List of any remaining events.
        """
        events: List[ParsedEvent] = []
        if self._buffer:
            events.append({"type": "text", "content": self._buffer})
            self._buffer = ""
        if self._in_products and self._products_buffer:
            # Unclosed marker - emit as text
            events.append(
                {"type": "text", "content": f"{_START_TAG}{self._products_buffer}"}
            )
            self._products_buffer = ""
            self._in_products = False
        return events


async def parse_product_stream(
    stream: AsyncGenerator[str, None],
) -> AsyncGenerator[ParsedEvent, None]:
    """Parse a stream of text chunks for product markers.

    This is a convenience wrapper that handles parser lifecycle automatically,
    including flushing at the end of the stream.

    Args:
        stream: Async generator yielding text chunks.

    Yields:
        Parsed events (text or products).

    Example:
        async def get_chunks():
            yield "Here are laptops "
            yield "<products>[{...}]</products>"

        async for event in parse_product_stream(get_chunks()):
            if event["type"] == "text":
                print(event["content"])
            elif event["type"] == "products":
                render_cards(event["data"])
    """
    parser = ProductMarkerParser()

    async for chunk in stream:
        for event in parser.feed(chunk):
            yield event

    # Flush remaining buffer
    for event in parser.flush():
        yield event
