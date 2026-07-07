from typing import TypedDict

class Product(TypedDict):
    id: str
    name: str
    description: str
    price: float
    url: str
    stock: int
