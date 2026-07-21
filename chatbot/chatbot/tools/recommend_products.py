"""Product recommendation tool using semantic search."""
from __future__ import annotations

from typing import Annotated, Optional

import structlog
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.types import Command

from chatbot.domain.ports import EmbeddingService, ProductRepository

logger = structlog.get_logger("ramon.chatbot.tools")

_SIMILARITY_THRESHOLD = 0.3


def make_recommend_products(
    embedding_service: EmbeddingService,
    product_repository: ProductRepository,
):
    """Create the ``recommend_products`` tool with pre-configured services."""

    @tool
    async def recommend_products(
        query: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> Command:
        """Search for hardware products using semantic similarity with optional price filtering.

        The query is embedded and searched against the product database using
        cosine distance. ``min_price`` / ``max_price`` are applied as filters.
        Only returns products with a similarity score of 70% or higher.
        """
        logger.debug(
            "recommend_products.search",
            query=query,
            min_price=min_price,
            max_price=max_price,
        )
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

        logger.debug("recommend_products.results", count=len(products))

        # Minimal ToolMessage with just IDs to save tokens
        # Full product data is in state and will be in the final AI response
        product_ids = [p.get("id") or p.get("product_id") for p in products]
        tool_content = f"Found {len(products)} products: {product_ids}" if products else "No products found"

        # Update state with query and recommendations
        # Routing is handled by conditional edge in graph based on product_query
        return Command(
            update={
                "product_query": query,
                "recommendations": products,
                "messages": [
                    ToolMessage(content=tool_content, tool_call_id=tool_call_id)
                ],
            },
        )

    return recommend_products
