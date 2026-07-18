"""
Create the sync_queue table for async product synchronization.

WordPress enqueues product changes here; a background worker processes them.
"""
from yoyo import step

__depends__ = {"0001_initial_schema"}

steps = [
    step(
        """
        CREATE TABLE sync_queue (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            payload JSONB NOT NULL,
            status TEXT DEFAULT 'pending',
            error TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            processed_at TIMESTAMPTZ
        )
        """,
        "DROP TABLE IF EXISTS sync_queue",
    ),
    step(
        "CREATE INDEX idx_sync_queue_pending ON sync_queue(status, created_at)",
        "DROP INDEX IF EXISTS idx_sync_queue_pending",
    ),
]
