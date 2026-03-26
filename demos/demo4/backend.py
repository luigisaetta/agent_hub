"""
Author: L. Saetta
Last modified: 2026-03-26
License: MIT

Description:
    Backend logic for Demo 4 RAG chatbot using file_search on a vector store.
"""

from __future__ import annotations

from collections.abc import Iterator

from common import (
    extract_provider_name,
    extract_text_and_refs,
    get_inference_client,
)
from config import MODEL_ID
from config_private import PROJECT_ID, VECTOR_STORE_ID

DEFAULT_MODEL = MODEL_ID
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_RESULTS = 10

STRICT_INSTRUCTIONS = (
    "Answer using only information from the retrieved documents. "
    "You may summarize or synthesize information that is explicitly "
    "supported by the retrieved text. "
    "Do not use outside knowledge. "
    "If the retrieved documents do not contain enough information to answer, say exactly: "
    "'I don't have sufficient information in the documents.'"
)


def create_client():
    """Create the configured OpenAI-compatible client."""
    return get_inference_client()


def create_conversation(client) -> str:
    """Create a new conversation and return its id."""
    conversation = client.conversations.create(metadata={"demo": "demo4"})
    return conversation.id


def _build_input_for_model(model_id: str, user_prompt: str) -> list[dict[str, str]]:
    """Build strict input messages with provider-aware role for instructions."""
    role_instructions = "system"
    if extract_provider_name(model_id) == "google":
        # Gemini variants may reject system-role instructions in this runtime.
        role_instructions = "user"

    return [
        {"role": role_instructions, "content": STRICT_INSTRUCTIONS},
        {"role": "user", "content": user_prompt},
    ]


def stream_rag(
    client,
    *,
    model_id: str,
    user_prompt: str,
    conversation_id: str,
) -> tuple[Iterator[str], dict]:
    """Stream strict file_search-based RAG output and collect final refs."""
    result: dict = {"answer_text": "", "refs": []}

    stream = client.responses.create(
        model=model_id,
        temperature=DEFAULT_TEMPERATURE,
        input=_build_input_for_model(model_id=model_id, user_prompt=user_prompt),
        conversation=conversation_id,
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [VECTOR_STORE_ID],
                "max_num_results": DEFAULT_MAX_RESULTS,
            }
        ],
        extra_headers={"OpenAI-Project": PROJECT_ID},
        tool_choice="required",
        include=["file_search_call.results"],
        stream=True,
    )

    def _iter_chunks() -> Iterator[str]:
        """Yield streamed output chunks and finalize answer text/references."""
        chunks: list[str] = []
        completed_response = None

        for event in stream:
            event_type = getattr(event, "type", "")
            if event_type == "response.output_text.delta":
                delta = getattr(event, "delta", "")
                if delta:
                    chunks.append(delta)
                    yield delta
                continue

            if event_type in {"response.completed", "response.done"}:
                completed_response = getattr(event, "response", None)

        streamed_text = "".join(chunks).strip()
        if completed_response is not None:
            text_with_refs, refs = extract_text_and_refs(completed_response)
            if text_with_refs:
                result["answer_text"] = text_with_refs
            else:
                result["answer_text"] = streamed_text
            result["refs"] = refs
        else:
            result["answer_text"] = streamed_text
            result["refs"] = []

    return _iter_chunks(), result
