"""OpenAI embedding service implementation."""
from typing import List

from openai import OpenAI

from chatbot.domain.ports import EmbeddingService


class OpenAIEmbeddingService:
    """EmbeddingService implementation using OpenAI's text-embedding-3-small model."""

    def __init__(self, client: OpenAI, model: str = "text-embedding-3-small") -> None:
        """Initialize the embedding service.
        
        Args:
            client: OpenAI client instance.
            model: The embedding model to use.
        """
        self._client = client
        self._model = model

    async def embed(self, text: str) -> List[float]:
        """Generate an embedding vector for the given text.
        
        Note: This uses the synchronous OpenAI client but is called from async code.
        For high-throughput scenarios, consider using AsyncOpenAI.
        """
        response = self._client.embeddings.create(input=text, model=self._model)
        return response.data[0].embedding


# Ensure the class satisfies the protocol
_: EmbeddingService = OpenAIEmbeddingService.__new__(OpenAIEmbeddingService)
