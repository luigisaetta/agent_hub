"""
Author: L. Saetta
Last modified: 2026-04-09
License: MIT

Description:
    Reranker runnable for Demo 6 backend.
"""

# pylint: disable=redefined-builtin

from __future__ import annotations

from typing import Any

from langchain_core.runnables.base import Runnable


class RerankerRunnable(Runnable):
    """Reranker node using score-based ordering with `top_n` truncation."""

    def invoke(self, input: dict[str, Any], config=None, **kwargs) -> dict[str, Any]:
        del config, kwargs
        retrieved = list(input.get("retrieved_chunks", []))
        graph_config = input.get("graph_config") or {}
        top_n = max(1, int(graph_config.get("top_n", 1)))
        reranked = sorted(
            retrieved, key=lambda item: item.get("score", 0), reverse=True
        )
        return {
            "reranked_chunks": reranked[:top_n],
            "reranker_model_id": str(graph_config.get("reranker_model_id", "")),
        }
