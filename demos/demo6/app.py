"""
Author: L. Saetta
Last modified: 2026-04-09
License: MIT

Description:
    Demo 6 Streamlit chat UI consuming backend SSE events from POST /chat.
"""

# pylint: disable=wrong-import-position,broad-exception-caught,import-error,too-many-arguments,too-many-statements

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import streamlit as st

# Ensure repository root is importable when Streamlit runs this file directly.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config import REGION  # noqa: E402
from demos.demo6.backend import DEFAULT_MODEL_ID, DEFAULT_VECTOR_STORE_ID  # noqa: E402

MESSAGES_KEY = "demo6_messages"
REFERENCES_KEY = "demo6_references"
BACKEND_URL_KEY = "demo6_backend_url"
MODEL_ID_KEY = "demo6_model_id"
VECTOR_STORE_ID_KEY = "demo6_vector_store_id"
REGION_KEY = "demo6_region"
DEFAULT_CHAT_URL = "http://127.0.0.1:8080/chat"
REQUEST_TIMEOUT_SECONDS = 300


def _init_session_state() -> None:
    """Initialize page session state."""
    if MESSAGES_KEY not in st.session_state:
        st.session_state[MESSAGES_KEY] = []
    if REFERENCES_KEY not in st.session_state:
        st.session_state[REFERENCES_KEY] = []
    if BACKEND_URL_KEY not in st.session_state:
        st.session_state[BACKEND_URL_KEY] = DEFAULT_CHAT_URL
    if MODEL_ID_KEY not in st.session_state:
        st.session_state[MODEL_ID_KEY] = DEFAULT_MODEL_ID
    if VECTOR_STORE_ID_KEY not in st.session_state:
        st.session_state[VECTOR_STORE_ID_KEY] = DEFAULT_VECTOR_STORE_ID
    if REGION_KEY not in st.session_state:
        st.session_state[REGION_KEY] = REGION


def _normalize_references(raw_refs: Any) -> list[dict[str, Any]]:
    """Normalize reranker references to a stable list for UI rendering."""
    normalized: list[dict[str, Any]] = []
    for item in list(raw_refs or []):
        if not isinstance(item, dict):
            continue
        pages = item.get("pages", [])
        if not isinstance(pages, list):
            pages = [pages]
        normalized.append(
            {
                "filename": str(item.get("filename", "unknown_file")),
                "pages": pages,
            }
        )
    return normalized


def _render_references_sidebar(
    references_container: Any, references: list[dict[str, Any]]
) -> None:
    """Render collapsible reranker references in the sidebar."""
    references_container.empty()
    with references_container.container():
        st.subheader("References")
        if not references:
            st.caption("No references yet.")
            return

        for index, item in enumerate(references, start=1):
            title = f"[{index}] {item['filename']}"
            with st.expander(title, expanded=index == 1):
                st.write(f"Pages: {item['pages'] or 'N/A'}")


def _render_sidebar() -> tuple[dict[str, str], Any]:
    """Render sidebar settings used for backend calls."""
    with st.sidebar:
        st.subheader("Runtime Configuration")
        backend_url = st.text_input("Backend /chat URL", key=BACKEND_URL_KEY)
        st.text_input("region", key=REGION_KEY, disabled=True)
        model_id = st.text_input("model_id", key=MODEL_ID_KEY)
        vector_store_id = st.text_input("vector_store_id", key=VECTOR_STORE_ID_KEY)

        if st.button("New Conversation"):
            st.session_state[MESSAGES_KEY] = []
            st.session_state[REFERENCES_KEY] = []
            st.rerun()

        st.divider()
        references_container = st.empty()
        _render_references_sidebar(
            references_container,
            _normalize_references(st.session_state[REFERENCES_KEY]),
        )

    return (
        {
            "backend_url": backend_url.strip(),
            "model_id": model_id.strip(),
            "vector_store_id": vector_store_id.strip(),
        },
        references_container,
    )


