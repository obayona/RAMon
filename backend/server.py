import json
import logging

from fastapi.responses import FileResponse
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

logger = logging.getLogger("ramon.server")

from chatbot.service import ChatbotService

svc = ChatbotService()

app = FastAPI(title="RAMon Chatbot")

@app.get("/")
async def root():
    return FileResponse("index.html")

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

            async for snapshot in svc.stream(
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
