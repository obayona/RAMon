"""Unit tests for src.core.config._base — require(), build_database_url()."""
import pytest

from src.core.config._base import ConfigError, build_database_url, require


# ---------------------------------------------------------------------------
# require()
# ---------------------------------------------------------------------------

class TestRequire:
    def test_returns_stripped_value(self) -> None:
        assert require({"KEY": "  hello  "}, "KEY") == "hello"

    def test_missing_key_raises(self) -> None:
        with pytest.raises(ConfigError, match="'MISSING' is required"):
            require({}, "MISSING")

    def test_empty_value_raises(self) -> None:
        with pytest.raises(ConfigError):
            require({"KEY": ""}, "KEY")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ConfigError):
            require({"KEY": "   "}, "KEY")

    def test_non_string_value_stripped(self) -> None:
        result = require({"KEY": "value"}, "KEY")
        assert result == "value"


# ---------------------------------------------------------------------------
# build_database_url()
# ---------------------------------------------------------------------------

class TestBuildDatabaseUrl:
    def test_existing_database_url_used_directly(self) -> None:
        url = "postgresql://user:pass@host:5432/db"
        result = build_database_url({"DATABASE_URL": url})
        assert result == url

    def test_existing_database_url_with_whitespace(self) -> None:
        url = "  postgresql://user:pass@host:5432/db  "
        result = build_database_url({"DATABASE_URL": url})
        assert result == "postgresql://user:pass@host:5432/db"

    def test_builds_from_components(self) -> None:
        env = {
            "DB_USER": "admin",
            "DB_PASSWORD": "secret",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "ramon",
        }
        result = build_database_url(env)
        assert result == "postgresql://admin:secret@localhost:5432/ramon"

    def test_missing_components_raises(self) -> None:
        env = {"DB_USER": "admin", "DB_HOST": "localhost"}
        with pytest.raises(ConfigError, match="Missing"):
            build_database_url(env)

    def test_empty_dict_raises(self) -> None:
        with pytest.raises(ConfigError):
            build_database_url({})

    def test_partial_components_raises_with_all_missing(self) -> None:
        env = {"DB_USER": "admin"}
        with pytest.raises(ConfigError, match="Missing"):
            build_database_url(env)

    def test_empty_component_raises(self) -> None:
        env = {
            "DB_USER": "admin",
            "DB_PASSWORD": "",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "ramon",
        }
        with pytest.raises(ConfigError, match="Missing"):
            build_database_url(env)
