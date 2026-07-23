"""PostgreSQL implementation of the ProductCatalog port."""
from typing import Optional

from psycopg_pool import AsyncConnectionPool

from src.domain.models import Product

_PRODUCT_COLUMNS = (
    "id, product_id, sku, name, description, categories, price, stock, in_stock, "
    "url, image_url, status"
)


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
                f"SELECT {_PRODUCT_COLUMNS} FROM products WHERE product_id = %s",
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
                in_stock=row["in_stock"] if row["in_stock"] is not None else True,
                url=row["url"] or "",
                image_url=row["image_url"] or "",
                status=row["status"] or "publish",
            )
