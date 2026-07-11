"""
LangGraph ShallowPostgresSaver checkpointer tables.

Uses LangGraph's built-in setup() method to create the required tables,
ensuring compatibility with the installed version of langgraph-checkpoint-postgres.
"""
import os

from yoyo import step
from langgraph.checkpoint.postgres import ShallowPostgresSaver
from dotenv import load_dotenv

load_dotenv('../.env')

__depends__ = {"0001_initial_schema"}


def _get_database_url() -> str:
    """Build DATABASE_URL from individual components or use existing value."""
    existing_url = os.environ.get("DATABASE_URL", "").strip()
    if existing_url:
        return existing_url
    
    return (
        f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )


def apply_step(conn):
    """Create LangGraph checkpointer tables using the official setup method."""
    
    # Yoyo passes its own connection, but LangGraph's ShallowPostgresSaver
    # requires its own psycopg3 connection. Open a direct connection.
    db_url = _get_database_url()
    with ShallowPostgresSaver.from_conn_string(db_url) as checkpointer:
        checkpointer.setup()


def rollback_step(conn):
    """Drop LangGraph checkpointer tables."""
    cursor = conn.cursor()
    
    # Drop tables in reverse dependency order
    cursor.execute("DROP TABLE IF EXISTS checkpoint_writes;")
    cursor.execute("DROP TABLE IF EXISTS checkpoint_blobs;")
    cursor.execute("DROP TABLE IF EXISTS checkpoints;")
    cursor.execute("DROP TABLE IF EXISTS checkpoint_migrations;")


steps = [
    step(apply_step, rollback_step),
]
