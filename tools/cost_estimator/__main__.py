"""CLI entry point for the RAMon cost estimator.

Usage::

    python -m tools.cost_estimator
    python -m tools.cost_estimator --daily-users 500 --messages 8
    python -m tools.cost_estimator --daily-users 50 --model gpt-4o
"""
from __future__ import annotations

import argparse
import sys

from tools.cost_estimator.estimator import estimate_monthly_cost
from tools.cost_estimator.pricing import OPENAI_PRICING


def _format_tokens(n: int) -> str:
    """Format token count with human-readable suffix."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _print_report(est) -> None:
    """Print a formatted cost estimate report."""
    print()
    print("=" * 56)
    print("  RAMon Monthly API Cost Estimate")
    print("=" * 56)
    print()
    print(
        f"  Traffic: {est.daily_users} users/day "
        f"x {est.messages_per_user} msgs "
        f"x {est.days_per_month} days "
        f"= {est.total_sessions:,} sessions/month"
    )
    print()

    # Profile mix
    print("  Profile Mix:")
    for b in est.breakdowns:
        pct = est.profile_mix[b.name] * 100
        print(f"    {b.name:<30s} {pct:4.0f}%  ({b.sessions:,} sessions)")
    print()

    # API calls
    print("  API Calls (monthly):")
    print(f"    LLM chat completions:   {est.total_llm_calls:>10,} calls")
    print(f"    Embeddings:              {est.total_embedding_calls:>10,} calls")
    print(f"    Tavily searches:         {est.total_tavily_searches:>10,} calls")
    print()

    # Token usage
    print("  Token Usage (estimated):")
    print(f"    LLM input:   {_format_tokens(est.total_llm_input_tokens):>10}")
    print(f"    LLM output:  {_format_tokens(est.total_llm_output_tokens):>10}")
    print(f"    Embeddings:  {_format_tokens(est.total_embedding_tokens):>10}")
    print()

    # Cost breakdown
    print("  Cost Breakdown:")
    print(f"    OpenAI LLM:             ${est.openai_llm_cost:>10.2f}")
    print(f"    OpenAI Embeddings:      ${est.openai_embedding_cost:>10.2f}")
    print(f"    Tavily:                 ${est.tavily_cost:>10.2f}")
    print("    " + "-" * 40)
    print(f"    Total monthly:          ${est.total_cost:>10.2f}")
    print(f"    Daily:                  ${est.daily_cost:>10.2f}")
    print(f"    Per session:            ${est.cost_per_session:>10.6f}")
    print()
    print("=" * 56)
    print()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Estimate monthly RAMon API costs (OpenAI + Tavily).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m tools.cost_estimator\n"
            "  python -m tools.cost_estimator --daily-users 500 --messages 8\n"
            "  python -m tools.cost_estimator --daily-users 50 --model gpt-4o\n"
        ),
    )
    parser.add_argument(
        "--daily-users",
        type=int,
        default=100,
        help="Average daily active users (default: 100)",
    )
    parser.add_argument(
        "--messages",
        type=int,
        default=5,
        help="Average messages per user per day (default: 5)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days in billing period (default: 30)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        choices=sorted(k for k in OPENAI_PRICING if "embed" not in k),
        help="Chat model (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--embedding-model",
        default="text-embedding-3-small",
        choices=sorted(k for k in OPENAI_PRICING if "embed" in k),
        help="Embedding model (default: text-embedding-3-small)",
    )
    parser.add_argument(
        "--user-tokens",
        type=int,
        default=30,
        help="Estimated tokens per user message (default: 30)",
    )
    parser.add_argument(
        "--response-tokens",
        type=int,
        default=150,
        help="Estimated tokens per AI response (default: 150)",
    )

    args = parser.parse_args(argv)

    estimate = estimate_monthly_cost(
        daily_users=args.daily_users,
        messages_per_user=args.messages,
        chat_model=args.model,
        embedding_model=args.embedding_model,
        days_per_month=args.days,
        user_msg_tokens=args.user_tokens,
        ai_response_tokens=args.response_tokens,
    )

    _print_report(estimate)


if __name__ == "__main__":
    main()
