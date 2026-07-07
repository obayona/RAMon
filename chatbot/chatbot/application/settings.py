from typing import TypedDict
from langchain_core.runnables import RunnableConfig
from langchain_tavily import TavilySearch
from psycopg_pool import AsyncConnectionPool
from openai import OpenAI

class ChatbotSettings(TypedDict):
    db_pool: AsyncConnectionPool
    openai_api_key: str
    tavily_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.0
