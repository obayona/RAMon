import json
from typing import Optional

from langchain_core.tools import tool
from psycopg_pool import AsyncConnectionPool
from openai import OpenAI


def make_recommend_products(openai_client: OpenAI, db_pool: AsyncConnectionPool):
    """Create the ``recommend_products`` tool with pre-configured clients."""

    @tool
    async def recommend_products(
        query: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> str:
        """Search for hardware products using semantic similarity with optional price filtering.

        The query is embedded with ``text-embedding-3-small`` and searched against the
        ``products`` table using pgvector cosine distance.  ``min_price`` / ``max_price``
        are applied as WHERE filters.  Returns the top 3 products as a JSON array."""

        embedding = (
            openai_client.embeddings.create(
                input=query, model="text-embedding-3-small"
            )
            .data[0]
            .embedding
        )

        # Build WHERE clause for price filtering
        conditions = []
        params: list = []

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

        sql = f"""
            SELECT id, name, description, price, url, stock
            FROM products
            {where_clause}
            ORDER BY embedding <=> %s::vector
            LIMIT 3
        """

        async with db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()

        products = [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "price": row["price"],
                "url": row["url"],
                "stock": row["stock"],
            }
            for row in rows
        ]

        return json.dumps(products, indent=2)

    return recommend_products
