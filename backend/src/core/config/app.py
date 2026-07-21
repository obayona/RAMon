"""Application configuration (database, OpenAI, Tavily)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from src.core.config._base import ConfigError, build_database_url, require


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Main application configuration."""

    database_url: str
    openai_api_key: str
    tavily_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.0

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> AppConfig:
        """Load configuration from environment variables."""
        data = env or os.environ

        try:
            temperature = float(data.get("OPENAI_TEMPERATURE", "0") or 0.0)
        except ValueError as exc:
            raise ConfigError("OPENAI_TEMPERATURE must be a float") from exc

        return cls(
            database_url=build_database_url(data),
            openai_api_key=require(data, "OPENAI_API_KEY"),
            tavily_api_key=require(data, "TAVILY_API_KEY"),
            openai_model=data.get("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
            openai_temperature=temperature,
        )
