from typing import Annotated, List, Optional, TypedDict

from langgraph.graph.message import add_messages


class Product(TypedDict):
    id: str
    name: str
    description: str
    price: float
    url: str
    stock: int


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_product: Optional[Product]
    recommendations: List[Product]
