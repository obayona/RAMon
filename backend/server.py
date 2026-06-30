import json
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import (Depends, FastAPI, HTTPException, WebSocket,
                     WebSocketException)
from fastapi.responses import FileResponse
from starlette import status
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from chatbot.config import ChatbotSettings, ConfigError
from chatbot.factory import build_chatbot_components
from chatbot.dependencies import (
    get_chatbot_service,
    get_chatbot_service_ws,
    get_product_catalog,
    get_product_catalog_ws,
)
from chatbot.product_catalog import ProductCatalog
from chatbot.service import ChatNotFoundError, ChatbotService

logger = logging.getLogger("ramon.server")

load_dotenv()
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        settings = ChatbotSettings.from_env()
    except ConfigError as exc:
        logger.critical("Failed to load chatbot configuration: %s", exc)
        raise

    async with AsyncSqliteSaver.from_conn_string(settings.sqlite_path) as checkpointer:
        components = build_chatbot_components(settings, checkpointer)

        app.state.chatbot_service = components.service
        app.state.product_catalog = components.product_catalog

        yield

app = FastAPI(title="RAMon Chatbot", lifespan=lifespan)

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.get("/chat/{chat_id}")
async def get_chat(
    chat_id: str,
    chatbot_service: ChatbotService = Depends(get_chatbot_service),
):
    try:
        return await chatbot_service.get_chat_history(chat_id)
    except ChatNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    chatbot_service: ChatbotService = Depends(get_chatbot_service_ws),
    product_catalog: ProductCatalog = Depends(get_product_catalog_ws),
):
    chat_id = ws.query_params.get("chat_id", "").strip()
    if not chat_id:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="chat_id query parameter is required",
        )

    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"message": raw, "current_product_id": None}

            message = payload.get("message", "").strip()
            current_product_id = (payload.get("current_product_id") or "").strip()
            current_product = None
            if current_product_id:
                try:
                    current_product = await product_catalog.get_product(current_product_id)
                except Exception:
                    logger.exception(
                        "Failed to fetch product metadata for id %s",
                        current_product_id,
                    )

            if not message:
                await ws.send_json({"type": "error", "content": "empty message"})
                continue

            async for snapshot in chatbot_service.stream(
                message=message,
                current_product=current_product,
                chat_id=chat_id,
            ):
                await ws.send_json(snapshot)

    except Exception as exc:
        logger.exception("WebSocket error")
        try:
            await ws.send_json({"error": str(exc)})
        except Exception:
            pass
