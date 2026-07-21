"""LangGraph workflow for the RAMon chatbot."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Literal

import structlog
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from chatbot.domain import ChatbotState, Product

logger = structlog.get_logger("ramon.chatbot.graph")

SYSTEM_PROMPT = (
    "You are a technical assistant for RAMon, an online hardware store. "
    "You help customers find products and answer hardware compatibility questions.\n\n"
    "Rules:\n"
    "1. If the user asks about compatibility with their own hardware (e.g. \"will this work "
    "with my motherboard X\"), look at the current_product context if available and use "
    "search_component_spec to fetch specs for the user's external component.\n"
    "2. If the user wants product recommendations, translate vague requirements (\"watching "
    "YouTube\", \"gaming\") into precise technical search terms and call recommend_products. "
    "Extract budget constraints from the query and pass them as min_price / max_price.\n"
    "3. If the question is general or you already have enough facts, answer directly without "
    "calling tools.\n"
    "4. If you need more details from the user, ask clarifying questions before invoking tools.\n"
    "Be concise, technical, and helpful."
)

RECOMMENDATIONS_PROMPT = """You are evaluating product recommendations for relevance.

Given the user's search query and the products retrieved from the database, decide:
1. If products are RELEVANT to the query: Write a short intro and include products using <products>[JSON]</products>
2. If products are NOT RELEVANT or the list is empty: Do NOT include the <products> marker, explain what you don't have

IMPORTANT: Only include products that actually match what the user asked for. If the retrieved products
are tangentially related but not what the user wants, do not include them.
Respond in the same language the user used in their query.

Examples:

Query: "gaming laptop"
Products: [{{"name": "ASUS ROG Gaming Laptop", "price": 1299.99}}, {{"name": "MSI Gaming Laptop", "price": 1199.99}}]
Response: Here are some gaming laptops that match your needs:
<products>[{{"name": "ASUS ROG Gaming Laptop", "price": 1299.99}}, {{"name": "MSI Gaming Laptop", "price": 1199.99}}]</products>

Query: "bikes"
Products: [{{"name": "Garmin Smartwatch for Cycling", "price": 299.99}}]
Response: I don't have bikes in our inventory. We're a computer hardware store, so we specialize in electronics like computers, monitors, and accessories. Is there anything else I can help you with?

Query: "monitor under $300"
Products: [{{"name": "Dell 27 Monitor", "price": 279.99}}, {{"name": "LG 24 Monitor", "price": 199.99}}]
Response: I found some monitors within your budget:
<products>[{{"name": "Dell 27 Monitor", "price": 279.99}}, {{"name": "LG 24 Monitor", "price": 199.99}}]</products>

Query: "mechanical keyboard"
Products: [{{"name": "Gaming Mouse", "price": 49.99}}, {{"name": "USB Hub", "price": 29.99}}]
Response: I couldn't find any mechanical keyboards in our current inventory. Would you like me to help you find other peripherals or accessories instead?

Query: "ultrawide monitor"
Products: []
Response: I couldn't find any ultrawide monitors in our current inventory. Would you like me to search for standard monitors or other display options?

Now evaluate:
Query: {query}
Products: {products}
Response:"""


def _build_system_message(product: Product | None = None) -> str:
    """Build the system prompt, optionally including current product context."""
    prompt = SYSTEM_PROMPT
    if product:
        prompt += (
            f"\n\nThe user is currently viewing this product:\n"
            f"Name: {product.get('name', 'N/A')}\n"
            f"Description: {product.get('description', 'N/A')}\n"
            f"Price: ${product.get('price', 'N/A')}\n"
            f"If the user asks about compatibility, use search_component_spec "
            f"to look up their hardware."
        )
    return prompt


def _should_continue(state: ChatbotState) -> Literal["tools", END]:
    """Determine if the chatbot should call tools or end."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        tool_names = [tc["name"] for tc in last.tool_calls]
        logger.debug("graph.tool_calls", tools=tool_names)
        return "tools"
    return END


def _make_chatbot_node(bound_model: ChatOpenAI):
    """Create the main chatbot node that handles conversation."""

    def chatbot(state: ChatbotState) -> Dict[str, Any]:
        prompt = _build_system_message(state.get("current_product"))
        messages = [SystemMessage(content=prompt)] + state["messages"]
        response = bound_model.invoke(messages)
        return {"messages": [response]}

    return chatbot


def _make_process_recommendations_node(model: ChatOpenAI):
    """Create the process_recommendations node that evaluates relevance.

    This node uses a few-shot prompt to determine if retrieved products
    match the user's query. If relevant, it includes them in the response
    wrapped in <products>...</products> markers. If not, it explains what's
    missing without including the products.

    The product_query and recommendations are already in state, populated
    by the recommend_products tool via Command.
    """

    def process_recommendations(state: ChatbotState) -> Dict[str, Any]:
        query = state.get("product_query", "")
        recommendations = state.get("recommendations", [])

        # Prepare products JSON for the prompt
        # Empty list is valid - LLM will explain no products were found
        products_for_prompt = json.dumps(recommendations, indent=2)

        # Build the evaluation prompt
        prompt = RECOMMENDATIONS_PROMPT.format(
            query=query or "unknown",
            products=products_for_prompt,
        )

        response = model.invoke([SystemMessage(content=prompt)])
        return {"messages": [response]}

    return process_recommendations


def _route_after_tools(state: ChatbotState) -> Literal["process_recommendations", "chatbot"]:
    """Route after tools based on whether recommend_products was called.

    recommend_products sets product_query in state, so we use that to detect
    if we should go to process_recommendations or back to chatbot.
    """
    if state.get("product_query"):
        return "process_recommendations"
    return "chatbot"


def build_graph(model: ChatOpenAI, tools: List[BaseTool]) -> StateGraph:
    """Build the LangGraph workflow for the chatbot.

    Flow:
        START → chatbot → [tool_calls?]
            → YES: tools → [product_query in state?]
                → YES: process_recommendations → END
                → NO:  chatbot (loop for search_component_spec)
            → NO: END

    The recommend_products tool updates state with product_query and
    recommendations, which triggers routing to process_recommendations.

    Args:
        model: ChatOpenAI model for conversation.
        tools: List of tools available to the chatbot.

    Returns:
        Configured StateGraph (not yet compiled).
    """
    bound_model = model.bind_tools(tools)
    graph = StateGraph(ChatbotState)

    # Nodes
    graph.add_node("chatbot", _make_chatbot_node(bound_model))
    graph.add_node("tools", ToolNode(tools))
    graph.add_node("process_recommendations", _make_process_recommendations_node(model))

    # Edges
    graph.add_edge(START, "chatbot")
    graph.add_conditional_edges(
        "chatbot", _should_continue, {END: END, "tools": "tools"}
    )
    # Route based on whether recommend_products was called (sets product_query)
    graph.add_conditional_edges(
        "tools",
        _route_after_tools,
        {"process_recommendations": "process_recommendations", "chatbot": "chatbot"},
    )
    graph.add_edge("process_recommendations", END)

    return graph
