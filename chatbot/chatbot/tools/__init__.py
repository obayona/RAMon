"""Tools module for chatbot functionality."""
from typing import List

from langchain_core.tools import BaseTool
from langchain_tavily import TavilySearch

from chatbot.domain.ports import EmbeddingService, ProductRepository
from chatbot.tools.recommend_products import make_recommend_products
from chatbot.tools.search_component_spec import make_search_component_spec


def build_tools(
    embedding_service: EmbeddingService,
    product_repository: ProductRepository,
    tavily_client: TavilySearch,
) -> List[BaseTool]:
    """Instantiate all tools with their runtime dependencies.
    
    Args:
        embedding_service: Service for generating text embeddings.
        product_repository: Repository for product data access.
        tavily_client: Tavily client for web search.
        
    Returns:
        List of configured tools.
    """
    tools: List[BaseTool] = [
        make_recommend_products(embedding_service, product_repository),
        make_search_component_spec(tavily_client),
    ]

    return tools


__all__ = ["build_tools"]
