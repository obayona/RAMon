"""Auto-detect system hardware capabilities."""
from __future__ import annotations

import os

import psutil


def detect_cores() -> int:
    """Return the number of CPU cores available."""
    return os.cpu_count() or 1


def detect_ram_gb() -> float:
    """Return total system RAM in GB."""
    return psutil.virtual_memory().total / (1024**3)


def detect_system() -> dict[str, float | int]:
    """Return a snapshot of current system resource usage.

    Returns:
        Dict with keys: cpu_percent, ram_used_gb, ram_total_gb, ram_percent.
    """
    ram = psutil.virtual_memory()
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "ram_used_gb": ram.used / (1024**3),
        "ram_total_gb": ram.total / (1024**3),
        "ram_percent": ram.percent,
    }
