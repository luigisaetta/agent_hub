"""
Author: L. Saetta
Last modified: 2026-04-13
License: MIT

Description:
    Utility helpers for deep_agents01 backend:
    environment loading, secret resolution, event envelope,
    output extraction, and runtime error summarization.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

_LOCAL_ENV_FILE = Path(__file__).with_name(".env.local")
load_dotenv(_LOCAL_ENV_FILE, override=False)


def resolve_model_id() -> str:
    """Resolve model id from environment with default fallback."""
    return os.getenv("DEEP_AGENTS_MODEL", "openai.gpt-5.4").strip() or "openai.gpt-5.4"


def resolve_api_key() -> str:
    """Resolve API key from environment/local env file."""
    env_value = (
        os.getenv("OPENAI_API_KEY") or os.getenv("OCI_GENAI_API_KEY") or ""
    ).strip()
    if env_value:
        return env_value
    raise ValueError(
        "Missing API key. Set OPENAI_API_KEY (or OCI_GENAI_API_KEY) in "
        "agents/deep_agents01/.env.local."
    )


def resolve_project_id() -> str:
    """Resolve OpenAI project id from environment/local env file."""
    env_value = (
        os.getenv("OPENAI_PROJECT_ID") or os.getenv("OCI_PROJECT_ID") or ""
    ).strip()
    if env_value:
        return env_value
    raise ValueError(
        "Missing project id. Set OPENAI_PROJECT_ID (or OCI_PROJECT_ID) in "
        "agents/deep_agents01/.env.local."
    )


def build_event(*, event_type: str, run_id: str, data: dict, node: str | None = None):
    """Build a standardized event envelope."""
    return {
        "id": f"evt_{uuid4().hex}",
        "type": event_type,
        "timestamp": int(time.time()),
        "run_id": run_id,
        "node": node,
        "data": data,
    }


def _extract_text_from_content(content: Any) -> str:
    """Extract plain text from LangChain/OpenAI-like message content."""
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                value = block.strip()
                if value:
                    text_parts.append(value)
                continue
            if isinstance(block, dict):
                # Common response formats use keys like text/content.
                for key in ("text", "content"):
                    raw_value = block.get(key)
                    if isinstance(raw_value, str) and raw_value.strip():
                        text_parts.append(raw_value.strip())
                        break
        return "\n".join(text_parts).strip()

    return str(content).strip()


def extract_output_text(result_state: dict[str, Any]) -> str:
    """Get final assistant text from state returned by deep agent invoke."""
    messages = result_state.get("messages")
    if isinstance(messages, list):
        for message in reversed(messages):
            role = ""
            content: Any = ""

            if isinstance(message, dict):
                role = str(message.get("role", "")).lower()
                content = message.get("content", "")
            else:
                role = str(getattr(message, "type", "")).lower()
                content = getattr(message, "content", "")

            if role in {"assistant", "ai"}:
                text = _extract_text_from_content(content)
                if text:
                    return text

    return "No textual response generated."


def summarize_runtime_error(exc: Exception, *, model_id: str) -> str:
    """Build a concise user-facing error message."""
    raw = str(exc).strip() or exc.__class__.__name__
    lower = raw.lower()
    if "not found" in lower:
        return (
            f"{raw}. Possible cause: model '{model_id}' not available on this OCI "
            "endpoint/region or unsupported Chat Completions route."
        )
    return raw
