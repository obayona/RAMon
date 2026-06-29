from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from langchain_tavily import TavilySearch
from openai import OpenAI
from pinecone import Pinecone

from chatbot.graph import build_graph
from chatbot.state import AgentState, Product
from chatbot.tools import build_tools


class ChatbotService:
    """Production-ready LangGraph chatbot for product recommendations and
    hardware compatibility assistance.

    All external clients (OpenAI, Pinecone, Tavily) are initialised once at
    construction time and wired into the tools via closures — no module-level
    state, no mocks, no circular imports.
    """

    def __init__(
        self,
        openai_api_key: str,
        pinecone_api_key: str,
        tavily_api_key: str,
        checkpointer: BaseCheckpointSaver,
        temperature: float = 0,
        model_name: str = "gpt-4o-mini",
        pinecone_index_name: str = "ramon-products",
    ) -> None:
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
            .compile(checkpointer=checkpointer)
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

    async def stream(
        self,
        message: str,
        current_product: Optional[Dict[str, Any]] = None,
        thread_id: str = "default",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams text tokens in real-time, followed by an end-of-stream payload 
        containing structured data if recommendations were made.
        """
        state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "current_product": current_product,
            "recommendations": [],
        }
        
        config = {"configurable": {"thread_id": thread_id}}

        message_id: Optional[str] = None

        # Use multiple stream modes simultaneously
        # 'messages' gives us real-time LLM tokens
        # 'updates' lets us capture state attributes when nodes finish
        async for msg, metadata in self._app.astream(
            state,
            config,
            stream_mode='messages',
        ):
            # Extract and yield raw text tokens as they stream from OpenAI
            if msg.content and isinstance(msg, AIMessage):
                if not message_id:
                    message_id = metadata.get("run_id") or getattr(msg, "id", None)

                yield {
                    "id": message_id,
                    "type": "text",
                    "content": msg.content
                }

        # Read the final overall state directly from memory/checkpoint store
        final_state = await self._app.aget_state(config)
        recommendations = final_state.values.get("recommendations", [])

        if recommendations:
            yield {
                "id": message_id or f"ui-{thread_id}",
                "type": "ui_data",
                "layout": "carousel",
                "products": recommendations
            }

    @property
    def compiled_graph(self) -> CompiledStateGraph:
        """Direct access to the underlying compiled graph (advanced use)."""
        return self._app