def _stream_chat_response(
    *,
    backend_url: str,
    user_request: str,
    history: list[dict[str, str]],
    model_id: str,
    vector_store_id: str,
    answer_placeholder: Any,
    references_container: Any,
) -> str:
    """Call backend SSE endpoint and stream assistant answer to UI."""
    payload = {
        "user_request": user_request,
        "history": history,
        "model_id": model_id,
        "vector_store_id": vector_store_id,
    }
    request = urllib.request.Request(
        backend_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    answer_parts: list[str] = []
    final_answer = ""
    current_event_type = "message"
    data_lines: list[str] = []

    def _process_event(event_type: str, raw_data_lines: list[str]) -> str:
        """Process one complete SSE event and return optional final text."""
        if not raw_data_lines:
            return ""
        raw_json = "\n".join(raw_data_lines).strip()
        if not raw_json:
            return ""

        event = json.loads(raw_json)
        event_data = event.get("data", {})

        if event_type == "response.output_text.delta":
            delta = str(event_data.get("delta", ""))
            if delta:
                answer_parts.append(delta)
                answer_placeholder.markdown("".join(answer_parts))
            return ""

        if event_type == "response.output_text.completed":
            completed_text = str(event_data.get("text", "")).strip()
            return completed_text

        if event_type == "graph.state.delta" and event.get("node") == "Reranker":
            reranked_chunks = _normalize_references(
                event_data.get("delta", {}).get("reranked_chunks", [])
            )
            st.session_state[REFERENCES_KEY] = reranked_chunks
            _render_references_sidebar(references_container, reranked_chunks)
            return ""

        if event_type == "response.completed":
            final_refs = _normalize_references(
                event_data.get("final_state", {}).get("reranked_chunks", [])
            )
            if final_refs:
                st.session_state[REFERENCES_KEY] = final_refs
                _render_references_sidebar(references_container, final_refs)
            output_text = str(event_data.get("output_text", "")).strip()
            return output_text

        if event_type == "response.error":
            message = str(event_data.get("message", "Unknown backend error"))
            raise RuntimeError(message)

        return ""

    try:
        with urllib.request.urlopen(  # nosec B310
            request, timeout=REQUEST_TIMEOUT_SECONDS
        ) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").rstrip("\n").rstrip("\r")
                if not line:
                    processed = _process_event(current_event_type, data_lines)
                    if processed:
                        final_answer = processed
                    current_event_type = "message"
                    data_lines = []
                    continue

                if line.startswith("event:"):
                    current_event_type = line[6:].strip() or "message"
                    continue
                if line.startswith("data:"):
                    data_lines.append(line[5:].strip())

        if data_lines:
            processed = _process_event(current_event_type, data_lines)
            if processed:
                final_answer = processed
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cannot reach backend: {exc.reason}") from exc

    if not final_answer:
        final_answer = "".join(answer_parts).strip()
    if not final_answer:
        final_answer = "I could not generate a text answer."
    answer_placeholder.markdown(final_answer)
    return final_answer


def main() -> None:
    """Render chat UI and stream assistant responses from demo6 backend."""
    st.set_page_config(page_title="Demo6 - SSE Chat UI", page_icon="Chat")
    st.title("Demo6: Chat UI (Streamlit + SSE)")

    _init_session_state()
    runtime, references_container = _render_sidebar()

    messages: list[dict[str, str]] = st.session_state[MESSAGES_KEY]
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Ask a question...")
    if not user_prompt:
        return

    history = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
    user_message = {"role": "user", "content": user_prompt}
    st.session_state[MESSAGES_KEY].append(user_message)

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        answer_placeholder = st.empty()
        st.session_state[REFERENCES_KEY] = []
        _render_references_sidebar(references_container, [])
        try:
            final_answer = _stream_chat_response(
                backend_url=runtime["backend_url"],
                user_request=user_prompt,
                history=history,
                model_id=runtime["model_id"],
                vector_store_id=runtime["vector_store_id"],
                answer_placeholder=answer_placeholder,
                references_container=references_container,
            )
        except Exception as exc:
            answer_placeholder.empty()
            st.error(f"Request failed: {exc}")
            st.session_state[MESSAGES_KEY].pop()
            return

    st.session_state[MESSAGES_KEY].append(
        {"role": "assistant", "content": final_answer}
    )


if __name__ == "__main__":
    main()
