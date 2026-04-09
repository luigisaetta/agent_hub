"""
Author: L. Saetta
Last modified: 2026-04-09
License: MIT

Description:
    QueryRewriter runnable for Demo 6 backend.
"""

# pylint: disable=redefined-builtin

from __future__ import annotations

from typing import Any, Callable

from langchain_core.runnables.base import Runnable

from common import get_inference_client
from config_private import PROJECT_ID
from demos.demo6.prompts import QUERY_REWRITER_SYSTEM_PROMPT


def _extract_output_text(response: Any) -> str:
    """Extract output text from a Responses API object with fallbacks."""
    output_text = (getattr(response, "output_text", "") or "").strip()
    if output_text:
        return output_text

    fragments: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            if getattr(content, "type", "") == "output_text":
                text = getattr(content, "text", "")
                if text:
                    fragments.append(str(text))
    return "\n".join(fragments).strip()


def _history_block(history: list[dict[str, str]]) -> str:
    """Serialize conversation history for the rewriter prompt."""
    lines = [
        f"{message.get('role', 'user')}: {str(message.get('content', '')).strip()}"
        for message in history
        if str(message.get("content", "")).strip()
    ]
    return "\n".join(lines) if lines else "No prior messages."


def default_query_rewrite(
    *,
    model_id: str,
    user_request: str,
    history: list[dict[str, str]],
) -> str:
    """Rewrite query via Responses API into a standalone query."""
    client = get_inference_client()
    
    user_prompt = (
        "Conversation history:\n"
        f"{_history_block(history)}\n\n"
        "Latest user request:\n"
        f"{user_request}\n\n"
        "Rewrite the latest user request as a standalone query."
    )
    
    response = client.responses.create(
        model=model_id,
        temperature=0.0,
        input=[
            {"role": "system", "content": QUERY_REWRITER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        extra_headers={"OpenAI-Project": PROJECT_ID},
        stream=False,
    )
    return _extract_output_text(response).strip()


class QueryRewriterRunnable(Runnable):
    """Rewrite follow-up queries into standalone ones when history exists."""

    def __init__(self, query_rewrite_fn: Callable[..., str]):
        self.query_rewrite_fn = query_rewrite_fn

    def invoke(self, input: dict[str, Any], config=None, **kwargs) -> dict[str, Any]:
        del config, kwargs
        user_request = str(input.get("user_request", "")).strip()
        graph_config = input.get("graph_config") or {}
        history = list(input.get("history", []))

        if not history:
            return {
                "rewritten_query": user_request,
                "rewriter_model_id": str(graph_config.get("model_id", "")),
            }

        rewritten_query = str(
            self.query_rewrite_fn(
                model_id=str(graph_config.get("model_id", "")),
                user_request=user_request,
                history=history,
            )
            or ""
        ).strip()
        if not rewritten_query:
            rewritten_query = user_request
        return {
            "rewritten_query": rewritten_query,
            "rewriter_model_id": str(graph_config.get("model_id", "")),
        }
