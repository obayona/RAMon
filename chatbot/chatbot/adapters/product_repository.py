"""PostgreSQL product repository implementation using pgvector."""
from typing import List, Optional

import structlog
from psycopg_pool import AsyncConnectionPool

from chatbot.domain.ports import ProductRepository
from chatbot.domain.product import Product

logger = structlog.get_logger("ramon.chatbot.adapters")


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
        min_similarity: Optional[float] = None,
        limit: int = 3,
    ) -> List[Product]:
        """Search for products by embedding similarity with optional price filtering."""
        # Build WHERE clause for price filtering (applied inside CTE)
        price_conditions: List[str] = []
        price_params: List = []

        if min_price is not None:
            price_conditions.append("price >= %s")
            price_params.append(min_price)

        if max_price is not None:
            price_conditions.append("price <= %s")
            price_params.append(max_price)

        inner_where = ""
        if price_conditions:
            inner_where = "WHERE " + " AND ".join(price_conditions)

        # Similarity filter applied on outer query
        outer_where = ""
        if min_similarity is not None:
            outer_where = "WHERE similarity >= %s"

        # Param order: embedding, price filters, similarity, limit
        params: List = [embedding]
        params.extend(price_params)
        if min_similarity is not None:
            params.append(min_similarity)
        params.append(limit)

        sql = f"""
            WITH scored AS (
                SELECT id, product_id, sku, name, description, categories, price,
                       stock, in_stock, url, image_url, status,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM products
                {inner_where}
            )
            SELECT * FROM scored
            {outer_where}
            ORDER BY similarity DESC
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
                "in_stock": row["in_stock"] if row["in_stock"] is not None else True,
                "url": row["url"] or "",
                "image_url": row["image_url"] or "",
                "status": row["status"] or "published",
                "similarity": float(row["similarity"]),
            }
            for row in rows
        ]

        logger.debug(
            "product_search.completed",
            result_count=len(products),
            has_price_filter=min_price is not None or max_price is not None,
        )

        return products


# Ensure the class satisfies the protocol
_: ProductRepository = PostgresProductRepository.__new__(PostgresProductRepository)
