"""Port interfaces (abstractions) for external dependencies.

These protocols define the contracts that adapters must implement,
allowing the domain layer to remain independent of infrastructure details.
"""
from typing import Optional, Protocol, runtime_checkable

from src.domain.models import Product


@runtime_checkable
class ProductCatalog(Protocol):
    """Abstract interface for retrieving product information."""

    async def get_product(self, product_id: str) -> Optional[Product]:
        """Retrieve a product by its ID.
        
        Args:
            product_id: The unique product identifier.
            
        Returns:
            The product if found, None otherwise.
        """
        ...
