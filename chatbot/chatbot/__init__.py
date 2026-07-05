"""RAMon Chatbot - Technical assistance chatbot for computer e-commerce.

This is the shared chatbot library used by both the backend server and CLI tools.

Quick Start:
    >>> from chatbot import create_chatbot
    >>> bot = create_chatbot()  # Loads settings from environment
    >>> result = bot.invoke("Recommend a gaming laptop under $1000")

For more control over initialization:
    >>> from chatbot import ChatbotSettings, build_chatbot_components
    >>> from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    >>> settings = ChatbotSettings.from_env()
    >>> async with AsyncSqliteSaver.from_conn_string(settings.sqlite_path) as saver:
    ...     components = build_chatbot_components(settings, saver)
    ...     service = components.service
"""
from chatbot.application.service import ChatbotService, ChatNotFoundError
from chatbot.config import ChatbotSettings, ConfigError
from chatbot.domain.models import AgentState, Product
from chatbot.factory import ChatbotComponents, build_chatbot_components, create_chatbot
from chatbot.graph_utils import generate_graph_image, save_graph_image
from chatbot.infrastructure.product_catalog import PineconeProductCatalog, ProductCatalog

__all__ = [
    # Main factory functions
    "create_chatbot",
    "build_chatbot_components",
    "ChatbotComponents",
    # Service
    "ChatbotService",
    "ChatNotFoundError",
    # Configuration
    "ChatbotSettings",
    "ConfigError",
    # Domain models
    "AgentState",
    "Product",
    # Infrastructure
    "ProductCatalog",
    "PineconeProductCatalog",
    # Utilities
    "generate_graph_image",
    "save_graph_image",
]
