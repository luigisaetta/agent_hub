"""
Author: L. Saetta
Last modified: 2026-04-10
License: MIT

Description:
    Minimal Hello World agent backend built with LangGraph.
    It receives a name and emits deterministic execution events.
"""

# pylint: disable=too-few-public-methods

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph


class HelloState(TypedDict, total=False):
    """Mutable state shared across graph execution."""

    name: str
    greeting: str


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


class HelloWorldAgent:
    """Small LangGraph-powered agent answering with a hello message."""

    def __init__(self):
        self.graph = self._build_langgraph()

    @staticmethod
    def _hello_node(state: HelloState) -> HelloState:
        """Create greeting from provided input name."""
        name = str(state.get("name", "")).strip() or "world"
        return {"name": name, "greeting": f"Hello, {name}!"}

    def _build_langgraph(self):
        """Build and compile the fixed execution graph for hello agent."""
        workflow = StateGraph(HelloState)
        workflow.add_node("HelloNode", self._hello_node)
        workflow.add_edge(START, "HelloNode")
        workflow.add_edge("HelloNode", END)
        return workflow.compile()

    async def stream_events(self, *, name: str) -> AsyncIterator[dict]:
        """Execute one run and emit simple SSE-friendly events."""
        run_id = f"run_{uuid4().hex}"
        normalized_name = str(name).strip() or "world"

        yield build_event(
            event_type="response.started",
            run_id=run_id,
            data={"message": "Execution started"},
        )

        yield build_event(
            event_type="graph.node.started",
            run_id=run_id,
            node="HelloNode",
            data={"status": "running"},
        )

        final_state: HelloState = await self.graph.ainvoke({"name": normalized_name})
        greeting = str(final_state.get("greeting", "Hello, world!"))

        yield build_event(
            event_type="graph.state.delta",
            run_id=run_id,
            node="HelloNode",
            data={"delta": {"greeting": greeting}},
        )

        yield build_event(
            event_type="response.output_text.delta",
            run_id=run_id,
            node="HelloNode",
            data={"delta": greeting},
        )

        yield build_event(
            event_type="graph.node.completed",
            run_id=run_id,
            node="HelloNode",
            data={"status": "completed"},
        )

        yield build_event(
            event_type="response.completed",
            run_id=run_id,
            data={"output_text": greeting, "final_state": final_state},
        )
