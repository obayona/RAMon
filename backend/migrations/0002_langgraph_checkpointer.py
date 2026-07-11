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


def apply_step(conn):
    """Create LangGraph checkpointer tables using the official setup method."""
    
    # Yoyo passes its own connection, but LangGraph's ShallowPostgresSaver
    # requires its own psycopg3 connection. Open a direct connection.
    db_url = os.getenv("DATABASE_URL")
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
