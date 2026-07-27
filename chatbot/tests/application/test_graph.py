"""Unit tests for pure functions in chatbot.application.graph."""

from langchain_core.messages import AIMessage

from chatbot.application.graph import (
    SYSTEM_PROMPT,
    _build_system_message,
    _route_after_tools,
    _should_continue,
)


# ---------------------------------------------------------------------------
# _build_system_message
# ---------------------------------------------------------------------------


class TestBuildSystemMessage:
    def test_no_product(self) -> None:
        result = _build_system_message(product=None)
        assert result == SYSTEM_PROMPT

    def test_with_product(self) -> None:
        product = {
            "name": "RTX 4090",
            "description": "High-end GPU",
            "price": 1599.99,
        }
        result = _build_system_message(product=product)
        assert "RTX 4090" in result
        assert "High-end GPU" in result
        assert "$1599.99" in result
        assert SYSTEM_PROMPT in result

    def test_with_empty_product_does_not_add_context(self) -> None:
        product = {}
        result = _build_system_message(product=product)
        assert result == SYSTEM_PROMPT

    def test_with_partial_product(self) -> None:
        product = {"name": "Keyboard"}
        result = _build_system_message(product=product)
        assert "Keyboard" in result
        assert "N/A" in result  # description and price missing


# ---------------------------------------------------------------------------
# _should_continue
# ---------------------------------------------------------------------------


class TestShouldContinue:
    def test_message_with_tool_calls(self) -> None:
        msg = AIMessage(
            content="",
            tool_calls=[{"name": "recommend_products", "args": {"query": "laptop"}, "id": "1"}],
        )
        state = {"messages": [msg]}
        assert _should_continue(state) == "tools"

    def test_message_without_tool_calls(self) -> None:
        msg = AIMessage(content="Here is a laptop")
        state = {"messages": [msg]}
        assert _should_continue(state) == "__end__"

    def test_empty_tool_calls_list(self) -> None:
        msg = AIMessage(content="Hello", tool_calls=[])
        state = {"messages": [msg]}
        assert _should_continue(state) == "__end__"

    def test_multiple_messages_uses_last(self) -> None:
        msg1 = AIMessage(content="", tool_calls=[{"name": "tool", "args": {}, "id": "1"}])
        msg2 = AIMessage(content="Done")
        state = {"messages": [msg1, msg2]}
        assert _should_continue(state) == "__end__"


# ---------------------------------------------------------------------------
# _route_after_tools
# ---------------------------------------------------------------------------


class TestRouteAfterTools:
    def test_routes_to_recommendations_when_query_present(self) -> None:
        state = {"product_query": "laptop gaming"}
        assert _route_after_tools(state) == "process_recommendations"

    def test_routes_to_chatbot_when_no_query(self) -> None:
        state = {}
        assert _route_after_tools(state) == "chatbot"

    def test_routes_to_chatbot_when_query_empty(self) -> None:
        state = {"product_query": ""}
        assert _route_after_tools(state) == "chatbot"

    def test_routes_to_chatbot_when_query_none(self) -> None:
        state = {"product_query": None}
        assert _route_after_tools(state) == "chatbot"
