import json
from typing import Any, Dict, List, Literal

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from chatbot.state import AgentState, Product

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
    "3. When you have finished processing tool results and are ready to present product "
    "recommendations, write ONLY a short conversational sentence (e.g. \"Here are some "
    "laptops that match your needs.\") without listing product names, prices, or "
    "descriptions. The product data is delivered separately through a structured channel "
    "so the frontend can render it as a nice list — you must not duplicate it in your text.\n"
    "4. If the question is general or you already have enough facts, answer directly without "
    "calling tools.\n"
    "5. If you need more details from the user, ask clarifying questions before invoking tools.\n"
    "Be concise, technical, and helpful."
)


def _build_system_message(product: Product | None = None) -> str:
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

def _process_tool_results(state: AgentState) -> Dict[str, Any]:
    """
    Extracts the tool output, updates the structured recommendations state,
    and appends a hidden system message so the LLM remembers what was recommended.
    """
    for msg in reversed(state["messages"]):
        if isinstance(msg, ToolMessage) and msg.name == "recommend_products":
            try:
                parsed = json.loads(msg.content)
                if isinstance(parsed, list) and len(parsed) > 0:
                    
                    # Create a compact string version for the LLM's memory bank
                    # We map only essential fields to keep the context window clean
                    compact_products = [
                        {
                            "id": p.get("id"), 
                            "name": p.get("name"), 
                            "price": p.get("price")
                        } 
                        for p in parsed
                    ]
                    
                    # Construct the hidden system instruction
                    memory_message = SystemMessage(
                        content=(
                            f"[SYSTEM MEMORY: You just recommended the following products to the user: "
                            f"{json.dumps(compact_products)}. Use this context if the user asks follow-up questions "
                            f"comparing them or referencing them.]"
                        )
                    )

                    return {
                        "recommendations": parsed,
                        "messages": [memory_message]
                    }
                    
            except (json.JSONDecodeError, TypeError):
                pass
            break
            
    return {}

def _should_continue(state: AgentState) -> Literal["tools", END]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def _make_chatbot_node(bound_model: ChatOpenAI):
    def chatbot(state: AgentState) -> Dict[str, Any]:
        prompt = _build_system_message(state.get("current_product"))
        messages = [SystemMessage(content=prompt)] + state["messages"]
        response = bound_model.invoke(messages)
        return {"messages": [response]}

    return chatbot


def build_graph(model: ChatOpenAI, tools: List[BaseTool]) -> StateGraph:
    bound_model = model.bind_tools(tools)
    graph = StateGraph(AgentState)

    graph.add_node("chatbot", _make_chatbot_node(bound_model))
    graph.add_node("tools", ToolNode(tools))
    graph.add_node("process_tool_results", _process_tool_results)

    graph.add_edge(START, "chatbot")
    graph.add_conditional_edges("chatbot", _should_continue, {END: END, "tools": "tools"})
    graph.add_edge("tools", "process_tool_results")
    graph.add_edge("process_tool_results", "chatbot")

    return graph
