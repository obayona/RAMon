from typing import Optional

from psycopg_pool import AsyncConnectionPool
from models import Product

class ProductCatalog:
    """Abstract interface for retrieving product information."""

    async def get_product(self, product_id: str) -> Optional[Product]:
        raise NotImplementedError


class PostgresProductCatalog(ProductCatalog):
    """PostgreSQL-backed implementation of the product catalog."""

    def __init__(self, pool: AsyncConnectionPool):
        self._pool = pool

    async def get_product(self, product_id: str) -> Optional[Product]:
        if not product_id:
            return None

        async with self._pool.connection() as conn:
            cursor = await conn.execute(
                "SELECT id, name, description, price, url, stock"
                " FROM products WHERE id = %s",
                (product_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None

            return Product(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                price=row['price'],
                url=row['url'],
                stock=row['stock'],
            )
