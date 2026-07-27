"""Async WebSocket client for benchmarking."""
from __future__ import annotations

import asyncio
import json
import time
import uuid

import psutil
import websockets

from tools.benchmark.metrics import RequestResult

TEST_MESSAGES = [
    "¿Qué laptops gaming tienes?",
    "Necesito una tarjeta gráfica compatible con mi motherboard ASUS PRIME B550M",
    "¿Cuál es la diferencia entre el ASUS ROG Strix y el MSI Raider?",
    "Recommiedame un monitor 4K para diseño",
    "¿Este procesador es compatible con mi DDR5 RAM?",
]

_SILENCE_TIMEOUT_S: float = 2.0
_MAX_RETRIES: int = 3
_BASE_BACKOFF_S: float = 1.0


async def _recv_all_frames(
    ws, timeout: float, start_time: float
) -> tuple[list[dict], str | None, float | None]:
    """Receive all response frames until silence or error.

    Args:
        ws: Open WebSocket connection.
        timeout: Per-recv timeout (silence detection).
        start_time: perf_counter() when the request was sent.

    Returns:
        Tuple of (frames list, error string or None, ttft_ms or None).
    """
    frames: list[dict] = []
    ttft_ms: float | None = None

    while True:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        except TimeoutError:
            if frames:
                return frames, None, ttft_ms
            return frames, "no response within timeout", None

        # Record time-to-first-frame on first successful recv
        if ttft_ms is None:
            ttft_ms = (time.perf_counter() - start_time) * 1000

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        frames.append(data)

        if data.get("type") == "error" or data.get("error"):
            err = data.get("content") or data.get("error", "unknown error")
            return frames, err, ttft_ms

    return frames, None, ttft_ms


async def _send_and_receive(
    ws,
    msg_text: str,
    timeout: float,
) -> tuple[float, float | None, str | None]:
    """Send one message and collect metrics.

    Returns:
        Tuple of (latency_ms, ttft_ms or None, error or None).
    """
    payload = json.dumps({"message": msg_text})
    start = time.perf_counter()

    await ws.send(payload)
    frames, error, ttft = await _recv_all_frames(ws, timeout, start)
    elapsed = (time.perf_counter() - start) * 1000

    return elapsed, ttft, error


async def run_client(
    url: str,
    token: str,
    messages_per_client: int,
    interval: float,
    timeout: float,
    client_id: int,
) -> list[RequestResult]:
    """Run a single benchmark client with automatic reconnection.

    Args:
        url: WebSocket endpoint URL.
        token: JWT token for authentication.
        messages_per_client: Number of messages to send.
        interval: Seconds between sends.
        timeout: Per-message timeout in seconds.
        client_id: Unique client identifier.

    Returns:
        List of RequestResult for each message sent.
    """
    results: list[RequestResult] = []
    chat_id = f"bench-{client_id}-{uuid.uuid4().hex[:8]}"
    full_url = f"{url}?chat_id={chat_id}&token={token}"

    for i in range(messages_per_client):
        msg_text = TEST_MESSAGES[i % len(TEST_MESSAGES)]
        success = False
        error: str | None = None
        latency_ms = 0.0
        ttft_ms: float | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                async with websockets.connect(
                    full_url,
                    open_timeout=timeout,
                    close_timeout=5,
                ) as ws:
                    latency_ms, ttft_ms, error = await _send_and_receive(
                        ws, msg_text, timeout
                    )
                    if error is None:
                        success = True
                        break
                    # Server returned an error frame — don't retry
                    break

            except websockets.ConnectionClosed as exc:
                error = f"connection closed: {exc}"
            except (TimeoutError, OSError) as exc:
                error = f"connection error: {exc}"
            except Exception as exc:
                error = str(exc)

            # Backoff before retry
            if attempt < _MAX_RETRIES - 1:
                backoff = _BASE_BACKOFF_S * (2**attempt)
                await asyncio.sleep(backoff)

        results.append(
            RequestResult(
                latency_ms=latency_ms,
                ttft_ms=ttft_ms if success else None,
                success=success,
                error=error,
                cpu_at_finish=psutil.cpu_percent(),
                ram_at_finish=psutil.virtual_memory().used / (1024**3),
            )
        )

        if i < messages_per_client - 1:
            await asyncio.sleep(interval)

    return results
