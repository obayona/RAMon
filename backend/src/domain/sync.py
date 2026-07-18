"""Port interface for enqueuing product sync changes."""
from __future__ import annotations

from typing import Any, Dict, List, Protocol, runtime_checkable


@runtime_checkable
class SyncEnqueuer(Protocol):
    """Protocol for enqueuing product changes into the sync queue."""

    async def enqueue(self, changes: List[Dict[str, Any]]) -> int:
        """Enqueue a batch of product changes for background processing.

        Args:
            changes: List of change dicts with keys: action, product_id, fields.

        Returns:
            Number of items enqueued.
        """
        ...
