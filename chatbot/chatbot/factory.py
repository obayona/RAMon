"""Factory module for easy chatbot initialization.

This module provides convenient factory functions to create chatbot components
with minimal boilerplate. It handles all the wiring of external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from openai import OpenAI
from pinecone import Pinecone

from chatbot.application.service import ChatbotService
from chatbot.config import ChatbotSettings
from chatbot.infrastructure.product_catalog import PineconeProductCatalog, ProductCatalog


@dataclass(slots=True)
class ChatbotComponents:
    """Container for all initialized chatbot components."""
    service: ChatbotService
    product_catalog: ProductCatalog


def build_chatbot_components(
    settings: ChatbotSettings,
    checkpointer: BaseCheckpointSaver,
) -> ChatbotComponents:
    """Build all chatbot components from settings and a checkpointer.

    This is the primary factory function for production use where you need
    full control over the checkpointer (e.g., AsyncSqliteSaver for the server).

    Args:
        settings: Configuration settings loaded from environment
        checkpointer: LangGraph checkpoint saver for conversation persistence

    Returns:
        ChatbotComponents containing the service and product catalog
    """
    openai_client = OpenAI(api_key=settings.openai_api_key)
    pinecone_client = Pinecone(api_key=settings.pinecone_api_key)
    pinecone_index = pinecone_client.Index(settings.pinecone_index_name)
    tavily_client = TavilySearch(max_results=3, tavily_api_key=settings.tavily_api_key)
    chat_model = ChatOpenAI(
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        api_key=settings.openai_api_key,
    )

    service = ChatbotService(
        openai_client=openai_client,
        pinecone_index=pinecone_index,
        tavily_client=tavily_client,
        chat_model=chat_model,
        checkpointer=checkpointer,
    )

    product_catalog = PineconeProductCatalog(pinecone_index)

    return ChatbotComponents(service=service, product_catalog=product_catalog)


def create_chatbot(
    settings: Optional[ChatbotSettings] = None,
    checkpointer: Optional[BaseCheckpointSaver] = None,
) -> ChatbotService:
    """Create a ChatbotService with minimal configuration.

    This is a convenience factory for simple use cases like CLI tools or testing.
    If no settings are provided, they are loaded from environment variables.
    If no checkpointer is provided, an in-memory saver is used.

    Args:
        settings: Optional configuration settings. If None, loads from env.
        checkpointer: Optional checkpoint saver. If None, uses MemorySaver.

    Returns:
        A fully configured ChatbotService ready to use

    Example:
        >>> from chatbot import create_chatbot
        >>> bot = create_chatbot()
        >>> result = bot.invoke("Recommend a gaming laptop")
    """
    if settings is None:
        settings = ChatbotSettings.from_env()

    if checkpointer is None:
        checkpointer = MemorySaver()

    components = build_chatbot_components(settings, checkpointer)
    return components.service


__all__ = [
    "ChatbotComponents",
    "build_chatbot_components",
    "create_chatbot",
]
