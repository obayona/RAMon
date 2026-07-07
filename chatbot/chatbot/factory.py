"""Factory module for easy chatbot initialization.

This module provides convenient factory functions to create chatbot components
with minimal boilerplate. It handles all the wiring of external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.postgres.aio import AsyncShallowPostgresSaver
from openai import OpenAI
from chatbot.application.service import ChatbotService
from chatbot.application.settings import ChatbotSettings

def build_chatbot(settings: ChatbotSettings) -> ChatbotService:
    """Build the chatbot

    Args:
        settings: Configuration settings

    Returns:
        ChatbotService
    """
    openai_client = OpenAI(api_key=settings["openai_api_key"])
    tavily_client = TavilySearch(max_results=3, tavily_api_key=settings["tavily_api_key"])
    chat_model = ChatOpenAI(
        model=settings["openai_model"],
        temperature=settings["openai_temperature"],
        api_key=settings["openai_api_key"],
    )

    checkpointer = AsyncShallowPostgresSaver(settings["db_pool"])

    service = ChatbotService(
        openai_client=openai_client,
        chat_model=chat_model,
        db_pool=settings["db_pool"],
        checkpointer=checkpointer,
        tavily_client=tavily_client,
    )

    return service
