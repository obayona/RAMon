"""Chatbot state definitions for LangGraph workflow."""
from typing import Annotated, List, Optional, TypedDict

from langgraph.graph.message import add_messages
from chatbot.domain.product import Product


class ChatbotState(TypedDict):
    """State schema for the chatbot graph.

    Attributes:
        messages: Conversation history with LangGraph message reducer.
        current_product: Product the user is currently viewing (optional context).
        recommendations: Products retrieved from recommend_products tool.
        product_query: The query used by recommend_products for relevance checking.
        original_query: The user's raw first message, used for language detection.
    """

    messages: Annotated[list, add_messages]
    current_product: Optional[Product]
    recommendations: List[Product]
    product_query: Optional[str]
    original_query: Optional[str]
