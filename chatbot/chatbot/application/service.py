"""Chatbot service providing the main API for chat interactions."""
from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph
from openai import OpenAI

from chatbot.application.graph import build_graph
from chatbot.application.parser import ProductMarkerParser
from chatbot.domain import ChatbotState, Product, EmbeddingService, ProductRepository
from chatbot.tools import build_tools


class ChatNotFoundError(Exception):
    """Raised when a chat thread could not be resolved."""


class ChatbotService:
    """Production-ready LangGraph chatbot for product recommendations and
    hardware compatibility assistance.
    """

    def __init__(
        self,
        *,
        openai_client: OpenAI,
        chat_model: ChatOpenAI,
        checkpointer: BaseCheckpointSaver,
        tavily_client: TavilySearch,
        embedding_service: EmbeddingService,
        product_repository: ProductRepository,
    ) -> None:
        if not openai_client:
            raise ValueError("openai_client must be provided")
        if not tavily_client:
            raise ValueError("tavily_client must be provided")
        if not embedding_service:
            raise ValueError("embedding_service must be provided")
        if not product_repository:
            raise ValueError("product_repository must be provided")

        self._openai_client = openai_client
        self._tavily_client = tavily_client
        self._model = chat_model
        self._embedding_service = embedding_service
        self._product_repository = product_repository

        self._tools = build_tools(
            embedding_service=self._embedding_service,
            product_repository=self._product_repository,
            tavily_client=self._tavily_client,
        )

        self._app: CompiledStateGraph = (
            build_graph(self._model, self._tools)
            .compile(checkpointer=checkpointer)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ainvoke(
        self,
        message: str,
        current_product: Optional[Product] = None,
        chat_id: str = "default",
    ) -> ChatbotState:
        """Run the full graph to completion and return the final state (async)."""
        state: ChatbotState = {
            "messages": [HumanMessage(content=message)],
            "current_product": current_product,
            "recommendations": [],
            "product_query": None,
        }

        return await self._app.ainvoke(state, {"configurable": {"thread_id": chat_id}})

    async def stream(
        self,
        message: str,
        current_product: Optional[Product] = None,
        chat_id: str = "default",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream text tokens and product recommendations in real-time.

        Text is streamed as it arrives from the LLM. Product recommendations
        are parsed from <products>...</products> markers in the LLM output
        and emitted as separate ui_data events.

        Yields:
            Dict with keys:
            - type="text": {"id", "type", "content"}
            - type="ui_data": {"id", "type", "layout", "products"}
        """
        state: ChatbotState = {
            "messages": [HumanMessage(content=message)],
            "current_product": current_product,
            "recommendations": [],
            "product_query": None,
        }

        config = {"configurable": {"thread_id": chat_id}}
        message_id: Optional[str] = None
        parser = ProductMarkerParser()

        async for msg, metadata in self._app.astream(
            state,
            config,
            stream_mode="messages",
        ):
            # Process AI message content through the parser
            if msg.content and isinstance(msg, AIMessage):
                if not message_id:
                    message_id = metadata.get("run_id") or getattr(msg, "id", None)

                for event in parser.feed(msg.content):
                    yield self._make_stream_event(event, message_id, chat_id)

        # Flush any remaining buffered content
        for event in parser.flush():
            yield self._make_stream_event(event, message_id, chat_id)

    def _make_stream_event(
        self,
        parsed_event: Dict[str, Any],
        message_id: Optional[str],
        chat_id: str,
    ) -> Dict[str, Any]:
        """Convert a parsed event to the stream output format."""
        if parsed_event["type"] == "text":
            return {
                "id": message_id,
                "type": "text",
                "content": parsed_event["content"],
            }
        elif parsed_event["type"] == "products":
            return {
                "id": message_id or f"ui-{chat_id}",
                "type": "ui_data",
                "layout": "carousel",
                "products": parsed_event["data"],
            }
        # Fallback for unknown event types
        return {
            "id": message_id,
            "type": "text",
            "content": str(parsed_event),
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
        """Format message history for API responses.

        Parses <products>...</products> markers in AI messages and extracts
        them as separate ui_data entries for frontend rendering.
        """
        formatted: List[Dict[str, Any]] = []
        for msg in messages:
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                # Parse the message content for product markers
                parsed_content = self._parse_message_content(msg.content)
                msg_id = getattr(msg, "id", None)

                # Add text portion
                if parsed_content["text"]:
                    formatted.append(
                        {
                            "id": msg_id,
                            "type": "ai",
                            "text": parsed_content["text"],
                        }
                    )

                # Add products as ui_data if present
                if parsed_content["products"]:
                    formatted.append(
                        {
                            "id": msg_id,
                            "type": "ui_data",
                            "layout": "carousel",
                            "products": parsed_content["products"],
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

    def _parse_message_content(self, content: str) -> Dict[str, Any]:
        """Parse message content to extract text and product markers.

        Args:
            content: Raw message content potentially containing <products> markers.

        Returns:
            Dict with 'text' (cleaned content) and 'products' (list or None).
        """
        parser = ProductMarkerParser()
        events = parser.feed(content)
        events.extend(parser.flush())

        text_parts = []
        products = None

        for event in events:
            if event["type"] == "text":
                text_parts.append(event["content"])
            elif event["type"] == "products":
                products = event["data"]

        return {
            "text": "".join(text_parts).strip(),
            "products": products,
        }

    @property
    def compiled_graph(self) -> CompiledStateGraph:
        """Direct access to the underlying compiled graph (advanced use)."""
        return self._app
