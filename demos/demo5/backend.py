"""
Author: L. Saetta
Last modified: 2026-04-08
License: MIT

Description:
    Backend logic for Demo 5 vector-store chunk exploration UI.
"""

from __future__ import annotations

from typing import Any

from common import get_inference_client
from config import REGION
from config_private import PROJECT_ID, VECTOR_STORE_ID

DEFAULT_REGION = REGION
DEFAULT_MAX_RESULTS = 10


def create_client():
    """Create the configured OpenAI-compatible inference client."""
    return get_inference_client()


def get_runtime_config() -> dict[str, str]:
    """Return effective runtime config used by this demo."""
    return {
        "region": DEFAULT_REGION,
        "vector_store_id": VECTOR_STORE_ID or "",
    }


def _as_dict(value: Any) -> dict[str, Any]:
    """Normalize optional dict-like values."""
    if isinstance(value, dict):
        return value
    return {}


def _normalize_pages(value: Any) -> list[Any]:
    """Normalize page numbers to a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def extract_chunk_text(item: Any) -> str:
    """Extract chunk text from a search result item."""
    content = getattr(item, "content", None)
    if isinstance(content, list):
        text_parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and block.get("text"):
                    text_parts.append(str(block["text"]))
                continue

            if getattr(block, "type", None) == "text" and getattr(block, "text", None):
                text_parts.append(str(block.text))

        if text_parts:
            return "\n".join(text_parts).strip()

    text = getattr(item, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    return ""


def normalize_search_item(item: Any, rank: int) -> dict[str, Any]:
    """Convert one API item to a stable shape for rendering."""
    additional_properties = _as_dict(getattr(item, "additional_properties", None))
    pages = _normalize_pages(additional_properties.get("page_numbers"))

    return {
        "rank": rank,
        "score": float(getattr(item, "score", 0.0) or 0.0),
        "filename": getattr(item, "filename", None) or "unknown_file",
        "file_id": getattr(item, "file_id", None) or "",
        "chunk_id": additional_properties.get("chunk_id", "N/A"),
        "pages": pages,
        "text": extract_chunk_text(item),
        "metadata": additional_properties,
    }


def normalize_search_results(search_results: Any) -> list[dict[str, Any]]:
    """Normalize and sort search results by score descending."""
    raw_items = list(getattr(search_results, "data", []) or [])
    sorted_items = sorted(
        raw_items,
        key=lambda item: getattr(item, "score", 0.0) or 0.0,
        reverse=True,
    )
    return [
        normalize_search_item(item, rank=index)
        for index, item in enumerate(sorted_items, start=1)
    ]


def search_vector_store(
    client, *, query: str, max_num_results: int
) -> list[dict[str, Any]]:
    """Run semantic search on configured vector store and return normalized items."""
    search_results = client.vector_stores.search(
        vector_store_id=VECTOR_STORE_ID,
        query=query,
        max_num_results=max_num_results,
        extra_headers={"OpenAI-Project": PROJECT_ID},
    )
    return normalize_search_results(search_results)
