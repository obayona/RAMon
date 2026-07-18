"""PostgreSQL sync queue enqueuer for the API."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger("ramon.sync")


class PostgresSyncEnqueuer:
    """Enqueues product changes into the sync_queue table (async, used by API)."""

    def __init__(self, pool) -> None:
        self._pool = pool

    async def enqueue(self, changes: List[Dict[str, Any]]) -> int:
        """Insert all changes into sync_queue in a single query."""
        if not changes:
            return 0

        payloads = [json.dumps(c) for c in changes]

        async with self._pool.connection() as conn:
            await conn.execute(
                "INSERT INTO sync_queue (payload) SELECT unnest(%s::jsonb[])",
                (payloads,),
            )

        logger.info("Enqueued %d sync changes", len(changes))
        return len(changes)
