"""CLI entry point for the RAMon WebSocket benchmark.

Usage::

    python -m tools.benchmark --app-key h8jC0gsKMUeOC22gNwX18tpwlOX
    python -m tools.benchmark --app-key KEY --concurrent 20 --messages 100
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time

import jwt

from tools.benchmark.metrics import BenchmarkStats
from tools.benchmark.runner import run_benchmark
from tools.benchmark.system import detect_cores, detect_ram_gb, detect_system


def _generate_token(app_key: str) -> str:
    """Generate a JWT token using the app key."""
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    payload = {
        "iat": now,
        "exp": now + timedelta(hours=24),
    }
    return jwt.encode(payload, app_key, algorithm="HS256")


def _print_report(stats: BenchmarkStats, config: dict) -> None:
    """Print a formatted benchmark report."""
    cores = detect_cores()
    ram = detect_ram_gb()

    print()
    print("=" * 56)
    print("  RAMon WebSocket Benchmark Results")
    print("=" * 56)
    print()
    print(f"  System: {cores} cores, {ram:.1f} GB RAM")
    print(
        f"  Config: {config['concurrent']} concurrent, "
        f"{config['messages']} msgs/connection, "
        f"{config['interval']}s interval"
    )
    print()

    # Request summary
    print("  Requests:")
    print(f"    Total:     {stats.total_requests:>8}")
    print(f"    Success:   {stats.successful:>8}")
    print(f"    Failed:    {stats.failed:>8}")
    print(f"    Error rate:{stats.error_rate:>7.1f}%")
    print()

    # Latency
    print("  Latency (ms):")
    print(f"    mean = {stats.latency_mean():>8.0f}")
    print(f"    p50  = {stats.latency_p50():>8.0f}")
    print(f"    p95  = {stats.latency_p95():>8.0f}")
    print(f"    p99  = {stats.latency_p99():>8.0f}")
    if stats.latencies_ms:
        print(
            f"    min  = {min(stats.latencies_ms):>8.0f}   "
            f"max = {max(stats.latencies_ms):>8.0f}"
        )
    print()

    # TTFT
    if stats.ttfts_ms:
        print("  Time to First Token (ms):")
        print(f"    mean = {stats.ttft_mean():>8.0f}")
        print(f"    p50  = {stats.ttft_p50():>8.0f}")
        print(f"    p95  = {stats.ttft_p95():>8.0f}")
        print(f"    p99  = {stats.ttft_p99():>8.0f}")
        print()

    # Throughput
    print(f"  Throughput:    {stats.throughput:>8.2f} turns/s")
    print(f"  Total time:    {stats.total_duration():>8.1f}s")
    print()

    # System resources
    if stats.cpu_samples:
        print("  Peak Resources:")
        print(f"    CPU:  {stats.peak_cpu():>6.1f}%")
        print(f"    RAM:  {stats.peak_ram_gb():>6.1f} GB ({stats.peak_ram_gb() / ram * 100:.1f}%)")
        print()

    # Error details
    if stats.failed > 0:
        print(f"  Errors ({stats.failed} failed):")
        from collections import Counter

        error_counts = Counter(stats.errors)
        for msg, count in error_counts.most_common(5):
            label = msg[:60] + "..." if len(msg) > 60 else msg
            print(f"    {count:>4}x  {label}")
        print()

    print("=" * 56)
    print()


async def _run(args: argparse.Namespace) -> None:
    """Async main entry point."""
    cores = detect_cores()
    ram = detect_ram_gb()

    print()
    print("  RAMon WebSocket Benchmark")
    print(f"  System: {cores} cores, {ram:.1f} GB RAM")
    print(f"  Target: {args.url}")
    print(f"  Config: {args.concurrent} concurrent, {args.messages} msgs, "
          f"{args.interval}s interval")
    print()
    print("  Generating JWT token...")
    token = _generate_token(args.app_key)
    print("  Starting benchmark...")
    print()

    sys.stdout.flush()

    stats = await run_benchmark(
        url=args.url,
        token=token,
        concurrent=args.concurrent,
        messages=args.messages,
        interval=args.interval,
        timeout=args.timeout,
        ramp_up=args.ramp_up,
    )

    config = {
        "concurrent": args.concurrent,
        "messages": args.messages,
        "interval": args.interval,
    }
    _print_report(stats, config)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark RAMon WebSocket chat endpoint.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m tools.benchmark --app-key SECRET\n"
            "  python -m tools.benchmark --app-key SECRET --concurrent 20\n"
            "  python -m tools.benchmark --app-key SECRET -c 50 -m 200 -i 0.2\n"
        ),
    )
    parser.add_argument(
        "--url",
        default="ws://localhost:8000/ws",
        help="WebSocket endpoint URL (default: ws://localhost:8000/ws)",
    )
    parser.add_argument(
        "--app-key",
        required=True,
        help="JWT signing key (APP_KEY from backend .env)",
    )
    parser.add_argument(
        "-c",
        "--concurrent",
        type=int,
        default=10,
        help="Number of simultaneous connections (default: 10)",
    )
    parser.add_argument(
        "-m",
        "--messages",
        type=int,
        default=50,
        help="Messages per connection (default: 50)",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=0.5,
        help="Seconds between sends within a client (default: 0.5)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=30,
        help="Per-message timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--ramp-up",
        type=float,
        default=0.1,
        help="Delay between opening connections in seconds (default: 0.1)",
    )

    args = parser.parse_args(argv)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
