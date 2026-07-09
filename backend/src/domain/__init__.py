"""Domain layer - Business entities and port interfaces."""
from src.domain.models import Product
from src.domain.ports import ProductCatalog

__all__ = ["Product", "ProductCatalog"]
