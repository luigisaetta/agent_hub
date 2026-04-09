"""
Author: L. Saetta
Last modified: 2026-04-09
License: MIT

Description:
    SemanticSearcher runnable and search normalization helpers for Demo 6 backend.
"""

# pylint: disable=redefined-builtin

from __future__ import annotations

from typing import Any, Callable

from langchain_core.runnables.base import Runnable

from common import get_inference_client
from config_private import PROJECT_ID


def _as_dict(value: Any) -> dict[str, Any]:
    """Return value as dict when possible, otherwise return an empty dict."""
    if isinstance(value, dict):
        return value
    return {}


def _normalize_pages(value: Any) -> list[Any]:
    """Normalize page metadata to a list shape for uniform downstream handling."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def extract_chunk_text(item: Any) -> str:
    """Extract plain chunk text from a vector-store item (SDK object or dict-like)."""
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
    """Convert a raw vector-store item to the internal chunk representation."""
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
    """Normalize search results and sort chunks by descending score."""
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


def default_semantic_search(
    *,
    query: str,
    top_k: int,
    vector_store_id: str,
) -> list[dict[str, Any]]:
    """Run semantic retrieval against the configured vector store."""
    client = get_inference_client()
    search_results = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=query,
        max_num_results=top_k,
        extra_headers={"OpenAI-Project": PROJECT_ID},
    )
    return normalize_search_results(search_results)


class SemanticSearcherRunnable(Runnable):
    """Retrieval node backed by `vector_stores.search(...)`."""

    def __init__(self, semantic_search_fn: Callable[..., list[dict[str, Any]]]):
        self.semantic_search_fn = semantic_search_fn

    def invoke(self, input: dict[str, Any], config=None, **kwargs) -> dict[str, Any]:
        del config, kwargs
        rewritten_query = str(input.get("rewritten_query", "")).strip()
        base = rewritten_query or str(input.get("user_request", "")).strip()
        graph_config = input.get("graph_config") or {}
        vector_store_id = str(graph_config.get("vector_store_id", "")).strip()
        if not vector_store_id:
            raise RuntimeError(
                "vector_store_id is empty. Configure VECTOR_STORE_ID in env or pass it in request."
            )
        top_k = max(1, int(graph_config.get("top_k", 1)))
        chunks = self.semantic_search_fn(
            query=base,
            top_k=top_k,
            vector_store_id=vector_store_id,
        )
        return {
            "retrieved_chunks": chunks,
            "search_model_id": str(graph_config.get("model_id", "")),
        }
