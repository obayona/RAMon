"""Configuration package.

Provides ``Settings`` (composite), individual config dataclasses, and the
``config()`` dot-notation accessor.

Usage::

    from src.core.config import config, load_settings, Settings, ConfigError

    # At startup
    settings = load_settings()          # or Settings.from_env()

    # Access
    config("app.openai_model")          # dot-notation
    config().app.openai_model           # attribute access
"""
from src.core.config._base import ConfigError
from src.core.config.app import AppConfig
from src.core.config.auth import AuthConfig
from src.core.config.logging import LoggingConfig
from src.core.config.settings import Settings, config, load_settings

__all__ = [
    "AppConfig",
    "AuthConfig",
    "ConfigError",
    "LoggingConfig",
    "Settings",
    "config",
    "load_settings",
]
