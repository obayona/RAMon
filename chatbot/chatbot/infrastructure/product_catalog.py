import asyncio
from typing import Optional

from pinecone import Index

from chatbot.domain.models import Product


class ProductCatalog:
    """Abstract interface for retrieving product information."""

    async def get_product(self, product_id: str) -> Optional[Product]:
        raise NotImplementedError


class PineconeProductCatalog(ProductCatalog):
    """Pinecone-backed implementation of the product catalog."""

    def __init__(self, index: Index):
        self._index = index

    async def get_product(self, product_id: str) -> Optional[Product]:
        if not product_id:
            return None

        response = await asyncio.to_thread(self._index.fetch, ids=[product_id])
        vectors = response.get("vectors") or {}
        vector = vectors.get(product_id)
        if not vector:
            return None

        metadata = vector.get("metadata") or {}

        return Product(
            id=product_id,
            name=str(metadata.get("name", "")),
            description=str(metadata.get("description", "")),
            price=float(metadata.get("price", 0.0) or 0.0),
            url=str(metadata.get("url", "")),
        )
