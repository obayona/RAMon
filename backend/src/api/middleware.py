"""Authentication middleware for FastAPI routes.

This module provides FastAPI dependencies for JWT and Basic Authentication,
keeping authentication concerns separate from business logic.
"""
from __future__ import annotations

import base64
import binascii

from fastapi import HTTPException, Request, WebSocket, WebSocketException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from src.api.auth import (
    JWTExpiredError,
    JWTValidationError,
    validate_jwt,
    verify_basic_auth,
)
from src.api.dependencies import get_auth_config, get_auth_config_ws
from src.core.config import AuthConfig

# Security scheme for JWT Bearer tokens
_bearer_scheme = HTTPBearer(auto_error=False)


async def require_jwt(request: Request) -> dict:
    """Dependency that validates JWT Bearer token from Authorization header.
    
    Returns:
        The decoded JWT payload if valid.
    
    Raises:
        HTTPException: 401 if token is missing, invalid, or expired.
    """
    credentials: HTTPAuthorizationCredentials | None = await _bearer_scheme(request)

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_config = get_auth_config(request)

    try:
        payload = validate_jwt(credentials.credentials, auth_config.app_key)
        return payload
    except JWTExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_basic_auth(request: Request) -> AuthConfig:
    """Dependency that validates HTTP Basic Authentication.
    
    Triggers browser's built-in authentication prompt if credentials
    are missing or invalid.
    
    Returns:
        AuthConfig if credentials are valid.
    
    Raises:
        HTTPException: 401 if credentials are missing or invalid.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Basic "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": 'Basic realm="RAMon Chatbot"'},
        )

    try:
        encoded_credentials = auth_header[6:]  # Remove "Basic " prefix
        decoded = base64.b64decode(encoded_credentials).decode("utf-8")
        username, password = decoded.split(":", 1)
    except (binascii.Error, ValueError, UnicodeDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials format",
            headers={"WWW-Authenticate": 'Basic realm="RAMon Chatbot"'},
        )

    auth_config = get_auth_config(request)

    if not verify_basic_auth(username, password, auth_config):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": 'Basic realm="RAMon Chatbot"'},
        )

    return auth_config


def validate_websocket_token(ws: WebSocket) -> dict:
    """Validate JWT token from WebSocket query parameters.
    
    Args:
        ws: The WebSocket connection.
        
    Returns:
        The decoded JWT payload if valid.
        
    Raises:
        WebSocketException: If token is missing, invalid, or expired.
    """
    token = ws.query_params.get("token", "").strip()
    if not token:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="token query parameter is required",
        )

    auth_config = get_auth_config_ws(ws)
    try:
        return validate_jwt(token, auth_config.app_key)
    except JWTExpiredError:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Token has expired",
        )
    except JWTValidationError as exc:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(exc),
        )
