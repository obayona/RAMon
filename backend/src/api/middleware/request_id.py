"""Request ID middleware.

Generates a unique ``request_id`` for every HTTP request and stores it in
a ``contextvars.ContextVar`` so that ``structlog``'s ``merge_contextvars``
processor includes it in every log record.  The ID is also returned as the
``X-Request-ID`` response header so clients can correlate logs.
"""
from __future__ import annotations

import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every HTTP request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=req_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
