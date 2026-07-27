"""Benchmark runner — orchestrates concurrent WebSocket clients."""
from __future__ import annotations

import asyncio
import sys
import time

from tools.benchmark.client import run_client
from tools.benchmark.metrics import BenchmarkStats


async def _print_progress(
    completed: list[int],
    total: int,
    done_event: asyncio.Event,
    start_time: float,
) -> None:
    """Periodically print progress while benchmark runs."""
    while not done_event.is_set():
        done = completed[0]
        elapsed = time.perf_counter() - start_time
        pct = done / total * 100 if total else 0
        sys.stdout.write(
            f"\r  Progress: {done}/{total} ({pct:.0f}%) "
            f"[{elapsed:.0f}s elapsed]"
        )
        sys.stdout.flush()
        await asyncio.sleep(1.0)
    done = completed[0]
    elapsed = time.perf_counter() - start_time
    pct = done / total * 100 if total else 0
    sys.stdout.write(
        f"\r  Progress: {done}/{total} ({pct:.0f}%) "
        f"[{elapsed:.0f}s elapsed]  \n"
    )
    sys.stdout.flush()


async def run_benchmark(
    url: str,
    token: str,
    concurrent: int,
    messages: int,
    interval: float,
    timeout: float,
    ramp_up: float,
) -> BenchmarkStats:
    """Run the full benchmark with concurrent clients.

    Args:
        url: WebSocket endpoint URL.
        token: JWT token for authentication.
        concurrent: Number of simultaneous connections.
        messages: Messages per client.
        interval: Seconds between sends within a client.
        timeout: Per-message timeout in seconds.
        ramp_up: Delay between opening connections.

    Returns:
        BenchmarkStats with all collected metrics.
    """
    stats = BenchmarkStats()
    all_results: list = []
    total_messages = concurrent * messages
    completed_count = [0]  # mutable counter for closure
    done_event = asyncio.Event()

    async def _run_one(client_id: int) -> None:
        await asyncio.sleep(client_id * ramp_up)
        results = await run_client(
            url=url,
            token=token,
            messages_per_client=messages,
            interval=interval,
            timeout=timeout,
            client_id=client_id,
        )
        all_results.extend(results)
        completed_count[0] += len(results)

    wall_start = time.perf_counter()

    tasks = [asyncio.create_task(_run_one(i)) for i in range(concurrent)]
    progress_task = asyncio.create_task(
        _print_progress(completed_count, total_messages, done_event, wall_start)
    )

    await asyncio.gather(*tasks)

    done_event.set()
    await progress_task

    wall_duration = time.perf_counter() - wall_start

    for r in all_results:
        stats.total_requests += 1
        if r.success:
            stats.successful += 1
            stats.latencies_ms.append(r.latency_ms)
            if r.ttft_ms is not None:
                stats.ttfts_ms.append(r.ttft_ms)
            stats.cpu_samples.append(r.cpu_at_finish)
            stats.ram_samples.append(r.ram_at_finish)
        else:
            stats.failed += 1
            if r.error:
                stats.errors.append(r.error)

    stats.durations_s = [wall_duration]

    return stats
