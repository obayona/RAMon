"""Base configuration utilities.

Shared helpers used by all config dataclasses: the ``ConfigError`` exception,
a ``require()`` helper for mandatory env vars, and a ``_build_database_url()``
utility.
"""
from __future__ import annotations


class ConfigError(RuntimeError):
    """Raised when required environment configuration is missing or invalid."""


def require(data: dict[str, str], key: str) -> str:
    """Return the value of *key* from *data*, raising ``ConfigError`` if absent.

    Args:
        data: Environment-like mapping.
        key: Variable name to look up.

    Returns:
        The stripped value.

    Raises:
        ConfigError: If the key is missing or blank.
    """
    value = data.get(key, "").strip()
    if not value:
        raise ConfigError(f"Environment variable '{key}' is required")
    return value


def build_database_url(data: dict[str, str]) -> str:
    """Build DATABASE_URL from individual components or use existing value.

    If ``DATABASE_URL`` is set, use it directly.  Otherwise, build it from
    ``DB_USER``, ``DB_PASSWORD``, ``DB_HOST``, ``DB_PORT``, and ``DB_NAME``.
    """
    existing_url = data.get("DATABASE_URL", "").strip()
    if existing_url:
        return existing_url

    required_keys = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
    missing = [k for k in required_keys if not data.get(k, "").strip()]
    if missing:
        raise ConfigError(
            f"Either DATABASE_URL or all of {required_keys} must be set. "
            f"Missing: {missing}"
        )

    return (
        f"postgresql://{data['DB_USER']}:{data['DB_PASSWORD']}"
        f"@{data['DB_HOST']}:{data['DB_PORT']}/{data['DB_NAME']}"
    )
