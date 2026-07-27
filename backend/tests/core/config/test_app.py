"""Unit tests for src.core.config.app — AppConfig.from_env()."""

import pytest

from src.core.config._base import ConfigError
from src.core.config.app import AppConfig


_VALID_ENV = {
    "DATABASE_URL": "postgresql://u:p@localhost:5432/db",
    "OPENAI_API_KEY": "sk-test",
    "TAVILY_API_KEY": "tvly-test",
}


class TestAppConfigFromEnv:
    def test_loads_all_values(self) -> None:
        config = AppConfig.from_env(_VALID_ENV)
        assert config.database_url == "postgresql://u:p@localhost:5432/db"
        assert config.openai_api_key == "sk-test"
        assert config.tavily_api_key == "tvly-test"
        assert config.openai_model == "gpt-4o-mini"
        assert config.openai_temperature == 0.0

    def test_custom_model_and_temperature(self) -> None:
        env = {**_VALID_ENV, "OPENAI_MODEL": "gpt-4o", "OPENAI_TEMPERATURE": "0.7"}
        config = AppConfig.from_env(env)
        assert config.openai_model == "gpt-4o"
        assert config.openai_temperature == 0.7

    def test_missing_openai_api_key_raises(self) -> None:
        env = {k: v for k, v in _VALID_ENV.items() if k != "OPENAI_API_KEY"}
        with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
            AppConfig.from_env(env)

    def test_missing_tavily_api_key_raises(self) -> None:
        env = {k: v for k, v in _VALID_ENV.items() if k != "TAVILY_API_KEY"}
        with pytest.raises(ConfigError, match="TAVILY_API_KEY"):
            AppConfig.from_env(env)

    def test_invalid_temperature_raises(self) -> None:
        env = {**_VALID_ENV, "OPENAI_TEMPERATURE": "not-a-number"}
        with pytest.raises(ConfigError, match="OPENAI_TEMPERATURE"):
            AppConfig.from_env(env)

    def test_empty_temperature_defaults_to_zero(self) -> None:
        env = {**_VALID_ENV, "OPENAI_TEMPERATURE": ""}
        config = AppConfig.from_env(env)
        assert config.openai_temperature == 0.0

    def test_empty_model_uses_default(self) -> None:
        env = {**_VALID_ENV, "OPENAI_MODEL": ""}
        config = AppConfig.from_env(env)
        assert config.openai_model == "gpt-4o-mini"

    def test_missing_database_raises(self) -> None:
        env = {k: v for k, v in _VALID_ENV.items() if k != "DATABASE_URL"}
        with pytest.raises(ConfigError):
            AppConfig.from_env(env)

    def test_builds_database_from_components(self) -> None:
        env = {
            "DB_USER": "user",
            "DB_PASSWORD": "pass",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "ramon",
            "OPENAI_API_KEY": "sk-test",
            "TAVILY_API_KEY": "tvly-test",
        }
        config = AppConfig.from_env(env)
        assert config.database_url == "postgresql://user:pass@localhost:5432/ramon"

    def test_frozen_dataclass(self) -> None:
        config = AppConfig.from_env(_VALID_ENV)
        with pytest.raises(AttributeError):
            config.openai_model = "gpt-4o"  # type: ignore[misc]
