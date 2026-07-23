"""Product relevance filtering based on LLM-judged IDs."""
from __future__ import annotations

import re
from typing import Any, Dict, List

_PRODUCTS_TAG_RE = re.compile(r'<products\s+ids="([^"]*)"\s*/>')


def parse_relevant_ids(tag_content: str) -> set[int]:
    """Extract product IDs from a <products ids="1,2,3"/> tag string.

    Args:
        tag_content: Full string that may contain the tag.

    Returns:
        Set of integer IDs found in the tag, or empty set if no tag found.
    """
    match = _PRODUCTS_TAG_RE.search(tag_content)
    if not match:
        return set()
    raw = match.group(1).strip()
    if not raw:
        return set()
    return {int(pid.strip()) for pid in raw.split(",") if pid.strip()}


def filter_by_ids(
    products: List[Dict[str, Any]], relevant_ids: set[int]
) -> List[Dict[str, Any]]:
    """Filter a product list to only those whose IDs are in the relevant set.

    Args:
        products: List of product dicts (each must have an "id" key).
        relevant_ids: Set of IDs to keep.

    Returns:
        Filtered list containing only products with matching IDs.
    """
    return [p for p in products if p.get("id") in relevant_ids]


def filter_products_from_response(
    products: List[Dict[str, Any]], response_content: str
) -> List[Dict[str, Any]]:
    """Parse relevant IDs from an LLM response and filter the product list.

    Convenience function that combines parse_relevant_ids and filter_by_ids.

    Args:
        products: Full list of product dicts from the database.
        response_content: LLM response text containing <products ids="..."/>.

    Returns:
        Filtered product list, or empty list if no valid tag found.
    """
    ids = parse_relevant_ids(response_content)
    if not ids:
        return []
    return filter_by_ids(products, ids)
