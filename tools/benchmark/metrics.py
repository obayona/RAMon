"""Statistical aggregation for benchmark results."""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field


@dataclass
class RequestResult:
    """Result of a single benchmark request."""

    latency_ms: float
    ttft_ms: float | None
    success: bool
    error: str | None = None
    cpu_at_finish: float = 0.0
    ram_at_finish: float = 0.0


@dataclass
class BenchmarkStats:
    """Aggregated benchmark statistics."""

    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    ttfts_ms: list[float] = field(default_factory=list)
    durations_s: list[float] = field(default_factory=list)
    cpu_samples: list[float] = field(default_factory=list)
    ram_samples: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failed / self.total_requests * 100

    @property
    def throughput(self) -> float:
        """Completed conversation turns per second."""
        total = sum(self.durations_s)
        if total == 0:
            return 0.0
        return self.successful / total

    def _percentile(self, data: list[float], p: float) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        idx = int(len(sorted_data) * p / 100)
        idx = min(idx, len(sorted_data) - 1)
        return sorted_data[idx]

    def latency_p50(self) -> float:
        return self._percentile(self.latencies_ms, 50)

    def latency_p95(self) -> float:
        return self._percentile(self.latencies_ms, 95)

    def latency_p99(self) -> float:
        return self._percentile(self.latencies_ms, 99)

    def ttft_p50(self) -> float:
        return self._percentile(self.ttfts_ms, 50)

    def ttft_p95(self) -> float:
        return self._percentile(self.ttfts_ms, 95)

    def ttft_p99(self) -> float:
        return self._percentile(self.ttfts_ms, 99)

    def latency_mean(self) -> float:
        return statistics.mean(self.latencies_ms) if self.latencies_ms else 0.0

    def ttft_mean(self) -> float:
        return statistics.mean(self.ttfts_ms) if self.ttfts_ms else 0.0

    def peak_cpu(self) -> float:
        return max(self.cpu_samples) if self.cpu_samples else 0.0

    def peak_ram_gb(self) -> float:
        return max(self.ram_samples) if self.ram_samples else 0.0

    def total_duration(self) -> float:
        return sum(self.durations_s)
