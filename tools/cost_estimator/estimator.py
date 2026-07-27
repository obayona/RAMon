"""Monthly cost estimator — projects API spend from conversation profiles."""
from __future__ import annotations

from dataclasses import dataclass, field

from tools.cost_estimator.pricing import (
    OPENAI_PRICING,
    TAVILY_CREDITS_PER_BASIC_SEARCH,
    TAVILY_PRICE_PER_CREDIT,
    ModelPricing,
)
from tools.cost_estimator.profiles import ConversationProfile, build_profiles


# ── Default traffic mix ───────────────────────────────────────────────────

DEFAULT_PROFILE_MIX: dict[str, float] = {
    "simple_answer": 0.30,
    "product_recommendation": 0.50,
    "compatibility_question": 0.10,
    "full_flow": 0.10,
}


# ── Result dataclasses ────────────────────────────────────────────────────


@dataclass(slots=True)
class ProfileBreakdown:
    """Cost detail for a single conversation profile."""

    name: str
    sessions: int
    llm_calls: int
    llm_input_tokens: int
    llm_output_tokens: int
    embedding_calls: int
    embedding_tokens: int
    tavily_searches: int
    llm_cost: float
    embedding_cost: float
    tavily_cost: float

    @property
    def total_cost(self) -> float:
        return self.llm_cost + self.embedding_cost + self.tavily_cost


@dataclass(slots=True)
class MonthlyEstimate:
    """Complete monthly cost projection."""

    daily_users: int
    messages_per_user: int
    days_per_month: int
    total_sessions: int
    profile_mix: dict[str, float]

    openai_llm_cost: float
    openai_embedding_cost: float
    tavily_cost: float

    total_llm_input_tokens: int
    total_llm_output_tokens: int
    total_embedding_tokens: int

    total_llm_calls: int
    total_embedding_calls: int
    total_tavily_searches: int

    breakdowns: list[ProfileBreakdown] = field(default_factory=list)

    @property
    def total_cost(self) -> float:
        return self.openai_llm_cost + self.openai_embedding_cost + self.tavily_cost

    @property
    def daily_cost(self) -> float:
        return self.total_cost / self.days_per_month if self.days_per_month else 0.0

    @property
    def cost_per_session(self) -> float:
        return self.total_cost / self.total_sessions if self.total_sessions else 0.0


# ── Calculator ────────────────────────────────────────────────────────────


def _cost_for_tokens(
    input_tokens: int,
    output_tokens: int,
    pricing: ModelPricing,
) -> float:
    """Calculate cost from token counts using per-1M pricing."""
    input_cost = input_tokens / 1_000_000 * pricing.input_per_m
    output_cost = output_tokens / 1_000_000 * pricing.output_per_m
    return input_cost + output_cost


