from typing import Annotated, List, Optional, TypedDict

from langgraph.graph.message import add_messages


class Product(TypedDict):
    id: int
    product_id: str
    sku: str
    name: str
    description: str
    categories: str
    price: float
    stock: int
    in_stock: bool
    url: str
    image_url: str
    status: str
    similarity: Optional[float]


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_product: Optional[Product]
    recommendations: List[Product]
