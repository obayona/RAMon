"""Logging configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Logging configuration loaded from environment variables."""

    level: str = "INFO"
    fmt: str = "text"
    log_dir: str | None = None

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> LoggingConfig:
        """Load logging settings from environment variables."""
        data = env or os.environ
        level = data.get("LOG_LEVEL", "INFO").upper()
        fmt = data.get("LOG_FORMAT", "text").lower()
        log_dir = data.get("LOG_DIR", "").strip() or None
        return cls(level=level, fmt=fmt, log_dir=log_dir)
