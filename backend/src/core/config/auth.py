"""Authentication configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass

from src.core.config._base import require


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
        return cls(
            app_key=require(data, "APP_KEY"),
            user=require(data, "GUEST_USER"),
            password=require(data, "GUEST_PASSWORD"),
        )
