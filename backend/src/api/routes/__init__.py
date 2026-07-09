"""API route definitions."""
from src.api.routes.chat import router as chat_router
from src.api.routes.root import router as root_router
from src.api.routes.websocket import router as websocket_router

__all__ = ["chat_router", "root_router", "websocket_router"]
