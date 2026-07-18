"""PostgreSQL product repository implementation using pgvector."""
from typing import List, Optional

from psycopg_pool import AsyncConnectionPool

from chatbot.domain.ports import ProductRepository
from chatbot.domain.product import Product


class PostgresProductRepository:
    """ProductRepository implementation using PostgreSQL with pgvector."""

    def __init__(self, pool: AsyncConnectionPool) -> None:
        """Initialize the repository.
        
        Args:
            pool: Async connection pool for PostgreSQL.
        """
        self._pool = pool

    async def search_by_similarity(
        self,
        embedding: List[float],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 3,
    ) -> List[Product]:
        """Search for products by embedding similarity with optional price filtering."""
        # Build WHERE clause for price filtering
        conditions: List[str] = []
        params: List = []

        if min_price is not None:
            conditions.append("price >= %s")
            params.append(min_price)

        if max_price is not None:
            conditions.append("price <= %s")
            params.append(max_price)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        params.append(embedding)
        params.append(limit)

        sql = f"""
            SELECT id, product_id, sku, name, description, categories, price, stock,
                   url, image_url, status
            FROM products
            {where_clause}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """

        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()

        products: List[Product] = [
            {
                "id": row["id"],
                "product_id": row["product_id"],
                "sku": row["sku"] or "",
                "name": row["name"],
                "description": row["description"] or "",
                "categories": row["categories"] or "",
                "price": row["price"],
                "stock": row["stock"],
                "url": row["url"] or "",
                "image_url": row["image_url"] or "",
                "status": row["status"] or "published",
            }
            for row in rows
        ]

        return products


# Ensure the class satisfies the protocol
_: ProductRepository = PostgresProductRepository.__new__(PostgresProductRepository)
