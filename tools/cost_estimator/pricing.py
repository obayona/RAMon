"""API pricing constants for cost estimation.

Prices are per 1M tokens (or per call for Tavily). Update these when
providers change pricing. Sources checked July 2026.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelPricing:
    """Pricing for a single model, per 1M tokens."""

    input_per_m: float
    output_per_m: float = 0.0


# ── OpenAI ────────────────────────────────────────────────────────────────

OPENAI_PRICING: dict[str, ModelPricing] = {
    "gpt-4o-mini": ModelPricing(input_per_m=0.15, output_per_m=0.60),
    "gpt-4o": ModelPricing(input_per_m=2.50, output_per_m=10.00),
    "gpt-4.1-mini": ModelPricing(input_per_m=0.40, output_per_m=1.60),
    "text-embedding-3-small": ModelPricing(input_per_m=0.02),
    "text-embedding-3-large": ModelPricing(input_per_m=0.13),
}

# ── Tavily ────────────────────────────────────────────────────────────────

TAVILY_PRICE_PER_CREDIT: float = 0.008  # pay-as-you-go
TAVILY_CREDITS_PER_BASIC_SEARCH: int = 1
