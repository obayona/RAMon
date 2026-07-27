"""Unit tests for chatbot.application.relevance — pure filtering logic."""

from chatbot.application.relevance import (
    filter_by_ids,
    filter_products_from_response,
    parse_relevant_ids,
)


# ---------------------------------------------------------------------------
# parse_relevant_ids
# ---------------------------------------------------------------------------


class TestParseRelevantIds:
    def test_single_id(self) -> None:
        result = parse_relevant_ids('text <products ids="42"/> after')
        assert result == {42}

    def test_multiple_ids(self) -> None:
        result = parse_relevant_ids('<products ids="1,2,3"/>')
        assert result == {1, 2, 3}

    def test_ids_with_whitespace(self) -> None:
        result = parse_relevant_ids('<products ids=" 1 , 2 , 3 "/>')
        assert result == {1, 2, 3}

    def test_no_tag_returns_empty(self) -> None:
        assert parse_relevant_ids("just plain text") == set()

    def test_empty_ids_returns_empty(self) -> None:
        assert parse_relevant_ids('<products ids=""/>') == set()

    def test_whitespace_only_ids_returns_empty(self) -> None:
        assert parse_relevant_ids('<products ids="   "/>') == set()

    def test_surrounding_text_ignored(self) -> None:
        result = parse_relevant_ids('before <products ids="5"/> after')
        assert result == {5}

    def test_large_ids(self) -> None:
        result = parse_relevant_ids('<products ids="100000,200000"/>')
        assert result == {100000, 200000}

    def test_malformed_tag_no_closing(self) -> None:
        assert parse_relevant_ids('<products ids="1,2">') == set()

    def test_partial_match_not_valid(self) -> None:
        assert parse_relevant_ids("products ids") == set()


# ---------------------------------------------------------------------------
# filter_by_ids
# ---------------------------------------------------------------------------


class TestFilterByIds:
    def test_filters_matching_ids(self) -> None:
        products = [
            {"id": 1, "name": "A"},
            {"id": 2, "name": "B"},
            {"id": 3, "name": "C"},
        ]
        result = filter_by_ids(products, {1, 3})
        assert len(result) == 2
        assert result[0]["name"] == "A"
        assert result[1]["name"] == "C"

    def test_empty_ids_returns_empty(self) -> None:
        products = [{"id": 1, "name": "A"}]
        assert filter_by_ids(products, set()) == []

    def test_no_matching_ids_returns_empty(self) -> None:
        products = [{"id": 1, "name": "A"}]
        assert filter_by_ids(products, {99}) == []

    def test_empty_products_returns_empty(self) -> None:
        assert filter_by_ids([], {1, 2}) == []

    def test_preserves_product_dict_structure(self) -> None:
        products = [{"id": 1, "name": "X", "price": 99.99, "extra": True}]
        result = filter_by_ids(products, {1})
        assert result[0] == {"id": 1, "name": "X", "price": 99.99, "extra": True}

    def test_product_without_id_key_not_matched(self) -> None:
        products = [{"name": "no-id-key"}]
        assert filter_by_ids(products, {1}) == []

    def test_duplicate_ids_not_duplicated(self) -> None:
        products = [{"id": 1, "name": "A"}]
        result = filter_by_ids(products, {1})
        assert len(result) == 1


# ---------------------------------------------------------------------------
# filter_products_from_response
# ---------------------------------------------------------------------------


class TestFilterProductsFromResponse:
    def test_extracts_and_filters(self) -> None:
        products = [
            {"id": 1, "name": "Laptop"},
            {"id": 2, "name": "Mouse"},
            {"id": 3, "name": "Keyboard"},
        ]
        response = 'Here is a laptop: <products ids="1,3"/>'
        result = filter_products_from_response(products, response)
        assert len(result) == 2
        assert result[0]["name"] == "Laptop"
        assert result[1]["name"] == "Keyboard"

    def test_no_tag_returns_empty(self) -> None:
        products = [{"id": 1, "name": "Laptop"}]
        result = filter_products_from_response(products, "No products here")
        assert result == []

    def test_empty_product_list(self) -> None:
        result = filter_products_from_response([], '<products ids="1"/>')
        assert result == []

    def test_irrelevant_ids_returns_empty(self) -> None:
        products = [{"id": 1, "name": "Laptop"}]
        result = filter_products_from_response(products, '<products ids="99"/>')
        assert result == []

    def test_empty_ids_tag_returns_empty(self) -> None:
        products = [{"id": 1}]
        result = filter_products_from_response(products, '<products ids=""/>')
        assert result == []
