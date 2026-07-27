"""Chat listing API route."""

from fastapi import APIRouter, Depends

from src.adapters.chat_repository import ChatRepository
from src.api.dependencies import get_chat_repository
from src.api.middleware import require_jwt

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("")
async def list_chats(
    chat_repository: ChatRepository = Depends(get_chat_repository),
    _: dict = Depends(require_jwt),
):
    """Return all chats ordered by most recent first."""
    return await chat_repository.list_chats()
