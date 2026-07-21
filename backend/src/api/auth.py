"""Authentication utilities for JWT and Basic Auth.

This module provides functions for generating and validating JWT tokens,
as well as verifying HTTP Basic Authentication credentials.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from src.core.config.auth import AuthConfig


class JWTValidationError(Exception):
    """Raised when JWT validation fails."""


class JWTExpiredError(JWTValidationError):
    """Raised when JWT has expired."""


def generate_jwt(secret_key: str, expires_in_hours: int = 24) -> str:
    """Generate a JWT token.
    
    Args:
        secret_key: The secret key used to sign the token.
        expires_in_hours: Token expiration time in hours (default: 24).
        
    Returns:
        The encoded JWT token string.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "iat": now,
        "exp": now + timedelta(hours=expires_in_hours),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def validate_jwt(token: str, secret_key: str) -> dict:
    """Validate a JWT token and return its payload.
    
    Args:
        token: The JWT token to validate.
        secret_key: The secret key used to decode the token.
        
    Returns:
        The decoded token payload.
        
    Raises:
        JWTExpiredError: If the token has expired.
        JWTValidationError: If the token is invalid.
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError as exc:
        raise JWTExpiredError("Token has expired") from exc
    except InvalidTokenError as exc:
        raise JWTValidationError(f"Invalid token: {exc}") from exc


def verify_basic_auth(username: str, password: str, config: AuthConfig) -> bool:
    """Verify basic authentication credentials.
    
    Uses constant-time comparison to prevent timing attacks.
    
    Args:
        username: The provided username.
        password: The provided password.
        config: The authentication config containing valid credentials.
        
    Returns:
        True if credentials are valid, False otherwise.
    """
    username_valid = secrets.compare_digest(username, config.user)
    password_valid = secrets.compare_digest(password, config.password)
    return username_valid and password_valid
