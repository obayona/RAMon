"""Domain models representing core business entities."""
from typing import TypedDict


class Product(TypedDict):
    """Product entity representing a hardware item in the catalog."""
    
    id: str
    name: str
    description: str
    price: float
    url: str
    stock: int
