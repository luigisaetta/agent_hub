"""
Session-state utilities for Demo1 UI.
"""

from __future__ import annotations

MESSAGES_KEY = "messages"
CONVERSATION_ID_KEY = "conversation_id"


def init_session_state(session_state) -> None:
    """Initialize session keys used by the chatbot."""
    if MESSAGES_KEY not in session_state:
        session_state[MESSAGES_KEY] = []
    if CONVERSATION_ID_KEY not in session_state:
        session_state[CONVERSATION_ID_KEY] = None


def get_messages(session_state) -> list[dict[str, str]]:
    """Return the current chat messages."""
    return session_state[MESSAGES_KEY]


def append_message(session_state, role: str, content: str) -> None:
    """Append a chat message to the local session history."""
    session_state[MESSAGES_KEY].append({"role": role, "content": content})


def get_conversation_id(session_state) -> str | None:
    """Return current remote conversation id, if any."""
    return session_state[CONVERSATION_ID_KEY]


def set_conversation_id(session_state, conversation_id: str) -> None:
    """Store the current remote conversation id."""
    session_state[CONVERSATION_ID_KEY] = conversation_id


def clear_messages(session_state) -> None:
    """Clear local message history."""
    session_state[MESSAGES_KEY] = []
