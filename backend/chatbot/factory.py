from __future__ import annotations

from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.base import BaseCheckpointSaver
from openai import OpenAI
from pinecone import Pinecone

from chatbot.config import ChatbotSettings
from chatbot.product_catalog import PineconeProductCatalog, ProductCatalog
from chatbot.service import ChatbotService


@dataclass(slots=True)
class ChatbotComponents:
    service: ChatbotService
    product_catalog: ProductCatalog


def build_chatbot_components(
    settings: ChatbotSettings,
    checkpointer: BaseCheckpointSaver,
) -> ChatbotComponents:
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