def estimate_monthly_cost(
    daily_users: int = 100,
    messages_per_user: int = 5,
    profile_mix: dict[str, float] | None = None,
    chat_model: str = "gpt-4o-mini",
    embedding_model: str = "text-embedding-3-small",
    tavily_price_per_credit: float = TAVILY_PRICE_PER_CREDIT,
    days_per_month: int = 30,
    user_msg_tokens: int = 30,
    ai_response_tokens: int = 150,
) -> MonthlyEstimate:
    """Estimate monthly API costs from traffic parameters.

    Args:
        daily_users: Average daily active users.
        messages_per_user: Average messages per user per day.
        profile_mix: Traffic distribution across conversation profiles.
            Keys are profile names, values are fractions summing to 1.0.
            Uses DEFAULT_PROFILE_MIX if None.
        chat_model: OpenAI chat model name (for pricing lookup).
        embedding_model: OpenAI embedding model name (for pricing lookup).
        tavily_price_per_credit: Tavily cost per credit.
        days_per_month: Days in the billing period.
        user_msg_tokens: Estimated tokens per user message.
        ai_response_tokens: Estimated tokens per AI response.

    Returns:
        MonthlyEstimate with full cost breakdown.
    """
    if profile_mix is None:
        profile_mix = DEFAULT_PROFILE_MIX

    # Normalize mix to sum to 1.0
    mix_total = sum(profile_mix.values())
    if mix_total > 0:
        profile_mix = {k: v / mix_total for k, v in profile_mix.items()}

    total_sessions = daily_users * messages_per_user * days_per_month
    profiles = build_profiles(
        user_msg_tokens=user_msg_tokens,
        ai_response_tokens=ai_response_tokens,
    )

    chat_pricing = OPENAI_PRICING.get(chat_model)
    if chat_pricing is None:
        raise ValueError(
            f"Unknown chat model '{chat_model}'. "
            f"Available: {', '.join(sorted(OPENAI_PRICING))}"
        )

    embed_pricing = OPENAI_PRICING.get(embedding_model)
    if embed_pricing is None:
        raise ValueError(
            f"Unknown embedding model '{embedding_model}'. "
            f"Available: {', '.join(sorted(OPENAI_PRICING))}"
        )

    total_llm_cost = 0.0
    total_embed_cost = 0.0
    total_tavily_cost = 0.0
    total_llm_input = 0
    total_llm_output = 0
    total_embed_tokens = 0
    total_llm_calls = 0
    total_embed_calls = 0
    total_tavily = 0
    breakdowns: list[ProfileBreakdown] = []

    for profile_name, fraction in profile_mix.items():
        if fraction <= 0:
            continue

        profile = profiles.get(profile_name)
        if profile is None:
            raise ValueError(f"Unknown profile '{profile_name}'")

        sessions = int(total_sessions * fraction)

        # LLM costs
        llm_input = sessions * profile.total_llm_input_tokens
        llm_output = sessions * profile.total_llm_output_tokens
        llm_calls = sessions * profile.total_llm_calls
        llm_cost = _cost_for_tokens(llm_input, llm_output, chat_pricing)

        # Embedding costs
        embed_tokens = sessions * profile.embedding_calls * profile.embedding_input_tokens
        embed_calls = sessions * profile.embedding_calls
        embed_cost = _cost_for_tokens(embed_tokens, 0, embed_pricing)

        # Tavily costs
        tavily = sessions * profile.tavily_searches
        tavily_cost = tavily * TAVILY_CREDITS_PER_BASIC_SEARCH * tavily_price_per_credit

        total_llm_cost += llm_cost
        total_embed_cost += embed_cost
        total_tavily_cost += tavily_cost
        total_llm_input += llm_input
        total_llm_output += llm_output
        total_embed_tokens += embed_tokens
        total_llm_calls += llm_calls
        total_embed_calls += embed_calls
        total_tavily += tavily

        breakdowns.append(
            ProfileBreakdown(
                name=profile_name,
                sessions=sessions,
                llm_calls=llm_calls,
                llm_input_tokens=llm_input,
                llm_output_tokens=llm_output,
                embedding_calls=embed_calls,
                embedding_tokens=embed_tokens,
                tavily_searches=tavily,
                llm_cost=llm_cost,
                embedding_cost=embed_cost,
                tavily_cost=tavily_cost,
            )
        )

    return MonthlyEstimate(
        daily_users=daily_users,
        messages_per_user=messages_per_user,
        days_per_month=days_per_month,
        total_sessions=total_sessions,
        profile_mix=profile_mix,
        openai_llm_cost=total_llm_cost,
        openai_embedding_cost=total_embed_cost,
        tavily_cost=total_tavily_cost,
        total_llm_input_tokens=total_llm_input,
        total_llm_output_tokens=total_llm_output,
        total_embedding_tokens=total_embed_tokens,
        total_llm_calls=total_llm_calls,
        total_embedding_calls=total_embed_calls,
        total_tavily_searches=total_tavily,
        breakdowns=breakdowns,
    )
