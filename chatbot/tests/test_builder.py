"""Unit tests for chatbot.builder — validation logic."""

import pytest

from chatbot.builder import ChatbotBuilder, OpenAIConfig


class TestOpenAIConfig:
    def test_defaults(self) -> None:
        config = OpenAIConfig(api_key="sk-test")
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.0
        assert config.embedding_model == "text-embedding-3-small"

    def test_custom_values(self) -> None:
        config = OpenAIConfig(
            api_key="sk-test",
            model="gpt-4o",
            temperature=0.5,
            embedding_model="text-embedding-3-large",
        )
        assert config.model == "gpt-4o"
        assert config.temperature == 0.5
        assert config.embedding_model == "text-embedding-3-large"


class TestChatbotBuilderValidation:
    def test_missing_openai_raises(self) -> None:
        builder = ChatbotBuilder()
        with pytest.raises(ValueError, match="OpenAI configuration is required"):
            builder.build()

    def test_missing_tavily_raises(self) -> None:
        builder = ChatbotBuilder().with_openai(api_key="sk-test")
        with pytest.raises(ValueError, match="Tavily configuration is required"):
            builder.build()

    def test_missing_repository_raises(self) -> None:
        builder = ChatbotBuilder().with_openai(api_key="sk-test").with_tavily(api_key="tvly-test")
        with pytest.raises(ValueError, match="Product repository is required"):
            builder.build()


class TestChatbotBuilderChaining:
    def test_with_openai_returns_self(self) -> None:
        builder = ChatbotBuilder()
        result = builder.with_openai(api_key="sk-test")
        assert result is builder

    def test_with_tavily_returns_self(self) -> None:
        builder = ChatbotBuilder()
        result = builder.with_tavily(api_key="tvly-test")
        assert result is builder

    def test_with_product_repository_returns_self(self) -> None:
        builder = ChatbotBuilder()
        result = builder.with_product_repository(object())
        assert result is builder

    def test_chain_all_returns_self(self) -> None:
        builder = ChatbotBuilder()
        result = (
            builder.with_openai(api_key="sk-test")
            .with_tavily(api_key="tvly-test")
            .with_product_repository(object())
        )
        assert result is builder

    def test_stores_openai_config(self) -> None:
        builder = ChatbotBuilder()
        builder.with_openai(api_key="sk-test", model="gpt-4o", temperature=0.7)
        assert builder._openai_config is not None
        assert builder._openai_config.api_key == "sk-test"
        assert builder._openai_config.model == "gpt-4o"
        assert builder._openai_config.temperature == 0.7

    def test_stores_tavily_key(self) -> None:
        builder = ChatbotBuilder()
        builder.with_tavily(api_key="tvly-test")
        assert builder._tavily_api_key == "tvly-test"

    def test_stores_repository(self) -> None:
        repo = object()
        builder = ChatbotBuilder()
        builder.with_product_repository(repo)
        assert builder._product_repository is repo
