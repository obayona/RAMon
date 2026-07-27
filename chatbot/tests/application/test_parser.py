"""Unit tests for chatbot.application.parser — streaming product marker parser."""

from chatbot.application.parser import ProductMarkerParser


SAMPLE_PRODUCTS = [
    {"id": 1, "name": "Laptop", "price": 999},
    {"id": 2, "name": "Mouse", "price": 25},
    {"id": 3, "name": "Keyboard", "price": 75},
]


class TestProductMarkerParserFeed:
    def test_plain_text_no_tag(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        events = parser.feed("Hello world")
        assert len(events) == 1
        assert events[0] == {"type": "text", "content": "Hello world"}

    def test_complete_tag_in_one_chunk(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        events = parser.feed('Text before <products ids="1,2"/> after')
        text_events = [e for e in events if e["type"] == "text"]
        product_events = [e for e in events if e["type"] == "products"]
        assert len(product_events) == 1
        assert len(product_events[0]["data"]) == 2
        assert product_events[0]["data"][0]["name"] == "Laptop"
        assert product_events[0]["data"][1]["name"] == "Mouse"
        assert "".join(e["content"] for e in text_events) == "Text before  after"

    def test_tag_only_no_surrounding_text(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        events = parser.feed('<products ids="3"/>')
        product_events = [e for e in events if e["type"] == "products"]
        assert len(product_events) == 1
        assert product_events[0]["data"][0]["name"] == "Keyboard"

    def test_multiple_tags_in_one_chunk(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        events = parser.feed('<products ids="1"/> then <products ids="2"/>')
        product_events = [e for e in events if e["type"] == "products"]
        assert len(product_events) == 2
        assert product_events[0]["data"][0]["id"] == 1
        assert product_events[1]["data"][0]["id"] == 2

    def test_partial_tag_held_back(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        events = parser.feed("Hello <products ids=")
        assert len(events) == 1
        assert events[0] == {"type": "text", "content": "Hello "}
        assert parser._buffer == "<products ids="

    def test_partial_tag_completed_in_next_chunk(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        events1 = parser.feed('Hello <products ids="')
        assert events1 == [{"type": "text", "content": "Hello "}]
        events2 = parser.feed('1"/>')
        product_events = [e for e in events2 if e["type"] == "products"]
        assert len(product_events) == 1
        assert product_events[0]["data"][0]["id"] == 1

    def test_empty_chunk(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        events = parser.feed("")
        assert events == []

    def test_text_only_after_tag(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        events = parser.feed('<products ids="1"/> and some text')
        text_parts = [e["content"] for e in events if e["type"] == "text"]
        assert "and some text" in "".join(text_parts)


class TestProductMarkerParserFlush:
    def test_flush_empty_buffer(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        assert parser.flush() == []

    def test_flush_with_remaining_text(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        events = parser.feed("Hello world")
        assert len(events) == 1
        assert events[0] == {"type": "text", "content": "Hello world"}
        assert parser.flush() == []

    def test_flush_after_partial_tag(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        parser.feed('<products ids="')
        events = parser.flush()
        assert len(events) == 1
        assert events[0]["type"] == "text"
        assert "products" in events[0]["content"]

    def test_flush_clears_buffer(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        parser.feed("data")
        parser.flush()
        assert parser._buffer == ""


class TestProductMarkerParserStreaming:
    def test_full_stream_simulation(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        all_events = []

        chunks = [
            "I recommend the ",
            '<products ids="1,2"/>',
            " for your setup.",
        ]
        for chunk in chunks:
            all_events.extend(parser.feed(chunk))
        all_events.extend(parser.flush())

        text_content = "".join(e["content"] for e in all_events if e["type"] == "text")
        product_events = [e for e in all_events if e["type"] == "products"]

        assert "I recommend the " in text_content
        assert " for your setup." in text_content
        assert len(product_events) == 1
        assert len(product_events[0]["data"]) == 2

    def test_stream_with_split_across_many_chunks(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        all_events = []

        # Split the tag across 4 chunks
        all_events.extend(parser.feed("Start <prod"))
        all_events.extend(parser.feed('ucts ids="'))
        all_events.extend(parser.feed("1"))
        all_events.extend(parser.feed('"/> End'))
        all_events.extend(parser.flush())

        product_events = [e for e in all_events if e["type"] == "products"]
        assert len(product_events) == 1
        assert product_events[0]["data"][0]["id"] == 1

    def test_no_products_filtered_correctly(self) -> None:
        parser = ProductMarkerParser(products=SAMPLE_PRODUCTS)
        events = parser.feed('<products ids="999"/>')
        product_events = [e for e in events if e["type"] == "products"]
        assert len(product_events) == 1
        assert product_events[0]["data"] == []

    def test_empty_products_list(self) -> None:
        parser = ProductMarkerParser(products=[])
        events = parser.feed('<products ids="1,2"/>')
        product_events = [e for e in events if e["type"] == "products"]
        assert len(product_events) == 1
        assert product_events[0]["data"] == []
