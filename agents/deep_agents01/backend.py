"""
Author: L. Saetta
Last modified: 2026-04-13
License: MIT

Description:
    Basic Deep Agents backend using LangChain + Deep Agents.
    The model is configured to OCI OpenAI-compatible endpoint via ChatOpenAI.
"""

# pylint: disable=too-few-public-methods,import-error

from __future__ import annotations

import os
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from uuid import uuid4

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from config import BASE_URL

_LOCAL_ENV_FILE = Path(__file__).with_name(".env.local")
load_dotenv(_LOCAL_ENV_FILE, override=False)

MODEL_ID = os.getenv("DEEP_AGENTS_MODEL", "openai.gpt-5.4").strip() or "openai.gpt-5.4"
SYSTEM_PROMPT = (
    "You are a concise and helpful assistant. "
    "Answer clearly and provide practical details when useful."
)


def _resolve_api_key() -> str:
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


def _resolve_project_id() -> str:
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


def _extract_output_text(result_state: dict[str, Any]) -> str:
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


def _summarize_runtime_error(exc: Exception) -> str:
    """Build a concise user-facing error message."""
    raw = str(exc).strip() or exc.__class__.__name__
    lower = raw.lower()
    if "not found" in lower:
        return (
            f"{raw}. Possible cause: model '{MODEL_ID}' not available on this OCI "
            "endpoint/region or unsupported Chat Completions route."
        )
    return raw


class DeepAgentsLocalBackend:
    """Wrapper around a Deep Agent graph that emits SSE-friendly events."""

    def __init__(self, graph: Any | None = None):
        self.graph = graph or self._build_deep_agent_graph()

    @staticmethod
    def _build_deep_agent_graph() -> Any:
        """Create compiled Deep Agent graph with OCI ChatOpenAI model."""
        project_id = _resolve_project_id()
        default_headers = {"OpenAI-Project": project_id} if project_id else None

        model = ChatOpenAI(
            model=MODEL_ID,
            openai_api_base=BASE_URL,
            openai_api_key=_resolve_api_key(),
            temperature=0.0,
            # important: force to responses (not completions)
            use_responses_api=True,
            output_version="responses/v1",
            default_headers=default_headers,
        )

        return create_deep_agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
        )

    async def stream_events(self, *, user_request: str) -> AsyncIterator[dict]:
        """Invoke deep agent and yield a minimal stream of execution events."""
        run_id = f"run_{uuid4().hex}"
        prompt = str(user_request).strip()

        yield build_event(
            event_type="response.started",
            run_id=run_id,
            data={"message": "Execution started"},
        )

        yield build_event(
            event_type="graph.node.started",
            run_id=run_id,
            node="DeepAgent",
            data={"status": "running"},
        )

        try:
            final_state = await self.graph.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]}
            )
            output_text = _extract_output_text(final_state)

            yield build_event(
                event_type="response.output_text.delta",
                run_id=run_id,
                node="DeepAgent",
                data={"delta": output_text},
            )

            yield build_event(
                event_type="graph.node.completed",
                run_id=run_id,
                node="DeepAgent",
                data={"status": "completed"},
            )

            yield build_event(
                event_type="response.completed",
                run_id=run_id,
                data={"output_text": output_text, "final_state": final_state},
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            message = _summarize_runtime_error(exc)
            yield build_event(
                event_type="response.error",
                run_id=run_id,
                node="DeepAgent",
                data={"message": message, "error_type": exc.__class__.__name__},
            )
            yield build_event(
                event_type="response.completed",
                run_id=run_id,
                node="DeepAgent",
                data={"output_text": "", "error": message},
            )
