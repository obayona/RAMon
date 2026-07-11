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

        async with self._pool.connection() as conn:
            cursor = await conn.execute(
                "SELECT id, product_id, sku, name, description, categories, price, url, stock "
                "FROM products WHERE product_id = %s",
                (product_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None

            return Product(
                id=row["id"],
                product_id=str(row["product_id"]),
                sku=row["sku"] or "",
                name=row["name"],
                description=row["description"] or "",
                categories=row["categories"] or "",
                price=row["price"],
                stock=row["stock"],
            )
