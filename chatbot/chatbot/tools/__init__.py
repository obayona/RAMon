from typing import List

from langchain_core.tools import BaseTool
from psycopg_pool import AsyncConnectionPool
from langchain_tavily import TavilySearch
from openai import OpenAI

from chatbot.tools.recommend_products import make_recommend_products
from chatbot.tools.search_component_spec import make_search_component_spec


def build_tools(
    openai_client: OpenAI,
    db_pool: AsyncConnectionPool,
    tavily_client: TavilySearch,
) -> List[BaseTool]:
    """Instantiate all tools with their runtime dependencies."""
    tools: List[BaseTool] = [
        make_recommend_products(openai_client, db_pool),
        make_search_component_spec(tavily_client),
    ]

    return tools


__all__ = ["build_tools"]