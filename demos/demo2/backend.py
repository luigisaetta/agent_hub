"""
Author: L. Saetta
Last modified: 2026-03-22
License: MIT

Description:
    Backend logic for Demo2 chatbot with Langfuse tracing enabled.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

from langfuse import get_client
from langfuse.openai import openai

from config import BASE_URL, LANGFUSE_BASE_URL, MODEL_ID
from config_private import KEY1, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, PROJECT_ID

DEFAULT_MODEL = MODEL_ID
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_OUTPUT_TOKENS = 4000
DEFAULT_ASSISTANT_INSTRUCTIONS = (
    "You are a helpful assistant. Reply in English unless the user explicitly asks "
    "for a different language."
)
WEB_SEARCH_TOOL = [{"type": "web_search"}]


def create_client():
    """Create an OpenAI-compatible client instrumented by Langfuse."""
    os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_HOST"] = LANGFUSE_BASE_URL

    return openai.OpenAI(
        base_url=BASE_URL,
        api_key=KEY1,
        project=PROJECT_ID,
    )


def create_conversation(client) -> str:
    """Create a new conversation and return its id."""
    conversation = client.conversations.create(metadata={"demo": "demo2"})
    return conversation.id


def stream_response_text(
    client,
    *,
    model_id: str,
    user_prompt: str,
    conversation_id: str,
) -> Iterator[str]:
    """Yield streamed text chunks from a model response."""
    stream = client.responses.create(
        model=model_id,
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
        instructions=DEFAULT_ASSISTANT_INSTRUCTIONS,
        input=user_prompt,
        conversation=conversation_id,
        tools=WEB_SEARCH_TOOL,
        stream=True,
    )

    emitted_delta = False
    try:
        for event in stream:
            if event.type == "response.output_text.delta":
                emitted_delta = True
                yield event.delta
            elif event.type == "response.output_text.done" and not emitted_delta:
                final_chunk = getattr(event, "text", "")
                if final_chunk:
                    yield final_chunk
    finally:
        get_client().flush()
