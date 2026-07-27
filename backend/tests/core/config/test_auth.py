"""Unit tests for src.core.config.auth — AuthConfig.from_env()."""
import pytest

from src.core.config._base import ConfigError
from src.core.config.auth import AuthConfig


_VALID_ENV = {
    "APP_KEY": "my-secret-key",
    "GUEST_USER": "guest",
    "GUEST_PASSWORD": "pass123",
}


class TestAuthConfigFromEnv:
    def test_loads_all_values(self) -> None:
        config = AuthConfig.from_env(_VALID_ENV)
        assert config.app_key == "my-secret-key"
        assert config.user == "guest"
        assert config.password == "pass123"

    def test_missing_app_key_raises(self) -> None:
        env = {k: v for k, v in _VALID_ENV.items() if k != "APP_KEY"}
        with pytest.raises(ConfigError, match="APP_KEY"):
            AuthConfig.from_env(env)

    def test_missing_user_raises(self) -> None:
        env = {k: v for k, v in _VALID_ENV.items() if k != "GUEST_USER"}
        with pytest.raises(ConfigError, match="GUEST_USER"):
            AuthConfig.from_env(env)

    def test_missing_password_raises(self) -> None:
        env = {k: v for k, v in _VALID_ENV.items() if k != "GUEST_PASSWORD"}
        with pytest.raises(ConfigError, match="GUEST_PASSWORD"):
            AuthConfig.from_env(env)

    def test_frozen_dataclass(self) -> None:
        config = AuthConfig.from_env(_VALID_ENV)
        with pytest.raises(AttributeError):
            config.user = "other"  # type: ignore[misc]

    def test_strips_whitespace(self) -> None:
        env = {**_VALID_ENV, "APP_KEY": "  key  "}
        config = AuthConfig.from_env(env)
        assert config.app_key == "key"
