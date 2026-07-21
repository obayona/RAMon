#!/usr/bin/env python3
"""Generate an image of the chatbot graph.

This script creates a visual representation of the LangGraph workflow
and saves it as graph.png.

Usage:
    python show_graph.py [output_path]

Arguments:
    output_path  Optional path for the output image (default: ../chatbot/graph.png)

Requires:
    - .env file with OPENAI_API_KEY and TAVILY_API_KEY
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from chatbot import ChatbotBuilder, save_graph_image
from chatbot.domain.ports import ProductRepository, EmbeddingService


class _MockProductRepository(ProductRepository):
    """Minimal mock repository for graph visualization only."""

    async def search_by_similarity(self, **kwargs):
        return []


class _MockEmbeddingService(EmbeddingService):
    """Minimal mock embedding service for graph visualization only."""

    async def embed(self, text: str):
        return [0.0] * 1536


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "../chatbot/graph.png"
    output_path = Path(output_path)

    print("Initializing chatbot...")
    bot = (
        ChatbotBuilder()
        .with_openai(api_key=os.environ.get("OPENAI_API_KEY", "sk-fake"))
        .with_tavily(api_key=os.environ.get("TAVILY_API_KEY", "tvly-fake"))
        .with_product_repository(_MockProductRepository())
        .with_embedding_service(_MockEmbeddingService())
        .build()
    )

    print("Generating graph image...")
    saved_path = save_graph_image(bot, output_path)

    print(f"Graph saved to {saved_path.resolve()}")


if __name__ == "__main__":
    main()
