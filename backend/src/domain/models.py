"""Domain models representing core business entities."""
from typing import TypedDict


class Product(TypedDict):
    """Product entity representing a hardware item in the catalog."""
    
    id: int
    product_id: str
    sku: str
    name: str
    description: str
    categories: str
    price: float
    stock: int
