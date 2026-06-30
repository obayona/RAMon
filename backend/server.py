import json
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import (Depends, FastAPI, HTTPException, Request, WebSocket,
                     WebSocketException)
from fastapi.responses import FileResponse
from starlette import status
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from openai import OpenAI
from pinecone import Pinecone

from chatbot.product_catalog import PineconeProductCatalog, ProductCatalog
from chatbot.service import ChatNotFoundError, ChatbotService

logger = logging.getLogger("ramon.server")

load_dotenv()


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Environment variable '{key}' is required")
    return value


def _get_chatbot_service(app: FastAPI) -> ChatbotService:
    chatbot_service: ChatbotService | None = getattr(app.state, "chatbot_service", None)
    if chatbot_service is None:
        raise RuntimeError("ChatbotService has not been initialised")
    return chatbot_service


def get_chatbot_service(request: Request) -> ChatbotService:
    return _get_chatbot_service(request.app)


def _get_product_catalog(app: FastAPI) -> ProductCatalog:
    product_catalog: ProductCatalog | None = getattr(app.state, "product_catalog", None)
    if product_catalog is None:
        raise RuntimeError("ProductCatalog has not been initialised")
    return product_catalog


def get_product_catalog(request: Request) -> ProductCatalog:
    return _get_product_catalog(request.app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    sqlite_path = _require_env("SQLITE_PATH")
    openai_api_key = _require_env("OPENAI_API_KEY")
    pinecone_api_key = _require_env("PINECONE_API_KEY")
    tavily_api_key = _require_env("TAVILY_API_KEY")

    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "ramon-products")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0"))

    async with AsyncSqliteSaver.from_conn_string(sqlite_path) as checkpointer:
        openai_client = OpenAI(api_key=openai_api_key)
        pinecone_client = Pinecone(api_key=pinecone_api_key)
        pinecone_index = pinecone_client.Index(pinecone_index_name)
        tavily_client = TavilySearch(max_results=3, tavily_api_key=tavily_api_key)
        chat_model = ChatOpenAI(
            model=openai_model,
            temperature=openai_temperature,
            api_key=openai_api_key,
        )

        app.state.chatbot_service = ChatbotService(
            openai_client=openai_client,
            pinecone_index=pinecone_index,
            tavily_client=tavily_client,
            chat_model=chat_model,
            checkpointer=checkpointer,
        )
        app.state.product_catalog = PineconeProductCatalog(pinecone_index)

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
async def websocket_endpoint(ws: WebSocket):
    chat_id = ws.query_params.get("chat_id", "").strip()
    if not chat_id:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="chat_id query parameter is required",
        )

    await ws.accept()
    chatbot_service = _get_chatbot_service(ws.app)
    product_catalog = _get_product_catalog(ws.app)
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
