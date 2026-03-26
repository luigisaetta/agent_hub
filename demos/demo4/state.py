"""
Author: L. Saetta
Last modified: 2026-03-26
License: MIT

Description:
    Session-state utilities for Demo 4 Streamlit RAG chatbot UI.
"""

from __future__ import annotations

MESSAGES_KEY = "messages"
CONVERSATION_ID_KEY = "conversation_id"
LAST_REFS_KEY = "last_references"


def init_session_state(session_state) -> None:
    """Initialize session keys used by the chatbot."""
    if MESSAGES_KEY not in session_state:
        session_state[MESSAGES_KEY] = []
    if CONVERSATION_ID_KEY not in session_state:
        session_state[CONVERSATION_ID_KEY] = None
    if LAST_REFS_KEY not in session_state:
        session_state[LAST_REFS_KEY] = []


def get_messages(session_state) -> list[dict[str, str]]:
    """Return current chat messages."""
    return session_state[MESSAGES_KEY]


def append_message(session_state, role: str, content: str) -> None:
    """Append a chat message to session history."""
    session_state[MESSAGES_KEY].append({"role": role, "content": content})


def clear_messages(session_state) -> None:
    """Clear local message history."""
    session_state[MESSAGES_KEY] = []


def get_conversation_id(session_state) -> str | None:
    """Return current remote conversation id, if any."""
    return session_state[CONVERSATION_ID_KEY]


def set_conversation_id(session_state, conversation_id: str) -> None:
    """Store current remote conversation id."""
    session_state[CONVERSATION_ID_KEY] = conversation_id


def get_last_references(session_state) -> list[dict]:
    """Return references extracted from the last assistant answer."""
    return session_state[LAST_REFS_KEY]


def set_last_references(session_state, refs: list[dict]) -> None:
    """Persist references extracted from the last assistant answer."""
    session_state[LAST_REFS_KEY] = refs
