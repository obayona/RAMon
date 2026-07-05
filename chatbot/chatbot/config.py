from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when required environment configuration is missing or invalid."""


@dataclass(slots=True)
class ChatbotSettings:
    sqlite_path: str
    openai_api_key: str
    pinecone_api_key: str
    tavily_api_key: str
    pinecone_index_name: str = "ramon-products"
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.0

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "ChatbotSettings":
        data = env or os.environ

        def require(key: str) -> str:
            value = data.get(key, "").strip()
            if not value:
                raise ConfigError(f"Environment variable '{key}' is required")
            return value

        try:
            temperature = float(data.get("OPENAI_TEMPERATURE", "0") or 0.0)
        except ValueError as exc:
            raise ConfigError("OPENAI_TEMPERATURE must be a float") from exc

        return cls(
            sqlite_path=require("SQLITE_PATH"),
            openai_api_key=require("OPENAI_API_KEY"),
            pinecone_api_key=require("PINECONE_API_KEY"),
            tavily_api_key=require("TAVILY_API_KEY"),
            pinecone_index_name=data.get("PINECONE_INDEX_NAME", "ramon-products"),
            openai_model=data.get("OPENAI_MODEL", "gpt-4o-mini"),
            openai_temperature=temperature,
        )
