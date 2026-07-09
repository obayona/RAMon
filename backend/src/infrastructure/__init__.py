"""Infrastructure layer - Database and external service setup."""
from src.infrastructure.database import create_db_pool

__all__ = ["create_db_pool"]
