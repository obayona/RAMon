"""Conversation profiles — token estimates for each chatbot flow pattern.

Each profile describes a typical user interaction pattern and the API calls
it triggers.  Token counts come from running tiktoken on the actual prompt
templates in ``chatbot/application/graph.py``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from tools.cost_estimator.tokenizer import count_tokens


# ── Measured from actual prompt templates (gpt-4o-mini tokenizer) ─────────

_SYSTEM_PROMPT_TOKENS: int = count_tokens(
    "You are a technical assistant for RAMon, an online hardware store. "
    "You help customers find products and answer hardware compatibility questions.\n\n"
    "Rules:\n"
    "1. Always respond in the same language the user writes in.\n"
    "2. If the user asks about compatibility with their own hardware "
    "(e.g. \"will this work with my motherboard X\"), look at the "
    "current_product context if available and use search_component_spec "
    "to fetch specs for the user's external component.\n"
    "3. If the user wants product recommendations, refine the query into "
    "precise technical terms in the same language. For example, "
    "\"celulares baratos\" becomes \"telefono movil gama baja\", NOT "
    "\"smartphone\". Do NOT translate to another language. Extract budget "
    "constraints from the query and pass them as min_price / max_price.\n"
    "4. If the question is general or you already have enough facts, answer "
    "directly without calling tools.\n"
    "5. If you need more details from the user, ask clarifying questions "
    "before invoking tools.\n"
    "Be concise, technical, and helpful.",
    "gpt-4o-mini",
)

_RECOMMENDATIONS_PROMPT_BASE_TOKENS: int = count_tokens(
    "You are evaluating product recommendations for relevance.\n\n"
    "Given the user's original query, the refined search query used, and "
    "the products retrieved from the database, decide:\n"
    "1. If some products are RELEVANT: Write a short intro, then output "
    "the marker <products ids=\"1,2,3\"/> listing ONLY the IDs of the "
    "relevant products (comma-separated). Do NOT include irrelevant products.\n"
    "2. If products are NOT RELEVANT or empty: Do NOT include the marker, "
    "explain what you don't have\n\n"
    "The products JSON includes an \"id\" field for each product. Use those "
    "IDs in the marker.\n\n"
    "The \"User query\" is the original message from the user. ALWAYS "
    "respond in the same language as the user query.\n\n"
    "Now evaluate:\n"
    "User query: \n"
    "Refined query: \n"
    "Products: \n"
    "Response:",
    "gpt-4o-mini",
)

_SAMPLE_PRODUCTS_JSON_TOKENS: int = count_tokens(
    '[{"id": 1, "name": "ASUS ROG Strix G16", "price": 1299.99, '
    '"description": "Gaming laptop"}, {"id": 2, "name": "MSI Raider GE78", '
    '"price": 1899.99, "description": "High-end gaming"}, {"id": 3, '
    '"name": "Lenovo Legion Pro 5", "price": 1099.99, '
    '"description": "Mid-range gaming"}]',
    "gpt-4o-mini",
)

# Per-message framing overhead in Chat Completions API
_MESSAGE_FRAMING_TOKENS: int = 4


# ── Profile dataclass ─────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class LLMCall:
    """One LLM invocation within a profile."""

    label: str
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True, slots=True)
class ConversationProfile:
    """Describes a typical user interaction and its API footprint."""

    name: str
    description: str
    llm_calls: list[LLMCall] = field(default_factory=list)
    embedding_calls: int = 0
    embedding_input_tokens: int = 0
    tavily_searches: int = 0

    @property
    def total_llm_input_tokens(self) -> int:
        return sum(c.input_tokens for c in self.llm_calls)

    @property
    def total_llm_output_tokens(self) -> int:
        return sum(c.output_tokens for c in self.llm_calls)

    @property
    def total_llm_calls(self) -> int:
        return len(self.llm_calls)


# ── Default profiles ──────────────────────────────────────────────────────
# Token counts use measured prompt template sizes + configurable estimates
# for variable content (user messages, AI responses).


def _estimate_user_tokens(text: str = "") -> int:
    """Estimate tokens for a user message. Uses actual count or default."""
    if text:
        return count_tokens(text, "gpt-4o-mini")
    return 30  # typical short user message


_DEFAULT_AI_RESPONSE_TOKENS: int = 150
_DEFAULT_SEARCH_RESULT_TOKENS: int = 500  # Tavily returns a lot of text
_DEFAULT_TOOL_CALL_ARGS_TOKENS: int = 20
_DEFAULT_TOOL_RESULT_TOKENS: int = 60


def build_profiles(
    user_msg_tokens: int = 30,
    ai_response_tokens: int = 150,
    product_json_tokens: int | None = None,
) -> dict[str, ConversationProfile]:
    """Build conversation profiles with the given token estimates.

    Args:
        user_msg_tokens: Estimated tokens for a typical user message.
        ai_response_tokens: Estimated tokens for a typical AI response.
        product_json_tokens: Estimated tokens for product JSON in the
            recommendations prompt.  Defaults to measured sample size.

    Returns:
        Dict of profile name → ConversationProfile.
    """
    if product_json_tokens is None:
        product_json_tokens = _SAMPLE_PRODUCTS_JSON_TOKENS

    # Tokens for the recommendations prompt with product data filled in
    rec_prompt_total = (
        _RECOMMENDATIONS_PROMPT_BASE_TOKENS
        + product_json_tokens
        + user_msg_tokens  # original_query placeholder
        + user_msg_tokens  # refined query placeholder
    )

    profiles = {
        # ── Profile 1: Direct answer, no tools ─────────────────────────
        "simple_answer": ConversationProfile(
            name="simple_answer",
            description="Direct answer without calling any tools",
            llm_calls=[
                LLMCall(
                    label="chatbot",
                    input_tokens=(
                        _SYSTEM_PROMPT_TOKENS
                        + _MESSAGE_FRAMING_TOKENS
                        + user_msg_tokens
                    ),
                    output_tokens=ai_response_tokens,
                ),
            ],
        ),
        # ── Profile 2: Product recommendation (most common) ────────────
        "product_recommendation": ConversationProfile(
            name="product_recommendation",
            description="User asks for product recommendations",
            llm_calls=[
                LLMCall(
                    label="chatbot → recommend_products",
                    input_tokens=(
                        _SYSTEM_PROMPT_TOKENS
                        + _MESSAGE_FRAMING_TOKENS
                        + user_msg_tokens
                    ),
                    output_tokens=_DEFAULT_TOOL_CALL_ARGS_TOKENS,
                ),
                LLMCall(
                    label="process_recommendations",
                    input_tokens=rec_prompt_total,
                    output_tokens=ai_response_tokens,
                ),
            ],
            embedding_calls=1,
            embedding_input_tokens=user_msg_tokens,
        ),
        # ── Profile 3: Compatibility question (Tavily only) ────────────
        "compatibility_question": ConversationProfile(
            name="compatibility_question",
            description="User asks about hardware compatibility",
            llm_calls=[
                LLMCall(
                    label="chatbot → search_component_spec",
                    input_tokens=(
                        _SYSTEM_PROMPT_TOKENS
                        + _MESSAGE_FRAMING_TOKENS
                        + user_msg_tokens
                    ),
                    output_tokens=_DEFAULT_TOOL_CALL_ARGS_TOKENS,
                ),
                LLMCall(
                    label="chatbot (answer with specs)",
                    input_tokens=(
                        _SYSTEM_PROMPT_TOKENS
                        + _MESSAGE_FRAMING_TOKENS
                        + user_msg_tokens
                        + _DEFAULT_TOOL_RESULT_TOKENS
                    ),
                    output_tokens=ai_response_tokens,
                ),
            ],
            tavily_searches=1,
        ),
        # ── Profile 4: Full flow (compatibility + products) ────────────
        "full_flow": ConversationProfile(
            name="full_flow",
            description="Compatibility question followed by product recommendations",
            llm_calls=[
                LLMCall(
                    label="chatbot → search_component_spec",
                    input_tokens=(
                        _SYSTEM_PROMPT_TOKENS
                        + _MESSAGE_FRAMING_TOKENS
                        + user_msg_tokens
                    ),
                    output_tokens=_DEFAULT_TOOL_CALL_ARGS_TOKENS,
                ),
                LLMCall(
                    label="chatbot → recommend_products",
                    input_tokens=(
                        _SYSTEM_PROMPT_TOKENS
                        + _MESSAGE_FRAMING_TOKENS
                        + user_msg_tokens
                        + _DEFAULT_SEARCH_RESULT_TOKENS
                    ),
                    output_tokens=_DEFAULT_TOOL_CALL_ARGS_TOKENS,
                ),
                LLMCall(
                    label="process_recommendations",
                    input_tokens=rec_prompt_total,
                    output_tokens=ai_response_tokens,
                ),
            ],
            embedding_calls=1,
            embedding_input_tokens=user_msg_tokens,
            tavily_searches=1,
        ),
    }

    return profiles
