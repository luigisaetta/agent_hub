"""
Author: L. Saetta
Last modified: 2026-03-26
License: MIT

Description:
    Demo 4 Streamlit chatbot with strict RAG via file_search and sidebar references.
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

from demos.demo4.backend import DEFAULT_MODEL, ask_rag, create_client, create_conversation
from demos.demo4.state import (
    append_message,
    clear_messages,
    get_conversation_id,
    get_last_references,
    get_messages,
    init_session_state,
    set_conversation_id,
    set_last_references,
)
from config_private import VECTOR_STORE_ID


def _render_sidebar() -> str:
    """Render sidebar controls and return selected model id."""
    with st.sidebar:
        st.subheader("Settings")
        model_id = st.text_input("Model ID", value=DEFAULT_MODEL)
        st.caption(f"Vector Store ID: `{VECTOR_STORE_ID or 'MISSING'}`")

        if st.button("New Conversation"):
            clear_messages(st.session_state)
            set_last_references(st.session_state, [])
            set_conversation_id(st.session_state, create_conversation(create_client()))
            st.rerun()

        st.divider()
        st.subheader("References")
        refs = get_last_references(st.session_state)
        if not refs:
            st.caption("No references yet.")
        else:
            for ref in refs:
                st.markdown(f"[{ref['n']}] {ref['filename']} (pages={ref['pages']})")

    return model_id


def main() -> None:
    """Render chatbot UI and run strict RAG chat loop."""
    st.set_page_config(page_title="Demo4 - RAG File Search", page_icon="Book")
    st.title("Demo4: Strict RAG with file_search")

    if not VECTOR_STORE_ID:
        st.error("VECTOR_STORE_ID is empty for the active profile.")
        st.info("Set VECTOR_STORE_ID in the selected .env profile.")
        return

    client = create_client()
    init_session_state(st.session_state)

    if not get_conversation_id(st.session_state):
        set_conversation_id(st.session_state, create_conversation(client))

    model_id = _render_sidebar()

    for msg in get_messages(st.session_state):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_prompt = st.chat_input("Ask a question about your indexed documents...")
    if not user_prompt:
        return

    append_message(st.session_state, "user", user_prompt)
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching documents and preparing strict answer..."):
            answer_text, refs = ask_rag(
                client,
                model_id=model_id,
                user_prompt=user_prompt,
                conversation_id=get_conversation_id(st.session_state),
            )

        answer_text = (answer_text or "").strip() or "I could not generate a text answer."
        st.markdown(answer_text)

    append_message(st.session_state, "assistant", answer_text)
    set_last_references(st.session_state, refs)
    st.rerun()


if __name__ == "__main__":
    main()
