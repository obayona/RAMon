"""Application configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when required environment configuration is missing or invalid."""


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
            database_url=require("DATABASE_URL"),
            openai_api_key=require("OPENAI_API_KEY"),
            tavily_api_key=require("TAVILY_API_KEY"),
            openai_model=data.get("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
            openai_temperature=temperature,
        )


@dataclass(frozen=True, slots=True)
class AuthConfig:
    """Authentication configuration."""
    
    app_key: str
    user: str
    password: str

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> AuthConfig:
        """Load authentication settings from environment variables."""
        data = env or os.environ

        def require(key: str) -> str:
            value = data.get(key, "").strip()
            if not value:
                raise ConfigError(f"Environment variable '{key}' is required")
            return value

        return cls(
            app_key=require("APP_KEY"),
            user=require("GUEST_USER"),
            password=require("GUEST_PASSWORD"),
        )
