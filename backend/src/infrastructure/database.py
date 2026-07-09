"""Database connection setup and configuration."""
from pgvector.psycopg import register_vector_async
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row


async def _configure_pgvector(conn) -> None:
    """Register the pgvector type on each new async connection."""
    await register_vector_async(conn)


def create_db_pool(database_url: str, min_size: int = 2, max_size: int = 10) -> AsyncConnectionPool:
    """Create an async connection pool for PostgreSQL.
    
    Args:
        database_url: PostgreSQL connection string.
        min_size: Minimum number of connections in the pool.
        max_size: Maximum number of connections in the pool.
        
    Returns:
        An AsyncConnectionPool instance (not yet opened).
    """
    return AsyncConnectionPool(
        conninfo=database_url,
        min_size=min_size,
        max_size=max_size,
        open=False,
        configure=_configure_pgvector,
        kwargs={
            "autocommit": True,
            "row_factory": dict_row,
        },
    )
