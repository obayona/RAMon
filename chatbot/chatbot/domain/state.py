from typing import Annotated, List, Optional, TypedDict

from langgraph.graph.message import add_messages
from chatbot.domain.product import Product

class ChatbotState(TypedDict):
    messages: Annotated[list, add_messages]
    current_product: Optional[Product]
    recommendations: List[Product]
