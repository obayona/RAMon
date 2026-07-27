"""Unit tests for src.core.config.settings — Settings and config()."""
import pytest

from src.core.config.app import AppConfig
from src.core.config.auth import AuthConfig
from src.core.config.logging import LoggingConfig
from src.core.config.settings import Settings, config


_VALID_ENV = {
    "DATABASE_URL": "postgresql://u:p@localhost:5432/db",
    "OPENAI_API_KEY": "sk-test",
    "TAVILY_API_KEY": "tvly-test",
    "APP_KEY": "key",
    "GUEST_USER": "user",
    "GUEST_PASSWORD": "pass",
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": "text",
}


class TestSettings:
    def test_from_env(self) -> None:
        import os
        saved = {k: os.environ.get(k) for k in _VALID_ENV}
        try:
            os.environ.update(_VALID_ENV)
            settings = Settings.from_env()
            assert isinstance(settings.app, AppConfig)
            assert isinstance(settings.auth, AuthConfig)
            assert isinstance(settings.logging, LoggingConfig)
        finally:
            for k in _VALID_ENV:
                if saved[k] is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = saved[k]

    def test_frozen(self) -> None:
        app = AppConfig.from_env(_VALID_ENV)
        auth = AuthConfig.from_env(_VALID_ENV)
        logging_cfg = LoggingConfig()
        settings = Settings(app=app, auth=auth, logging=logging_cfg)
        with pytest.raises(AttributeError):
            settings.app = app  # type: ignore[misc]


class TestConfigAccessor:
    def test_no_args_returns_settings(self) -> None:
        import src.core.config.settings as mod
        old = mod._settings
        try:
            app = AppConfig.from_env(_VALID_ENV)
            auth = AuthConfig.from_env(_VALID_ENV)
            mod._settings = Settings(app=app, auth=auth, logging=LoggingConfig())
            result = config()
            assert isinstance(result, Settings)
        finally:
            mod._settings = old

    def test_dotpath_returns_value(self) -> None:
        import src.core.config.settings as mod
        old = mod._settings
        try:
            app = AppConfig.from_env(_VALID_ENV)
            auth = AuthConfig.from_env(_VALID_ENV)
            mod._settings = Settings(app=app, auth=auth, logging=LoggingConfig())
            assert config("app.openai_model") == "gpt-4o-mini"
            assert config("logging.level") == "INFO"
        finally:
            mod._settings = old

    def test_before_load_raises(self) -> None:
        import src.core.config.settings as mod
        old = mod._settings
        try:
            mod._settings = None
            with pytest.raises(RuntimeError, match="Settings not loaded"):
                config()
        finally:
            mod._settings = old

    def test_invalid_dotpath_raises(self) -> None:
        import src.core.config.settings as mod
        old = mod._settings
        try:
            app = AppConfig.from_env(_VALID_ENV)
            auth = AuthConfig.from_env(_VALID_ENV)
            mod._settings = Settings(app=app, auth=auth, logging=LoggingConfig())
            with pytest.raises(AttributeError):
                config("nonexistent.path")
        finally:
            mod._settings = old
