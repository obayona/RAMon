from typing import List

from langchain_core.tools import BaseTool

from chatbot.tools.recommend_products import make_recommend_products
from chatbot.tools.search_component_spec import make_search_component_spec


def build_tools(
    openai_client,
    pinecone_index,
    tavily_client,
) -> List[BaseTool]:
    """Instantiate all tools with their runtime dependencies.

    When ``tavily_api_key`` is falsy the ``search_component_spec`` tool is
    omitted so the LLM never attempts to call it.
    """
    tools: List[BaseTool] = [
        make_recommend_products(openai_client, pinecone_index),
        make_search_component_spec(tavily_client),
    ]
    
    return tools


__all__ = ["build_tools"]
