"""Product recommendation tool using semantic search."""
import json
from typing import Optional

from langchain_core.tools import tool

from chatbot.domain.ports import EmbeddingService, ProductRepository


def make_recommend_products(
    embedding_service: EmbeddingService,
    product_repository: ProductRepository,
):
    """Create the ``recommend_products`` tool with pre-configured services."""

    @tool
    async def recommend_products(
        query: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> str:
        """Search for hardware products using semantic similarity with optional price filtering.

        The query is embedded and searched against the product database using 
        cosine distance. ``min_price`` / ``max_price`` are applied as filters.
        Returns the top 3 products as a JSON array.
        """
        # Generate embedding for the query
        embedding = await embedding_service.embed(query)

        # Search for similar products
        products = await product_repository.search_by_similarity(
            embedding=embedding,
            min_price=min_price,
            max_price=max_price,
            limit=3,
        )

        return json.dumps(products, indent=2)

    return recommend_products
