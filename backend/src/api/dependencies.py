"""FastAPI dependency injection for accessing application services.

These dependencies extract services from the FastAPI application state,
making them available to route handlers via dependency injection.

Note: We need separate functions for Request and WebSocket because FastAPI's
dependency injection uses type hints to determine how to inject parameters.
Using Union[Request, WebSocket] doesn't work with FastAPI's DI system.
"""
from __future__ import annotations

from fastapi import Request, WebSocket

from chatbot import ChatbotService
from src.core.config import AuthConfig
from src.domain.ports import ProductCatalog


def _get_state_attr(scope: Request | WebSocket, attribute: str):
    """Extract an attribute from the app state."""
    value = getattr(scope.app.state, attribute, None)
    if value is None:
        raise RuntimeError(f"{attribute} has not been initialised")
    return value


# --- Auth Config ---

def get_auth_config(request: Request) -> AuthConfig:
    """Get auth config from HTTP request."""
    return _get_state_attr(request, "auth_config")


def get_auth_config_ws(ws: WebSocket) -> AuthConfig:
    """Get auth config from WebSocket."""
    return _get_state_attr(ws, "auth_config")


# --- Chatbot Service ---

def get_chatbot_service(request: Request) -> ChatbotService:
    """Get chatbot service from HTTP request."""
    return _get_state_attr(request, "chatbot_service")


def get_chatbot_service_ws(ws: WebSocket) -> ChatbotService:
    """Get chatbot service from WebSocket."""
    return _get_state_attr(ws, "chatbot_service")


# --- Product Catalog ---

def get_product_catalog(request: Request) -> ProductCatalog:
    """Get product catalog from HTTP request."""
    return _get_state_attr(request, "product_catalog")


def get_product_catalog_ws(ws: WebSocket) -> ProductCatalog:
    """Get product catalog from WebSocket."""
    return _get_state_attr(ws, "product_catalog")
