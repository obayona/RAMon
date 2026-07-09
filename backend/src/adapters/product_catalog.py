"""PostgreSQL implementation of the ProductCatalog port."""
from typing import Optional

from psycopg_pool import AsyncConnectionPool

from src.domain.models import Product


class PostgresProductCatalog:
    """PostgreSQL-backed implementation of the product catalog."""

    def __init__(self, pool: AsyncConnectionPool) -> None:
        """Initialize with a connection pool.
        
        Args:
            pool: Async connection pool for PostgreSQL.
        """
        self._pool = pool

    async def get_product(self, product_id: str) -> Optional[Product]:
        """Retrieve a product by its ID from PostgreSQL.
        
        Args:
            product_id: The unique product identifier.
            
        Returns:
            The product if found, None otherwise.
        """
        if not product_id:
            return None

        async with self._pool.connection() as conn:
            cursor = await conn.execute(
                "SELECT id, name, description, price, url, stock "
                "FROM products WHERE id = %s",
                (product_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None

            return Product(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                price=row["price"],
                url=row["url"],
                stock=row["stock"],
            )
