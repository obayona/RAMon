"""WebSocket handler for the chatbot endpoint.

This module encapsulates the WebSocket message handling logic,
keeping it separate from the main server routing.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket, WebSocketException
from starlette import status
from starlette.websockets import WebSocketDisconnect

from chatbot import ChatbotService, ProductCatalog

logger = logging.getLogger("ramon.websocket")


@dataclass
class ChatMessage:
    """Parsed chat message from WebSocket payload."""
    
    message: str
    current_product_id: str | None
    
    @classmethod
    def from_raw(cls, raw: str) -> "ChatMessage":
        """Parse a raw WebSocket message into a ChatMessage.
        
        Args:
            raw: Raw text received from WebSocket.
            
        Returns:
            Parsed ChatMessage instance.
        """
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"message": raw, "current_product_id": None}
        
        message = payload.get("message", "").strip()
        current_product_id = (payload.get("current_product_id") or "").strip() or None
        
        return cls(message=message, current_product_id=current_product_id)


def validate_chat_id(ws: WebSocket) -> str:
    """Extract and validate chat_id from WebSocket query parameters.
    
    Args:
        ws: The WebSocket connection.
        
    Returns:
        The validated chat_id string.
        
    Raises:
        WebSocketException: If chat_id is missing or empty.
    """
    chat_id = ws.query_params.get("chat_id", "").strip()
    if not chat_id:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="chat_id query parameter is required",
        )
    return chat_id


async def handle_websocket_session(
    ws: WebSocket,
    chat_id: str,
    chatbot_service: ChatbotService,
    product_catalog: ProductCatalog,
) -> None:
    """Handle a WebSocket chat session after connection is accepted.
    
    This function manages the message loop for an authenticated WebSocket
    connection, processing incoming messages and streaming responses.
    
    Args:
        ws: The accepted WebSocket connection.
        chat_id: The chat session identifier.
        chatbot_service: The chatbot service for processing messages.
        product_catalog: The product catalog for fetching product metadata.
    """
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
