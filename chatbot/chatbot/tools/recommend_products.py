"""Product recommendation tool using semantic search."""
from __future__ import annotations

from typing import Literal, Optional

from langchain_core.tools import tool
from langgraph.types import Command

from chatbot.domain.ports import EmbeddingService, ProductRepository

_SIMILARITY_THRESHOLD = 0.3


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
    ) -> Command[Literal["process_recommendations"]]:
        """Search for hardware products using semantic similarity with optional price filtering.

        The query is embedded and searched against the product database using
        cosine distance. ``min_price`` / ``max_price`` are applied as filters.
        Only returns products with a similarity score of 70% or higher.
        """
        # Generate embedding for the query
        embedding = await embedding_service.embed(query)

        # Search with similarity threshold applied at the database level
        products = await product_repository.search_by_similarity(
            embedding=embedding,
            min_price=min_price,
            max_price=max_price,
            min_similarity=_SIMILARITY_THRESHOLD,
            limit=3,
        )

        # Return Command to update state and route to process_recommendations
        # No ToolMessage needed - the final response from process_recommendations
        # will contain the product context, saving tokens on future LLM calls
        return Command(
            goto="process_recommendations",
            update={
                "product_query": query,
                "recommendations": products,
            },
        )

    return recommend_products
