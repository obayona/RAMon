"""Composite settings object and dot-notation accessor.

Usage::

    from src.core.config import config

    # Attribute access (type-safe)
    model = config().app.openai_model

    # Dot-notation access (Laravel-style)
    model = config("app.openai_model")
    level = config("logging.level")
"""
from __future__ import annotations

from dataclasses import dataclass

from src.core.config.app import AppConfig
from src.core.config.auth import AuthConfig
from src.core.config.logging import LoggingConfig

# Module-level singleton, populated by ``load_settings()``.
_settings: Settings | None = None


@dataclass(frozen=True, slots=True)
class Settings:
    """Top-level container for all configuration sections."""

    app: AppConfig
    auth: AuthConfig
    logging: LoggingConfig

    @classmethod
    def from_env(cls) -> Settings:
        """Load all configuration sections from environment variables."""
        return cls(
            app=AppConfig.from_env(),
            auth=AuthConfig.from_env(),
            logging=LoggingConfig.from_env(),
        )


def load_settings() -> Settings:
    """Load settings from the environment and register them globally.

    Returns:
        The loaded ``Settings`` instance.
    """
    global _settings
    _settings = Settings.from_env()
    return _settings


def config(dotpath: str = "") -> Settings | object:
    """Access configuration via dot notation.

    Called without arguments, returns the full ``Settings`` instance.
    Called with a dot-separated path, walks the attribute tree and returns
    the leaf value.

    Examples::

        config()                        # → Settings instance
        config("app.openai_model")      # → "gpt-4o-mini"
        config("logging.level")         # → "INFO"
        config("auth.app_key")          # → "secret"
    """
    if _settings is None:
        raise RuntimeError(
            "Settings not loaded. Call load_settings() during application startup."
        )
    if not dotpath:
        return _settings

    obj: object = _settings
    for part in dotpath.split("."):
        obj = getattr(obj, part)
    return obj
