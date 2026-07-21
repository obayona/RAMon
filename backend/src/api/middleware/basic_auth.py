"""HTTP Basic Authentication dependency."""
from __future__ import annotations

import base64
import binascii

from fastapi import HTTPException, Request
from starlette import status

from src.api.auth import verify_basic_auth
from src.api.dependencies import get_auth_config
from src.core.config import AuthConfig


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
