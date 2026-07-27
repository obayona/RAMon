"""Unit tests for src.api.routes.websocket.ChatMessage."""
from src.api.routes.websocket import ChatMessage


class TestChatMessageFromRaw:
    def test_valid_json(self) -> None:
        raw = '{"message": "hello", "current_product_id": "prod-123"}'
        msg = ChatMessage.from_raw(raw)
        assert msg.message == "hello"
        assert msg.current_product_id == "prod-123"

    def test_only_message(self) -> None:
        raw = '{"message": "hello"}'
        msg = ChatMessage.from_raw(raw)
        assert msg.message == "hello"
        assert msg.current_product_id is None

    def test_invalid_json_falls_back(self) -> None:
        msg = ChatMessage.from_raw("just plain text")
        assert msg.message == "just plain text"
        assert msg.current_product_id is None

    def test_empty_message_stripped(self) -> None:
        raw = '{"message": "", "current_product_id": "p1"}'
        msg = ChatMessage.from_raw(raw)
        assert msg.message == ""
        assert msg.current_product_id == "p1"

    def test_whitespace_message_stripped(self) -> None:
        raw = '{"message": "  hello  ", "current_product_id": "p1"}'
        msg = ChatMessage.from_raw(raw)
        assert msg.message == "hello"

    def test_empty_product_id_normalized_to_none(self) -> None:
        raw = '{"message": "hi", "current_product_id": ""}'
        msg = ChatMessage.from_raw(raw)
        assert msg.current_product_id is None

    def test_whitespace_product_id_normalized_to_none(self) -> None:
        raw = '{"message": "hi", "current_product_id": "   "}'
        msg = ChatMessage.from_raw(raw)
        assert msg.current_product_id is None

    def test_null_product_id(self) -> None:
        raw = '{"message": "hi", "current_product_id": null}'
        msg = ChatMessage.from_raw(raw)
        assert msg.current_product_id is None

    def test_missing_message_key(self) -> None:
        raw = '{"current_product_id": "p1"}'
        msg = ChatMessage.from_raw(raw)
        assert msg.message == ""
        assert msg.current_product_id == "p1"


class TestChatMessageInit:
    def test_init(self) -> None:
        msg = ChatMessage(message="hi", current_product_id="p1")
        assert msg.message == "hi"
        assert msg.current_product_id == "p1"

    def test_init_none_product(self) -> None:
        msg = ChatMessage(message="hi", current_product_id=None)
        assert msg.current_product_id is None
