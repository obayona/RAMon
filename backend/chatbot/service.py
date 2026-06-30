from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph
from langchain_tavily import TavilySearch
from openai import OpenAI

from chatbot.graph import build_graph
from chatbot.state import AgentState, Product
from chatbot.tools import build_tools


class ChatNotFoundError(Exception):
    """Raised when a chat thread could not be resolved."""


class ChatbotService:
    """Production-ready LangGraph chatbot for product recommendations and
    hardware compatibility assistance.

    All external clients (OpenAI, Pinecone, Tavily) are initialised once at
    construction time and wired into the tools via closures — no module-level
    state, no mocks, no circular imports.
    """

    def __init__(
        self,
        *,
        openai_client: OpenAI,
        pinecone_index: Any,
        tavily_client: TavilySearch,
        chat_model: ChatOpenAI,
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        if not openai_client:
            raise ValueError("openai_client must be provided")
        if not pinecone_index:
            raise ValueError("pinecone_index must be provided")
        if not tavily_client:
            raise ValueError("tavily_client must be provided")

        self._openai_client = openai_client
        self._pinecone_index = pinecone_index
        self._tavily_client = tavily_client
        self._model = chat_model

        self._tools = build_tools(
            openai_client=self._openai_client,
            pinecone_index=self._pinecone_index,
            tavily_client=self._tavily_client,
        )

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
        chat_id: str = "default",
    ) -> AgentState:
        """Run the full graph to completion and return the final state."""
        state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "current_product": current_product,
            "recommendations": [],
        }
        return self._app.invoke(state, {"configurable": {"thread_id": chat_id}})

    async def stream(
        self,
        message: str,
        current_product: Optional[Product] = None,
        chat_id: str = "default",
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
        
        config = {"configurable": {"thread_id": chat_id}}

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
                "id": message_id or f"ui-{chat_id}",
                "type": "ui_data",
                "layout": "carousel",
                "products": recommendations
            }

    async def get_chat_history(self, chat_id: str) -> List[Dict[str, Any]]:
        config = {"configurable": {"thread_id": chat_id}}
        state = await self._app.aget_state(config)

        if not state or "messages" not in state.values:
            raise ChatNotFoundError(f"Chat '{chat_id}' not found")

        messages = state.values["messages"]
        if not messages:
            raise ChatNotFoundError(f"Chat '{chat_id}' has no messages")

        return self._format_messages(messages)

    def _format_messages(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        formatted: List[Dict[str, Any]] = []
        for msg in messages:
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                formatted.append(
                    {
                        "id": getattr(msg, "id", None),
                        "type": "ai",
                        "text": msg.content,
                        "ui_data": msg.additional_kwargs.get("ui_payload"),
                    }
                )
            elif isinstance(msg, HumanMessage):
                formatted.append(
                    {
                        "id": getattr(msg, "id", None),
                        "type": "human",
                        "text": msg.content,
                    }
                )

        return formatted

    @property
    def compiled_graph(self) -> CompiledStateGraph:
        """Direct access to the underlying compiled graph (advanced use)."""
        return self._app
