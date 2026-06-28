import json
import os
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pinecone import Pinecone
from openai import OpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_product: Optional[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Mock product catalogue
# ---------------------------------------------------------------------------

MOCK_PRODUCTS: List[Dict[str, Any]] = [
    {
        "id": "laptop-001",
        "name": "Acer Aspire 5",
        "description": '15.6" FHD laptop, Intel Core i5-1235U, 8GB RAM, 256GB SSD, Intel UHD Graphics, Windows 11 Home',
        "price": 379.99,
        "url": "/products/laptop-001",
    },
    {
        "id": "laptop-002",
        "name": "Lenovo IdeaPad 3",
        "description": '14" HD laptop, AMD Ryzen 5 5500U, 8GB RAM, 512GB SSD, AMD Radeon Graphics, Windows 11 Home',
        "price": 399.99,
        "url": "/products/laptop-002",
    },
    {
        "id": "laptop-003",
        "name": "HP Pavilion 15",
        "description": '15.6" FHD laptop, Intel Core i7-1255U, 16GB RAM, 512GB SSD, Intel Iris Xe, Windows 11 Home',
        "price": 549.99,
        "url": "/products/laptop-003",
    },
    {
        "id": "laptop-004",
        "name": "Dell Inspiron 16",
        "description": '16" 2K laptop, Intel Core i5-1340P, 16GB RAM, 1TB SSD, Intel Iris Xe, Windows 11 Pro',
        "price": 699.99,
        "url": "/products/laptop-004",
    },
    {
        "id": "laptop-005",
        "name": "ASUS VivoBook 15",
        "description": '15.6" FHD OLED laptop, Intel Core i3-1215U, 8GB RAM, 256GB SSD, Windows 11 Home',
        "price": 329.99,
        "url": "/products/laptop-005",
    },
    {
        "id": "ram-001",
        "name": "Corsair Vengeance LPX 16GB (2x8GB) DDR4",
        "description": "DDR4 3200MHz CL16, 1.35V, Intel XMP 2.0, black PCB, dual-channel desktop memory kit",
        "price": 49.99,
        "url": "/products/ram-001",
    },
    {
        "id": "ram-002",
        "name": "G.Skill Ripjaws V 32GB (2x16GB) DDR4",
        "description": "DDR4 3600MHz CL18, 1.35V, dual-channel kit, Intel XMP 2.0 ready",
        "price": 89.99,
        "url": "/products/ram-002",
    },
    {
        "id": "ram-003",
        "name": "Kingston Fury Beast 16GB (1x16GB) DDR5",
        "description": "DDR5 5200MHz CL40, 1.25V, Intel XMP 3.0 ready, desktop memory",
        "price": 64.99,
        "url": "/products/ram-003",
    },
    {
        "id": "gpu-001",
        "name": "NVIDIA GeForce RTX 4060",
        "description": "8GB GDDR6, PCIe 4.0 x8, 3072 CUDA cores, DLSS 3 capable, 115W TDP",
        "price": 299.99,
        "url": "/products/gpu-001",
    },
    {
        "id": "cpu-001",
        "name": "AMD Ryzen 5 7600",
        "description": "6 cores / 12 threads, AM5 socket, 3.8 GHz base / 5.1 GHz boost, 65W TDP, DDR5-5200 support",
        "price": 199.99,
        "url": "/products/cpu-001",
    },
    {
        "id": "ssd-001",
        "name": "Samsung 990 EVO 1TB NVMe",
        "description": "M.2 PCIe 4.0 x4 / 5.0 x2, read 5000 MB/s, write 4200 MB/s, TLC V-NAND",
        "price": 89.99,
        "url": "/products/ssd-001",
    },
]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def recommend_products(
    query: str,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> str:
    """Search for hardware products based on a natural-language query with optional price filtering.

    Translates the user's needs into a semantic search over the product catalogue.
    When min_price / max_price are provided they are applied as Pinecone metadata filters
    using $gte / $lte operators.
    Returns top 3 matching products as a JSON string."""
    metadata_filter = {}
    if min_price is not None:
        metadata_filter["price"] = {"$gte": min_price}
    if max_price is not None:
        metadata_filter["price"] = {"$lte": max_price}

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index("ramon-products")
    oai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    emb = oai.embeddings.create(input=query, model="text-embedding-3-small")
    results = index.query(
         vector=emb.data[0].embedding,
         top_k=3,
         include_metadata=True,
         filter=metadata_filter or None,
    )
    return json.dumps([{"id": m.id, **m.metadata, "score": m.score} for m in results.matches])

    # --- Mock implementation ---
    '''
    query_lower = query.lower()
    query_words = query_lower.split()

    candidates = list(MOCK_PRODUCTS)

    if min_price is not None:
        candidates = [p for p in candidates if p["price"] >= min_price]
    if max_price is not None:
        candidates = [p for p in candidates if p["price"] <= max_price]

    def score_product(p: Dict[str, Any]) -> int:
        text = (p["name"] + " " + p["description"]).lower()
        name_score = sum(2 for kw in query_words if kw in p["name"].lower())
        desc_score = sum(1 for kw in query_words if kw in text and kw not in p["name"].lower())
        return name_score + desc_score

    scored = sorted(((score_product(p), p) for p in candidates), key=lambda x: -x[0])
    top = [p for _, p in scored[:3]]
    if not top:
        top = candidates[:3] if candidates else MOCK_PRODUCTS[:3]

    return json.dumps(top, indent=2)
    '''


@tool
def search_component_spec(component_model: str) -> str:
    """Fetch technical specifications for an external hardware component from the web.

    Use when a user asks about compatibility with their own motherboard, CPU, GPU or other
    component so that you can compare specs against the product they are currently viewing."""
    try:
        tavily = TavilySearchResults(max_results=3)
        results = tavily.invoke({"query": f"{component_model} technical specifications specs"})
        return json.dumps(results, indent=2)
    except Exception as exc:
        return (
            f"[Web search unavailable: {exc}]\n\n"
            f"For component '{component_model}' you should verify:\n"
            f"- Motherboard: chipset, socket, memory standard (DDR4/DDR5), max frequency, form factor\n"
            f"- CPU: socket, supported memory type, TDP, generation\n"
            f"- GPU: PCIe version, physical dimensions, power connector requirements\n"
            f"Always consult the manufacturer's official page for definitive specs."
        )


tools = [recommend_products, search_component_spec]


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------
# todo: add guardrails
SYSTEM_PROMPT = (
    "You are a technical assistant for RAMon, an online hardware store. "
    "You help customers find products and answer hardware compatibility questions.\n\n"
    "Rules:\n"
    "1. If the user asks about compatibility with their own hardware (e.g. \"will this work "
    "with my motherboard X\"), look at the current_product context if available and use "
    "search_component_spec to fetch specs for the user's external component.\n"
    "2. If the user wants product recommendations, translate vague requirements (\"watching "
    "YouTube\", \"gaming\") into precise technical search terms like 'Intel Core i3 or Ryzen 3 processor, "
    "8GB RAM, 256GB SSD, long battery life' and call recommend_products. "
    "Extract budget constraints from the query and pass them as min_price / max_price.\n"
    "3. If the question is general or you already have enough facts, answer directly without "
    "calling tools.\n"
    "4. If you need more details from the user, ask clarifying questions before invoking tools.\n"
    "Be concise, technical, and helpful."
)


def chatbot(state: AgentState) -> Dict[str, Any]:
    """Main chatbot node: invokes the LLM with conversation history and tools."""
    product = state.get("current_product")
    prompt = SYSTEM_PROMPT
    if product:
        prompt += (
            f"\n\nThe user is currently viewing this product:\n"
            f"Name: {product.get('name', 'N/A')}\n"
            f"Description: {product.get('description', 'N/A')}\n"
            f"Price: ${product.get('price', 'N/A')}\n"
            f"If the user asks about compatibility, use search_component_spec to look up their hardware."
        )

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    model_with_tools = model.bind_tools(tools)

    messages = [SystemMessage(content=prompt)] + state["messages"]
    response = model_with_tools.invoke(messages)

    dispatch: Dict[str, Any] = {"messages": [response]}

    if recommendations := state.get("recommendations"):
        dispatch["recommendations"] = recommendations

    return dispatch


def process_tool_results(state: AgentState) -> Dict[str, Any]:
    """Extract product recommendations from the last ToolMessage into state."""
    for msg in reversed(state["messages"]):
        if isinstance(msg, ToolMessage) and msg.name == "recommend_products":
            try:
                parsed = json.loads(msg.content)
                if isinstance(parsed, list):
                    return {"recommendations": parsed}
            except (json.JSONDecodeError, TypeError):
                pass
            break
    return {}


def should_continue(state: AgentState) -> Literal["tools", END]:
    """Route to tools if the last message has tool_calls, otherwise end."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


# ---------------------------------------------------------------------------
# Build graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("chatbot", chatbot)
    graph.add_node("tools", ToolNode(tools))
    graph.add_node("process_tool_results", process_tool_results)

    graph.add_edge(START, "chatbot")
    graph.add_conditional_edges("chatbot", should_continue, {END: END, "tools": "tools"})
    graph.add_edge("tools", "process_tool_results")
    graph.add_edge("process_tool_results", "chatbot")

    return graph


# ---------------------------------------------------------------------------
# Main – test runs
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    graph = build_graph()
    app = graph.compile(checkpointer=MemorySaver())

    # ---- Test 1: Product Recommendation ----
    print("=" * 72)
    print("TEST 1 — Product Recommendation")
    print('User: "I need a laptop for watching YouTube videos at college that costs under 400 dollars"')
    print("current_product: None")
    print("=" * 72)

    config1 = {"configurable": {"thread_id": "test-1"}}
    state1: AgentState = {
        "messages": [
            HumanMessage(
                content="I need a laptop for watching YouTube videos at college that costs under 400 dollars"
            )
        ],
        "current_product": None,
        "recommendations": [],
    }

    for event in app.stream(state1, config1, stream_mode="values"):
        if "messages" not in event:
            continue
        msg = event["messages"][-1]
        if isinstance(msg, HumanMessage):
            print(f"\n  > Human: {msg.content}")
        elif isinstance(msg, AIMessage) and msg.content:
            print(f"\n  > Assistant: {msg.content}")
        elif isinstance(msg, ToolMessage):
            snippet = msg.content[:300].replace("\n", " ")
            print(f"\n  > Tool ({msg.name}): {snippet}")

    print("\n" + "=" * 72)
    print("TEST 2 — Technical Compatibility")
    print('User: "Is this memory RAM compatible with my ASUS Prime B450M motherboard?"')
    print("current_product: Corsair Vengeance LPX 16GB (2x8GB) DDR4")
    print("=" * 72)

    current_ram: Dict[str, Any] = {
        "id": "ram-001",
        "name": "Corsair Vengeance LPX 16GB (2x8GB) DDR4",
        "description": "DDR4 3200MHz CL16, 1.35V, Intel XMP 2.0, black PCB, dual-channel desktop memory kit",
        "price": 49.99,
        "url": "/products/ram-001",
    }

    config2 = {"configurable": {"thread_id": "test-2"}}
    state2: AgentState = {
        "messages": [
            HumanMessage(
                content="Is this memory RAM compatible with my ASUS Prime B450M motherboard?"
            )
        ],
        "current_product": current_ram,
        "recommendations": [],
    }

    for event in app.stream(state2, config2, stream_mode="values"):
        if "messages" not in event:
            continue
        msg = event["messages"][-1]
        if isinstance(msg, HumanMessage):
            print(f"\n  > Human: {msg.content}")
        elif isinstance(msg, AIMessage) and msg.content:
            print(f"\n  > Assistant: {msg.content}")
        elif isinstance(msg, ToolMessage):
            snippet = msg.content[:300].replace("\n", " ")
            print(f"\n  > Tool ({msg.name}): {snippet}")
