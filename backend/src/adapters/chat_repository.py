"""PostgreSQL implementation of chat listing from LangGraph checkpoints."""
from typing import Any

from psycopg_pool import AsyncConnectionPool


class ChatRepository:
    """Reads chat metadata from the LangGraph checkpoints tables."""

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def list_chats(self) -> list[dict[str, Any]]:
        """Return all chats ordered by most recent first.

        Returns:
            A list of dicts with ``thread_id`` and ``created_at`` keys.
        """
        async with self._pool.connection() as conn:
            cursor = await conn.execute(
                "SELECT DISTINCT thread_id, "
                "       checkpoint->>'ts' AS created_at "
                "FROM checkpoints "
                "ORDER BY (checkpoint->>'ts') DESC "
                "LIMIT 30"
            )
            rows = await cursor.fetchall()
            return [
                {"thread_id": row["thread_id"], "created_at": row["created_at"]}
                for row in rows
            ]
