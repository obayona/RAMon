"""WebSocket route for real-time chat."""
import json
import logging
from dataclasses import dataclass

from fastapi import APIRouter, Depends, WebSocket, WebSocketException
from starlette import status
from starlette.websockets import WebSocketDisconnect

from chatbot import ChatbotService
from src.api.dependencies import get_chatbot_service_ws, get_product_catalog_ws
from src.api.middleware import validate_websocket_token
from src.domain.ports import ProductCatalog

router = APIRouter(tags=["websocket"])
logger = logging.getLogger("ramon.websocket")


@dataclass
class ChatMessage:
    """Parsed chat message from WebSocket payload."""

    message: str
    current_product_id: str | None

    @classmethod
    def from_raw(cls, raw: str) -> "ChatMessage":
        """Parse a raw WebSocket message into a ChatMessage."""
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"message": raw, "current_product_id": None}

        message = payload.get("message", "").strip()
        current_product_id = (payload.get("current_product_id") or "").strip() or None

        return cls(message=message, current_product_id=current_product_id)


def _validate_chat_id(ws: WebSocket) -> str:
    """Extract and validate chat_id from WebSocket query parameters."""
    chat_id = ws.query_params.get("chat_id", "").strip()
    if not chat_id:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="chat_id query parameter is required",
        )
    return chat_id


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    chatbot_service: ChatbotService = Depends(get_chatbot_service_ws),
    product_catalog: ProductCatalog = Depends(get_product_catalog_ws),
):
    """Bi-directional chat channel used by the frontend.

    The client must supply a `chat_id` query parameter and a valid JWT token
    via the `token` query parameter when opening the connection
    (for example `/ws?chat_id=abc123&token=eyJ...`).

    Messages are sent as UTF-8 text frames and should be JSON objects with
    the following shape:

        {
            "message": "User input text",
            "current_product_id": "optional-catalog-id"
        }

    `message` is required and `current_product_id` lets the agent enrich the
    conversation with product metadata.
    """
    # Validate authentication and parameters before accepting connection
    validate_websocket_token(ws)
    chat_id = _validate_chat_id(ws)

    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            chat_message = ChatMessage.from_raw(raw)

            if not chat_message.message:
                await ws.send_json({"type": "error", "content": "empty message"})
                continue

            # Fetch product metadata if product ID is provided
            current_product = None
            if chat_message.current_product_id:
                try:
                    current_product = await product_catalog.get_product(
                        chat_message.current_product_id
                    )
                except Exception:
                    logger.exception(
                        "Failed to fetch product metadata for id %s",
                        chat_message.current_product_id,
                    )

            # Stream chatbot responses
            async for snapshot in chatbot_service.stream(
                message=chat_message.message,
                current_product=current_product,
                chat_id=chat_id,
            ):
                await ws.send_json(snapshot)

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.exception("WebSocket error")
        try:
            await ws.send_json({"error": str(exc)})
        except Exception:
            pass
