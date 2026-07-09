"""Adapters implementing the domain port interfaces.

This module provides concrete implementations of the Protocol classes
defined in the domain layer.
"""
from chatbot.adapters.embedding import OpenAIEmbeddingService
from chatbot.adapters.product_repository import PostgresProductRepository

__all__ = [
    "OpenAIEmbeddingService",
    "PostgresProductRepository",
]
