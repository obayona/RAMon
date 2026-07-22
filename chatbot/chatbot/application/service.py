"""Chatbot service providing the main API for chat interactions."""
from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List, Optional

import structlog
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

logger = structlog.get_logger("ramon.chatbot.service")


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
        logger.debug("ainvoke.start", chat_id=chat_id, message_length=len(message))
        state: ChatbotState = {
            "messages": [HumanMessage(content=message)],
            "current_product": current_product,
            "recommendations": [],
            "product_query": None,
        }

        result = await self._app.ainvoke(state, {"configurable": {"thread_id": chat_id}})
        logger.debug("ainvoke.complete", chat_id=chat_id)
        return result

    async def stream(
        self,
        message: str,
        current_product: Optional[Product] = None,
        chat_id: str = "default",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream text tokens and product recommendations in real-time.

        Text is streamed as it arrives from the LLM. When the LLM outputs a
        <products/> marker, the parser injects the actual products from state.

        Yields:
            Dict with keys:
            - type="text": {"id", "type", "content"}
            - type="ui_data": {"id", "type", "layout", "products"}
        """
        logger.debug("stream.start", chat_id=chat_id, message_length=len(message))
        state: ChatbotState = {
            "messages": [HumanMessage(content=message)],
            "current_product": current_product,
            "recommendations": [],
            "product_query": None,
        }

        config = {"configurable": {"thread_id": chat_id}}
        message_id: Optional[str] = None

        # Parser is created lazily once we have products from state
        parser: Optional[ProductMarkerParser] = None
        recommendations: List[Dict[str, Any]] = []

        # Track which node we're streaming from to avoid mixing outputs
        # Only stream from: chatbot (final response) or process_recommendations
        stream_nodes = {"chatbot", "process_recommendations"}

        async for msg, metadata in self._app.astream(
            state,
            config,
            stream_mode="messages",
        ):
            node_name = metadata.get("langgraph_node", "")

            # Only process AI messages from allowed nodes
            # Skip messages from chatbot when it's deciding to call tools (has tool_calls)
            if (
                msg.content
                and isinstance(msg, AIMessage)
                and node_name in stream_nodes
                and not msg.tool_calls
            ):
                if not message_id:
                    message_id = metadata.get("run_id") or getattr(msg, "id", None)

                # Create parser with products on first content from process_recommendations
                if parser is None:
                    # Get current state to access recommendations
                    current_state = await self._app.aget_state(config)
                    recommendations = current_state.values.get("recommendations", [])
                    parser = ProductMarkerParser(products=recommendations)

                for event in parser.feed(msg.content):
                    yield self._make_stream_event(event, message_id, chat_id)

        # Flush any remaining buffered content
        if parser is not None:
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
        logger.debug("get_chat_history.start", chat_id=chat_id)
        config = {"configurable": {"thread_id": chat_id}}
        state = await self._app.aget_state(config)

        if not state or "messages" not in state.values:
            raise ChatNotFoundError(f"Chat '{chat_id}' not found")

        messages = state.values["messages"]
        if not messages:
            raise ChatNotFoundError(f"Chat '{chat_id}' has no messages")

        # Get recommendations from state to inject into <products/> markers
        recommendations = state.values.get("recommendations", [])
        return self._format_messages(messages, recommendations)

    def _format_messages(
        self,
        messages: List[BaseMessage],
        recommendations: List[Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        """Format message history for API responses.

        Parses <products/> markers in AI messages and injects products data.

        Args:
            messages: List of messages from state.
            recommendations: Products to inject when <products/> marker is found.
        """
        formatted: List[Dict[str, Any]] = []
        products_to_inject = recommendations or []

        for msg in messages:
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                # Parse the message content for product markers
                parsed_content = self._parse_message_content(msg.content, products_to_inject)
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

    def _parse_message_content(
        self,
        content: str,
        products: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """Parse message content to extract text and product markers.

        Args:
            content: Raw message content potentially containing <products/> markers.
            products: Products to inject when <products/> marker is found.

        Returns:
            Dict with 'text' (cleaned content) and 'products' (list or None).
        """
        parser = ProductMarkerParser(products=products or [])
        events = parser.feed(content)
        events.extend(parser.flush())

        text_parts = []
        parsed_products = None

        for event in events:
            if event["type"] == "text":
                text_parts.append(event["content"])
            elif event["type"] == "products":
                parsed_products = event["data"]

        return {
            "text": "".join(text_parts).strip(),
            "products": parsed_products,
        }

    @property
    def compiled_graph(self) -> CompiledStateGraph:
        """Direct access to the underlying compiled graph (advanced use)."""
        return self._app
