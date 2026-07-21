"""Port interfaces (abstractions) for external dependencies.

This module defines Protocol classes that allow the chatbot to work with
different implementations of external services (e.g., databases, embedding
providers). This enables easier testing and flexibility in deployment.
"""
from typing import List, Optional, Protocol, runtime_checkable

from chatbot.domain.product import Product


@runtime_checkable
class EmbeddingService(Protocol):
    """Protocol for generating text embeddings."""

    async def embed(self, text: str) -> List[float]:
        """Generate an embedding vector for the given text.
        
        Args:
            text: The text to embed.
            
        Returns:
            A list of floats representing the embedding vector.
        """
        ...


@runtime_checkable
class ProductRepository(Protocol):
    """Protocol for accessing product data with semantic search."""

    async def search_by_similarity(
        self,
        embedding: List[float],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_similarity: Optional[float] = None,
        limit: int = 3,
    ) -> List[Product]:
        """Search for products by embedding similarity with optional price filtering.
        
        Args:
            embedding: The embedding vector to search against.
            min_price: Optional minimum price filter.
            max_price: Optional maximum price filter.
            min_similarity: Optional minimum cosine similarity (0.0-1.0).
            limit: Maximum number of results to return.
            
        Returns:
            A list of matching products ordered by similarity.
        """
        ...


__all__ = ["EmbeddingService", "ProductRepository"]
