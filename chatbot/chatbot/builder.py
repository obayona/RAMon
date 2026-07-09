"""Builder module for flexible chatbot initialization.

This module provides a Builder pattern for creating chatbot components
with sensible defaults and flexibility in choosing different implementations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from openai import OpenAI

from chatbot.application.service import ChatbotService
from chatbot.adapters import OpenAIEmbeddingService
from chatbot.domain.ports import EmbeddingService, ProductRepository


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI services (chat model and embeddings)."""
    api_key: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    embedding_model: str = "text-embedding-3-small"


class ChatbotBuilder:
    """Builder for creating ChatbotService instances with flexible configuration.
    
    The builder provides sensible defaults:
    - MemorySaver checkpointer (in-memory, great for testing/CLI)
    - OpenAI embedding service (created automatically from OpenAI config)
    
    Example usage:
    
        # Minimal setup for CLI/testing:
        chatbot = (
            ChatbotBuilder()
            .with_openai(api_key="sk-...")
            .with_tavily(api_key="tvly-...")
            .with_product_repository(PostgresProductRepository(pool))
            .build()
        )
        
        # Production with Postgres checkpointer:
        chatbot = (
            ChatbotBuilder()
            .with_openai(api_key="sk-...", model="gpt-4o")
            .with_tavily(api_key="tvly-...")
            .with_checkpointer(AsyncShallowPostgresSaver(pool))
            .with_product_repository(PostgresProductRepository(pool))
            .build()
        )
        
        # Using pre-configured clients:
        chatbot = (
            ChatbotBuilder()
            .with_openai_client(my_openai_client, model="gpt-4o")
            .with_tavily_client(my_tavily_client)
            .with_product_repository(my_repo)
            .build()
        )
        
        # Custom embedding service (for testing):
        chatbot = (
            ChatbotBuilder()
            .with_openai(api_key="sk-...")
            .with_tavily(api_key="tvly-...")
            .with_embedding_service(MockEmbeddingService())
            .with_product_repository(MockProductRepository())
            .build()
        )
    """

    def __init__(self) -> None:
        """Initialize the builder with default values."""
        self._openai_config: Optional[OpenAIConfig] = None
        self._openai_client: Optional[OpenAI] = None
        self._model: str = "gpt-4o-mini"
        self._temperature: float = 0.0
        
        self._tavily_api_key: Optional[str] = None
        self._tavily_client: Optional[TavilySearch] = None
        
        self._checkpointer: Optional[BaseCheckpointSaver] = None
        self._embedding_service: Optional[EmbeddingService] = None
        self._product_repository: Optional[ProductRepository] = None

    def with_openai(
        self,
        api_key: str,
        *,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        embedding_model: str = "text-embedding-3-small",
    ) -> ChatbotBuilder:
        """Configure OpenAI using an API key.
        
        This will create both the chat model and embedding service.
        
        Args:
            api_key: OpenAI API key.
            model: Chat model to use (default: gpt-4o-mini).
            temperature: Model temperature (default: 0.0).
            embedding_model: Embedding model (default: text-embedding-3-small).
            
        Returns:
            Self for method chaining.
        """
        self._openai_config = OpenAIConfig(
            api_key=api_key,
            model=model,
            temperature=temperature,
            embedding_model=embedding_model,
        )
        return self

    def with_openai_client(
        self,
        client: OpenAI,
        *,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        embedding_model: str = "text-embedding-3-small",
    ) -> ChatbotBuilder:
        """Configure OpenAI using a pre-configured client.
        
        Use this when you need custom client configuration or want to share
        a client instance across services.
        
        Args:
            client: Pre-configured OpenAI client.
            api_key: API key (needed for ChatOpenAI model).
            model: Chat model to use (default: gpt-4o-mini).
            temperature: Model temperature (default: 0.0).
            embedding_model: Embedding model (default: text-embedding-3-small).
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValueError: If with_openai was already called.
        """
        self._openai_client = client
        self._openai_config = OpenAIConfig(
            api_key=api_key,
            model=model,
            temperature=temperature,
            embedding_model=embedding_model,
        )
        return self

    def with_tavily(self, api_key: str, *, max_results: int = 3) -> ChatbotBuilder:
        """Configure Tavily web search using an API key.
        
        Args:
            api_key: Tavily API key.
            max_results: Maximum search results (default: 3).
            
        Returns:
            Self for method chaining.
        """
        self._tavily_api_key = api_key
        self._tavily_max_results = max_results
        return self

    def with_tavily_client(self, client: TavilySearch) -> ChatbotBuilder:
        """Configure Tavily using a pre-configured client.
        
        Args:
            client: Pre-configured TavilySearch client.
            
        Returns:
            Self for method chaining.
        """
        self._tavily_client = client
        return self

    def with_checkpointer(self, checkpointer: BaseCheckpointSaver) -> ChatbotBuilder:
        """Set the checkpointer for conversation persistence.
        
        If not called, defaults to MemorySaver (in-memory).
        
        Args:
            checkpointer: A LangGraph checkpointer (e.g., MemorySaver,
                AsyncShallowPostgresSaver).
                
        Returns:
            Self for method chaining.
        """
        self._checkpointer = checkpointer
        return self

    def with_embedding_service(self, service: EmbeddingService) -> ChatbotBuilder:
        """Set a custom embedding service.
        
        If not called, an OpenAIEmbeddingService is created automatically
        from the OpenAI configuration.
        
        Args:
            service: An implementation of the EmbeddingService protocol.
            
        Returns:
            Self for method chaining.
        """
        self._embedding_service = service
        return self

    def with_product_repository(self, repository: ProductRepository) -> ChatbotBuilder:
        """Set the product repository for product data access.
        
        This is required and must be called before build().
        
        Args:
            repository: An implementation of the ProductRepository protocol.
            
        Returns:
            Self for method chaining.
        """
        self._product_repository = repository
        return self

    def build(self) -> ChatbotService:
        """Build the ChatbotService with the configured options.
        
        Returns:
            A fully configured ChatbotService instance.
            
        Raises:
            ValueError: If required configuration is missing.
        """
        # Validate OpenAI configuration
        if self._openai_config is None:
            raise ValueError(
                "OpenAI configuration is required. "
                "Call with_openai(api_key=...) or with_openai_client(client, api_key=...)."
            )
        
        # Validate Tavily configuration
        if self._tavily_api_key is None and self._tavily_client is None:
            raise ValueError(
                "Tavily configuration is required. "
                "Call with_tavily(api_key=...) or with_tavily_client(client)."
            )
        
        # Validate product repository
        if self._product_repository is None:
            raise ValueError(
                "Product repository is required. "
                "Call with_product_repository(repository)."
            )

        # Create or use OpenAI client
        openai_client = self._openai_client or OpenAI(api_key=self._openai_config.api_key)
        
        # Create chat model
        chat_model = ChatOpenAI(
            model=self._openai_config.model,
            temperature=self._openai_config.temperature,
            api_key=self._openai_config.api_key,
        )
        
        # Create Tavily client if not provided
        tavily_client = self._tavily_client or TavilySearch(
            max_results=getattr(self, '_tavily_max_results', 3),
            tavily_api_key=self._tavily_api_key,
        )
        
        # Create embedding service if not provided
        if self._embedding_service is None:
            embedding_service = OpenAIEmbeddingService(
                openai_client, 
                model=self._openai_config.embedding_model,
            )
        else:
            embedding_service = self._embedding_service
        
        # Use MemorySaver as default checkpointer
        checkpointer = self._checkpointer or MemorySaver()

        # Build and return the service
        return ChatbotService(
            openai_client=openai_client,
            chat_model=chat_model,
            checkpointer=checkpointer,
            tavily_client=tavily_client,
            embedding_service=embedding_service,
            product_repository=self._product_repository,
        )
