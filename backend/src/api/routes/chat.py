"""Chat history API route."""
from fastapi import APIRouter, Depends, HTTPException

from chatbot import ChatbotService, ChatNotFoundError
from src.api.dependencies import get_chatbot_service
from src.api.middleware import require_jwt

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    chatbot_service: ChatbotService = Depends(get_chatbot_service),
    _: dict = Depends(require_jwt),
):
    """Return the full message history for the provided chat_id.

    Raises HTTPException with a 404 status code if the chat session does
    not exist in the configured checkpoint backend.
    """
    try:
        return await chatbot_service.get_chat_history(chat_id)
    except ChatNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
