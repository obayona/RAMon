"""Authentication module for JWT validation and basic authentication.

This module provides helper functions for securing API endpoints
using JWT tokens and HTTP Basic Authentication.
"""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


@dataclass(frozen=True)
class AuthSettings:
    """Authentication configuration loaded from environment variables."""
    
    app_key: str
    user: str
    password: str
    
    @classmethod
    def from_env(cls) -> "AuthSettings":
        """Load authentication settings from environment variables."""
        app_key = os.getenv("APP_KEY")
        user = os.getenv("GUEST_USER")
        password = os.getenv("GUEST_PASSWORD")
        
        if not app_key:
            raise ValueError("APP_KEY environment variable is required")
        if not user:
            raise ValueError("GUEST_USER environment variable is required")
        if not password:
            raise ValueError("GUEST_PASSWORD environment variable is required")
        
        return cls(app_key=app_key, user=user, password=password)


class JWTValidationError(Exception):
    """Raised when JWT validation fails."""
    pass


class JWTExpiredError(JWTValidationError):
    """Raised when JWT has expired."""
    pass


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


def verify_basic_auth(username: str, password: str, settings: AuthSettings) -> bool:
    """Verify basic authentication credentials.
    
    Uses constant-time comparison to prevent timing attacks.
    
    Args:
        username: The provided username.
        password: The provided password.
        settings: The authentication settings containing valid credentials.
        
    Returns:
        True if credentials are valid, False otherwise.
    """
    username_valid = secrets.compare_digest(username, settings.user)
    password_valid = secrets.compare_digest(password, settings.password)
    return username_valid and password_valid
