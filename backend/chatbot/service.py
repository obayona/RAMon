import os
from typing import Any, Dict, Generator, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from langchain_tavily import TavilySearch
from openai import OpenAI
from pinecone import Pinecone

from chatbot.graph import build_graph
from chatbot.state import AgentState, Product
from chatbot.tools import build_tools

load_dotenv()


class ChatbotService:
    """Production-ready LangGraph chatbot for product recommendations and
    hardware compatibility assistance.

    All external clients (OpenAI, Pinecone, Tavily) are initialised once at
    construction time and wired into the tools via closures — no module-level
    state, no mocks, no circular imports.
    """

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0,
        *,
        openai_api_key: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        pinecone_index_name: str = "ramon-products",
        tavily_api_key: Optional[str] = None,
    ) -> None:
        # ---- resolve credentials -------------------------------------------------
        openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")

        if not openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required — set it via the constructor, "
                "the OPENAI_API_KEY env var, or a .env file."
            )
        if not pinecone_api_key:
            raise ValueError(
                "PINECONE_API_KEY is required — set it via the constructor, "
                "the PINECONE_API_KEY env var, or a .env file."
            )

        # ---- initialise external clients -----------------------------------------
        self._openai_client = OpenAI(api_key=openai_api_key)
        self._pinecone_index = Pinecone(api_key=pinecone_api_key).Index(
            pinecone_index_name
        )
        self._tavily_client = TavilySearch(max_results=3, tavily_api_key=tavily_api_key)

        # ---- build tools (each tool closes over its dependencies) -----------------
        self._tools = build_tools(
            openai_client=self._openai_client,
            pinecone_index=self._pinecone_index,
            tavily_client=self._tavily_client,
        )

        # ---- build + compile graph ------------------------------------------------
        self._model = ChatOpenAI(model=model_name, temperature=temperature)
        self._app: CompiledStateGraph = (
            build_graph(self._model, self._tools)
            .compile(checkpointer=MemorySaver())
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def invoke(
        self,
        message: str,
        current_product: Optional[Product] = None,
        thread_id: str = "default",
    ) -> AgentState:
        """Run the full graph to completion and return the final state."""
        state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "current_product": current_product,
            "recommendations": [],
        }
        return self._app.invoke(state, {"configurable": {"thread_id": thread_id}})

    def stream(
        self,
        message: str,
        current_product: Optional[Product] = None,
        thread_id: str = "default",
    ) -> Generator[Dict[str, Any], None, None]:
        """Yield node-level state snapshots as the graph executes."""
        state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "current_product": current_product,
            "recommendations": [],
        }
        yield from self._app.stream(
            state,
            {"configurable": {"thread_id": thread_id}},
            stream_mode="values",
        )

    def get_recommendations(self, thread_id: str = "default") -> List[Product]:
        """Return the ``recommendations`` stored for a given thread."""
        try:
            snapshot = self._app.get_state(
                {"configurable": {"thread_id": thread_id}}
            )
            return snapshot.values.get("recommendations", [])
        except (KeyError, AttributeError):
            return []

    @property
    def compiled_graph(self) -> CompiledStateGraph:
        """Direct access to the underlying compiled graph (advanced use)."""
        return self._app
