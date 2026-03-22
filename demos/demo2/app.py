"""
Author: L. Saetta
Last modified: 2026-03-22
License: MIT

Description:
    Demo 2 - Streamlit chatbot using Responses API + web search tool
    with Langfuse tracing.
"""

# pylint: disable=wrong-import-position

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure repository root is importable when Streamlit runs this file directly.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from demos.demo2.backend import (
    DEFAULT_MODEL,
    create_client,
    create_conversation,
    stream_response_text,
)
from demos.demo2.state import (
    append_message,
    clear_messages,
    get_conversation_id,
    get_messages,
    init_session_state,
    set_conversation_id,
)


def main() -> None:
    """Render chatbot UI and run chat loop."""
    st.set_page_config(page_title="Demo2 - Responses Chatbot", page_icon="Chat")
    st.title("Demo2: Responses API + Web Search + Langfuse")

    client = create_client()
    init_session_state(st.session_state)
    if not get_conversation_id(st.session_state):
        set_conversation_id(st.session_state, create_conversation(client))

    with st.sidebar:
        st.subheader("Settings")
        model_id = st.text_input("Model ID", value=DEFAULT_MODEL)
        if st.button("New Conversation"):
            clear_messages(st.session_state)
            set_conversation_id(st.session_state, create_conversation(client))
            st.rerun()

        st.caption(f"Conversation ID: `{get_conversation_id(st.session_state)}`")

    for msg in get_messages(st.session_state):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_prompt = st.chat_input("Ask a question...")
    if not user_prompt:
        return

    append_message(st.session_state, "user", user_prompt)
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        answer_chunks: list[str] = []

        with st.spinner("Searching the web and preparing the answer..."):
            for chunk in stream_response_text(
                client,
                model_id=model_id,
                user_prompt=user_prompt,
                conversation_id=get_conversation_id(st.session_state),
            ):
                answer_chunks.append(chunk)
                placeholder.markdown("".join(answer_chunks))

        answer_text = "".join(answer_chunks).strip()
        if not answer_text:
            answer_text = "I could not generate a text answer."
        placeholder.markdown(answer_text)

    append_message(st.session_state, "assistant", answer_text)


if __name__ == "__main__":
    main()
