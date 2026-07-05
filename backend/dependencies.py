"""FastAPI dependency injection helpers for the chatbot service.

These dependencies extract the chatbot service and product catalog from
the FastAPI application state, making them available to route handlers.
"""
from __future__ import annotations

from typing import Any, cast

from fastapi import Request, WebSocket

from chatbot import ChatbotService, ProductCatalog


def _get_state_attr(scope: Any, attribute: str) -> Any:
    if not hasattr(scope, "app"):
        raise RuntimeError("Dependency scope does not expose an app instance")
    app = scope.app
    value = getattr(app.state, attribute, None)
    if value is None:
        raise RuntimeError(f"{attribute} has not been initialised")
    return value


def _resolve_chatbot_service(scope: Any) -> ChatbotService:
    service = _get_state_attr(scope, "chatbot_service")
    if not isinstance(service, ChatbotService):
        raise RuntimeError(
            "chatbot_service has been initialised with an unexpected type"
        )
    return cast(ChatbotService, service)


def _resolve_product_catalog(scope: Any) -> ProductCatalog:
    catalog = _get_state_attr(scope, "product_catalog")
    if not isinstance(catalog, ProductCatalog):
        raise RuntimeError(
            "product_catalog has been initialised with an unexpected type"
        )
    return cast(ProductCatalog, catalog)


def get_chatbot_service(request: Request) -> ChatbotService:
    return _resolve_chatbot_service(request)


def get_chatbot_service_ws(ws: WebSocket) -> ChatbotService:
    return _resolve_chatbot_service(ws)


def get_product_catalog(request: Request) -> ProductCatalog:
    return _resolve_product_catalog(request)


def get_product_catalog_ws(ws: WebSocket) -> ProductCatalog:
    return _resolve_product_catalog(ws)
