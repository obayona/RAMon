from typing import List

from langchain_core.tools import BaseTool

from chatbot.infrastructure.tools.recommend_products import make_recommend_products
from chatbot.infrastructure.tools.search_component_spec import make_search_component_spec


def build_tools(
    openai_client,
    pinecone_index,
    tavily_client,
) -> List[BaseTool]:
    """Instantiate all tools with their runtime dependencies."""
    tools: List[BaseTool] = [
        make_recommend_products(openai_client, pinecone_index),
        make_search_component_spec(tavily_client),
    ]

    return tools


__all__ = ["build_tools"]
