import json
import logging
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from langchain_core.messages import HumanMessage, AIMessage
from fastapi.responses import FileResponse
from fastapi import FastAPI, WebSocket
from langchain_core.messages import BaseMessage, messages_to_dict
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from chatbot.service import ChatbotService

logger = logging.getLogger("ramon.server")

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSqliteSaver.from_conn_string(os.getenv("SQLITE_PATH")) as checkpointer:
        app.state.checkpointer = checkpointer
        app.state.svc = ChatbotService(
            openai_api_key = os.getenv("OPENAI_API_KEY"),
            pinecone_api_key = os.getenv("PINECONE_API_KEY"),
            tavily_api_key = os.getenv("TAVILY_API_KEY"),
            checkpointer=checkpointer
        )
        
        yield

app = FastAPI(title="RAMon Chatbot", lifespan=lifespan)

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.get("/thread/{thread_id}")
async def get_chat(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    state = await app.state.svc.compiled_graph.aget_state(config)
    print(state)
    if not state:
        raise HTTPException(status_code=404, detail="Chat not found")

    if  "messages" not in state.values:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = []
    for msg in state.values["messages"]:
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            messages.append({
                "id": msg.id,
                "type": "ai",
                "text": msg.content,
                "ui_data": msg.additional_kwargs.get("ui_payload") 
            })
        if isinstance(msg, HumanMessage):
            messages.append({
                "id": msg.id,
                "type": "human",
                "text": msg.content,
            })
        

    return messages

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"message": raw, "chat_id": None}

            message = payload.get("message", "").strip()
            chat_id = payload.get("chat_id") or "default"
            product = payload.get("current_product")

            if not message:
                await ws.send_json({"type": "error", "content": "empty message"})
                continue

            async for snapshot in app.state.svc.stream(
                message=message,
                current_product=product,
                thread_id=chat_id,
            ):
                await ws.send_json(snapshot)

    except Exception as exc:
        logger.exception("WebSocket error")
        try:
            await ws.send_json({"error": str(exc)})
        except Exception:
            pass
