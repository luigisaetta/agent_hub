"""
Author: L. Saetta
Last modified: 2026-04-08
License: MIT

Description:
    Backend logic for Demo 4 RAG chatbot using file_search on a vector store.
"""

from __future__ import annotations

from collections.abc import Iterator
import traceback

from common import (
    extract_provider_name,
    extract_text_and_refs,
    get_inference_client,
)
from demos.demo4.prompts import STRICT_INSTRUCTIONS
from config import MODEL_ID
from config_private import PROJECT_ID, VECTOR_STORE_ID

DEFAULT_MODEL = MODEL_ID
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_RESULTS = 10
DEFAULT_RERANKER = "Auto"


def create_client():
    """Create the configured OpenAI-compatible client."""
    return get_inference_client()


def create_conversation(client) -> str:
    """Create a new conversation and return its id."""
    conversation = client.conversations.create(metadata={"demo": "demo4"})
    return conversation.id


def _get_header_case_insensitive(headers, header_name: str) -> str:
    """Read one header value with case-insensitive matching."""
    if headers is None:
        return ""

    value = headers.get(header_name)
    if value:
        return str(value)

    header_name = header_name.lower()
    for key, item_value in headers.items():
        if str(key).lower() == header_name:
            return str(item_value)
    return ""


def _extract_error_details(exc: Exception) -> dict[str, str]:
    """Extract diagnostics from OpenAI-compatible errors when available."""
    # Start from generic exception attributes; enrich with HTTP response data if present.
    details: dict[str, str] = {
        "exception_type": type(exc).__name__,
        "message": str(exc),
        "status_code": str(getattr(exc, "status_code", "") or ""),
        "request_id": str(getattr(exc, "request_id", "") or ""),
        "opc_request_id": "",
        "response_body": "",
    }

    response = getattr(exc, "response", None)
    if response is None:
        # Not all failures come with an HTTP response (e.g. local/network errors).
        return details

    headers = getattr(response, "headers", None)
    details["opc_request_id"] = _get_header_case_insensitive(
        headers, "opc-request-id"
    ) or _get_header_case_insensitive(headers, "opc-requestid")

    if not details["request_id"]:
        details["request_id"] = (
            _get_header_case_insensitive(headers, "x-request-id")
            or _get_header_case_insensitive(headers, "request-id")
            or _get_header_case_insensitive(headers, "openai-request-id")
        )

    details["response_body"] = str(getattr(response, "text", "") or "")
    return details


def _log_api_error(exc: Exception, *, stage: str) -> None:
    """Print full error diagnostics to terminal logs."""
    # Centralized error logger so UI code stays small and logs are consistent.
    details = _extract_error_details(exc)
    print("")
    print("=" * 80)
    print(f"[Demo4][ERROR] stage={stage}")
    print(f"exception_type: {details['exception_type']}")
    print(f"message: {details['message']}")
    print(f"status_code: {details['status_code'] or '<n/a>'}")
    print(f"request_id: {details['request_id'] or '<n/a>'}")
    print(f"opc-request-id: {details['opc_request_id'] or '<n/a>'}")
    if details["response_body"]:
        print("response_body:")
        print(details["response_body"])
    print("traceback:")
    print(traceback.format_exc())
    print("=" * 80)
    print("")


def _build_input_for_model(model_id: str, user_prompt: str) -> list[dict[str, str]]:
    """
    Build strict input messages with provider-aware role for instructions.
    Customize instructions in prompts.py, not here.

    """
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
    enable_reranking: bool = True,
) -> tuple[Iterator[str], dict]:
    """Stream strict file_search-based RAG output and collect final refs."""
    # Mutable container shared with the caller: populated once streaming ends.
    result: dict = {"answer_text": "", "refs": []}

    # Build the file_search tool payload once; enable reranking only when requested.
    file_search_tool = {
        "type": "file_search",
        "vector_store_ids": [VECTOR_STORE_ID],
        "max_num_results": DEFAULT_MAX_RESULTS,
    }
    if enable_reranking:
        file_search_tool["ranking_options"] = {"ranker": DEFAULT_RERANKER}

    try:
        # Create a streaming Responses request and include raw file_search results
        # so references can be reconstructed after completion.
        stream = client.responses.create(
            model=model_id,
            temperature=DEFAULT_TEMPERATURE,
            input=_build_input_for_model(model_id=model_id, user_prompt=user_prompt),
            conversation=conversation_id,
            tools=[file_search_tool],
            extra_headers={"OpenAI-Project": PROJECT_ID},
            tool_choice="required",
            include=["file_search_call.results"],
            stream=True,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        _log_api_error(exc, stage="responses.create")
        raise

    def _iter_chunks() -> Iterator[str]:
        """Yield streamed output chunks and finalize answer text/references."""
        chunks: list[str] = []
        completed_response = None

        try:
            for event in stream:
                event_type = getattr(event, "type", "")
                if event_type == "response.output_text.delta":
                    # Forward text deltas immediately to the UI for real-time rendering.
                    delta = getattr(event, "delta", "")
                    if delta:
                        chunks.append(delta)
                        yield delta
                    continue

                if event_type in {"response.completed", "response.done"}:
                    # Keep final response object to extract normalized citations/references.
                    completed_response = getattr(event, "response", None)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            _log_api_error(exc, stage="responses.stream")
            raise

        streamed_text = "".join(chunks).strip()
        if completed_response is not None:
            # Prefer post-processed text with inline references when available.
            text_with_refs, refs = extract_text_and_refs(completed_response)
            if text_with_refs:
                result["answer_text"] = text_with_refs
            else:
                result["answer_text"] = streamed_text
            result["refs"] = refs
        else:
            # Fallback when stream ends without a completed response payload.
            result["answer_text"] = streamed_text
            result["refs"] = []

    return _iter_chunks(), result
