"""WebSocket JWT authentication dependency."""
from __future__ import annotations

from fastapi import WebSocket, WebSocketException
from starlette import status

from src.api.auth import JWTExpiredError, JWTValidationError, validate_jwt
from src.api.dependencies import get_auth_config_ws


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
