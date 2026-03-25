"""
Backend logic for Demo1 chatbot.
"""

from __future__ import annotations

from collections.abc import Iterator

from common import get_inference_client
from config import MODEL_ID

DEFAULT_MODEL = MODEL_ID
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_OUTPUT_TOKENS = 4000
DEFAULT_ASSISTANT_INSTRUCTIONS = (
    "You are a helpful assistant. Reply in English unless the user explicitly asks "
    "for a different language."
)
WEB_SEARCH_TOOL = [{"type": "web_search"}]


def create_client():
    """Create the configured OpenAI-compatible client."""
    return get_inference_client()


def create_conversation(client) -> str:
    """Create a new conversation and return its id."""
    conversation = client.conversations.create(metadata={"demo": "demo1"})
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
    for event in stream:
        if event.type == "response.output_text.delta":
            emitted_delta = True
            yield event.delta
        elif event.type == "response.output_text.done" and not emitted_delta:
            final_chunk = getattr(event, "text", "")
            if final_chunk:
                yield final_chunk
