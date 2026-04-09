"""
Author: L. Saetta
Last modified: 2026-04-09
License: MIT

Description:
    QueryRewriter runnable for Demo 6 backend.
"""

# pylint: disable=redefined-builtin

from __future__ import annotations

from typing import Any

from langchain_core.runnables.base import Runnable


class QueryRewriterRunnable(Runnable):
    """No-op query rewriter node (current phase keeps the request unchanged)."""

    def invoke(self, input: dict[str, Any], config=None, **kwargs) -> dict[str, Any]:
        del config, kwargs
        user_request = str(input.get("user_request", "")).strip()
        graph_config = input.get("graph_config") or {}
        return {
            "rewritten_query": user_request,
            "rewriter_model_id": str(graph_config.get("model_id", "")),
        }
