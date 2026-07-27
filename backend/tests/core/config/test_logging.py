"""Unit tests for src.core.config.logging — LoggingConfig.from_env()."""
import pytest

from src.core.config.logging import LoggingConfig


class TestLoggingConfigFromEnv:
    def test_defaults(self) -> None:
        config = LoggingConfig.from_env({})
        assert config.level == "INFO"
        assert config.fmt == "text"
        assert config.log_dir is None

    def test_custom_level_uppercased(self) -> None:
        config = LoggingConfig.from_env({"LOG_LEVEL": "debug"})
        assert config.level == "DEBUG"

    def test_custom_fmt_lowercased(self) -> None:
        config = LoggingConfig.from_env({"LOG_FORMAT": "JSON"})
        assert config.fmt == "json"

    def test_log_dir_set(self) -> None:
        config = LoggingConfig.from_env({"LOG_DIR": "/var/log/ramon"})
        assert config.log_dir == "/var/log/ramon"

    def test_empty_log_dir_becomes_none(self) -> None:
        config = LoggingConfig.from_env({"LOG_DIR": ""})
        assert config.log_dir is None

    def test_whitespace_log_dir_becomes_none(self) -> None:
        config = LoggingConfig.from_env({"LOG_DIR": "   "})
        assert config.log_dir is None

    def test_partial_env(self) -> None:
        config = LoggingConfig.from_env({"LOG_LEVEL": "warning"})
        assert config.level == "WARNING"
        assert config.fmt == "text"
        assert config.log_dir is None

    def test_frozen_dataclass(self) -> None:
        config = LoggingConfig()
        with pytest.raises(AttributeError):
            config.level = "DEBUG"  # type: ignore[misc]
