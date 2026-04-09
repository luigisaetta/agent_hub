"""
Author: L. Saetta
Last modified: 2026-04-09
License: MIT

Description:
    AnswerGenerator runnable and model streaming helpers for Demo 6 backend.
"""

# pylint: disable=redefined-builtin

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Callable

from langchain_core.runnables.base import Runnable

from common import get_inference_client
from config_private import PROJECT_ID
from demos.demo6.prompts import ANSWER_SYSTEM_PROMPT


def default_response_stream(
    *,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
) -> Iterator[Any]:
    """Open a streaming Responses API call for final answer generation."""
    client = get_inference_client()
    return client.responses.create(
        model=model_id,
        temperature=0.0,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        extra_headers={"OpenAI-Project": PROJECT_ID},
        stream=True,
    )


def iter_model_text_deltas(
    *,
    response_stream_fn: Callable[..., Iterator[Any]],
    model_id: str,
    user_prompt: str,
    system_prompt: str = ANSWER_SYSTEM_PROMPT,
) -> Iterator[str]:
    """Yield response text deltas from Responses API streaming events."""
    stream = response_stream_fn(
        model_id=model_id,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    emitted_delta = False
    for event in stream:
        event_type = getattr(event, "type", "")
        if event_type == "response.output_text.delta":
            delta = getattr(event, "delta", "")
            if delta:
                emitted_delta = True
                yield str(delta)
        elif event_type in {
            "response.output_text.done",
            "response.output_text.completed",
        }:
            # Some providers may only emit a final text chunk with no deltas.
            final_chunk = getattr(event, "text", "")
            if final_chunk and not emitted_delta:
                yield str(final_chunk)


class AnswerGeneratorRunnable(Runnable):
    """Node that builds the grounded prompt consumed by final generation."""

    def invoke(self, input: dict[str, Any], config=None, **kwargs) -> dict[str, Any]:
        del config, kwargs
        reranked = list(input.get("reranked_chunks", []))
        user_request = str(input.get("user_request", "")).strip()
        history = list(input.get("history", []))

        history_lines = [
            f"{message.get('role', 'user')}: {message.get('content', '').strip()}"
            for message in history
            if str(message.get("content", "")).strip()
        ]
        history_block = (
            "\n".join(history_lines) if history_lines else "No prior messages."
        )

        # Keep chunk formatting explicit so the model can cite only provided evidence.
        chunk_lines: list[str] = []
        for index, chunk in enumerate(reranked, start=1):
            chunk_lines.append(
                (
                    f"[{index}] filename={chunk.get('filename', 'unknown_file')} "
                    f"score={float(chunk.get('score', 0.0) or 0.0):.4f} "
                    f"chunk_id={chunk.get('chunk_id', 'N/A')}\n"
                    f"text: {chunk.get('text', '')}"
                )
            )
        chunks_block = (
            "\n\n".join(chunk_lines) if chunk_lines else "No retrieved chunks."
        )

        answer_user_prompt = (
            "User request:\n"
            f"{user_request}\n\n"
            "Conversation history:\n"
            f"{history_block}\n\n"
            "Retrieved document chunks:\n"
            f"{chunks_block}\n\n"
            "Write the final answer for the user."
        )
        return {"answer_user_prompt": answer_user_prompt}
