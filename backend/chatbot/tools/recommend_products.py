import json
from typing import Optional

from langchain_core.tools import tool
from openai import OpenAI
from pinecone import Index

from chatbot.state import Product


def make_recommend_products(openai_client: OpenAI, pinecone_index: Index):
    """Create the ``recommend_products`` tool with pre-configured clients."""

    @tool
    def recommend_products(
        query: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> str:
        """Search for hardware products using semantic similarity with optional price filtering.

        The query is embedded with ``text-embedding-3-small`` and searched against the
        ``ramon-products`` Pinecone index.  ``min_price`` / ``max_price`` are applied as
        ``$gte`` / ``$lte`` metadata filters.  Returns the top 3 products as a JSON array."""
        metadata_filter = {}
        if min_price is not None:
            metadata_filter["price"] = {"$gte": min_price}
        if max_price is not None:
            metadata_filter["price"] = {"$lte": max_price}

        embedding = (
            openai_client.embeddings.create(
                input=query, model="text-embedding-3-small"
            )
            .data[0]
            .embedding
        )

        response = pinecone_index.query(
            vector=embedding,
            top_k=3,
            include_metadata=True,
            filter=metadata_filter or None,
        )
        products: list[Product] = []
        for match in response.matches:
            meta = match.metadata
            products.append(
                {
                    "id": match.id,
                    "name": meta.get("name", ""),
                    "description": meta.get("description", ""),
                    "price": meta.get("price", 0.0),
                    "url": meta.get("url", ""),
                }
            )

        return json.dumps(products, indent=2)

    return recommend_products
