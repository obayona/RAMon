"""Unit tests for src.api.auth — JWT and Basic Auth utilities."""
import pytest

from src.api.auth import (
    JWTExpiredError,
    JWTValidationError,
    generate_jwt,
    validate_jwt,
    verify_basic_auth,
)
from src.core.config.auth import AuthConfig


# ---------------------------------------------------------------------------
# generate_jwt + validate_jwt round-trip
# ---------------------------------------------------------------------------

class TestJWT:
    def test_round_trip(self) -> None:
        token = generate_jwt("secret-key")
        payload = validate_jwt(token, "secret-key")
        assert "exp" in payload
        assert "iat" in payload

    def test_custom_expiry(self) -> None:
        token = generate_jwt("secret-key", expires_in_hours=1)
        payload = validate_jwt(token, "secret-key")
        assert payload["exp"] - payload["iat"] == 3600

    def test_invalid_token_raises(self) -> None:
        with pytest.raises(JWTValidationError, match="Invalid token"):
            validate_jwt("not-a-jwt", "secret-key")

    def test_wrong_key_raises(self) -> None:
        token = generate_jwt("correct-key")
        with pytest.raises(JWTValidationError):
            validate_jwt(token, "wrong-key")

    def test_expired_token_raises(self) -> None:
        token = generate_jwt("secret-key", expires_in_hours=-1)
        with pytest.raises(JWTExpiredError, match="expired"):
            validate_jwt(token, "secret-key")

    def test_returns_string_token(self) -> None:
        token = generate_jwt("key")
        assert isinstance(token, str)
        assert len(token) > 0


# ---------------------------------------------------------------------------
# verify_basic_auth
# ---------------------------------------------------------------------------

class TestVerifyBasicAuth:
    def _make_config(self) -> AuthConfig:
        return AuthConfig(app_key="key", user="admin", password="secret123")

    def test_valid_credentials(self) -> None:
        config = self._make_config()
        assert verify_basic_auth("admin", "secret123", config) is True

    def test_wrong_username(self) -> None:
        config = self._make_config()
        assert verify_basic_auth("wrong", "secret123", config) is False

    def test_wrong_password(self) -> None:
        config = self._make_config()
        assert verify_basic_auth("admin", "wrong", config) is False

    def test_both_wrong(self) -> None:
        config = self._make_config()
        assert verify_basic_auth("wrong", "wrong", config) is False

    def test_empty_credentials(self) -> None:
        config = self._make_config()
        assert verify_basic_auth("", "", config) is False
