"""JWT Bearer authentication dependency."""
from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from src.api.auth import JWTExpiredError, JWTValidationError, validate_jwt
from src.api.dependencies import get_auth_config

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
