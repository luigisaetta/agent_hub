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

from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI

from agents.deep_agents01.utility import (
    build_event,
    extract_output_text,
    resolve_api_key,
    resolve_model_id,
    resolve_project_id,
    summarize_runtime_error,
)
from common import get_sampling_kwargs
from config import BASE_URL

MODEL_ID = resolve_model_id()
SYSTEM_PROMPT = (
    "You are a concise and helpful assistant. "
    "Answer clearly and provide practical details when useful."
)


class DeepAgentsLocalBackend:
    """Wrapper around a Deep Agent graph that emits SSE-friendly events."""

    def __init__(self, graph: Any | None = None):
        self.graph = graph or self._build_deep_agent_graph()

    @staticmethod
    def _build_deep_agent_graph() -> Any:
        """Create compiled Deep Agent graph with OCI ChatOpenAI model."""
        project_id = resolve_project_id()
        default_headers = {"OpenAI-Project": project_id} if project_id else None

        model = ChatOpenAI(
            model=MODEL_ID,
            openai_api_base=BASE_URL,
            openai_api_key=resolve_api_key(),
            **get_sampling_kwargs(MODEL_ID, temperature=0.0),
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
        backend_config = {
            "model": MODEL_ID,
            "openai_api_base": BASE_URL,
            "use_responses_api": True,
            "output_version": "responses/v1",
        }

        yield build_event(
            event_type="response.started",
            run_id=run_id,
            data={
                "message": "Execution started",
                "backend_config": backend_config,
            },
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
            output_text = extract_output_text(final_state)

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
            message = summarize_runtime_error(exc, model_id=MODEL_ID)
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
