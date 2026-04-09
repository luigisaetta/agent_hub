"""
Author: L. Saetta
Last modified: 2026-04-08
License: MIT

Description:
    Demo 6 backend core.
    It orchestrates a LangGraph-style RAG pipeline and emits standardized
    execution events for SSE transport to the UI layer.
"""

# pylint: disable=too-few-public-methods,broad-exception-caught,too-many-instance-attributes,redefined-builtin

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from typing import Any, AsyncIterator, Callable, TypedDict
from uuid import uuid4

from langchain_core.runnables.base import Runnable
from langgraph.graph import END, START, StateGraph

from config_private import VECTOR_STORE_ID
from demos.demo6.nodes import (
    AnswerGeneratorRunnable,
    QueryRewriterRunnable,
    RerankerRunnable,
    SemanticSearcherRunnable,
    default_query_rewrite,
    default_response_stream,
    default_semantic_search,
    iter_model_text_deltas,
)


class RagState(TypedDict, total=False):
    """Mutable state shared across graph nodes during one run."""

    user_request: str
    history: list[dict[str, str]]
    rewritten_query: str
    retrieved_chunks: list[dict[str, Any]]
    reranked_chunks: list[dict[str, Any]]
    answer_user_prompt: str
    answer: str
    graph_config: GraphRunConfig


class GraphRunConfig(TypedDict, total=False):
    """Runtime overrides controlling model choices and retrieval sizes."""

    model_id: str
    reranker_model_id: str
    top_k: int
    top_n: int
    vector_store_id: str


DEFAULT_MODEL_ID = "openai.gpt-5.4"
DEFAULT_RERANKER_MODEL_ID = "openai.gpt-5.4"
DEFAULT_TOP_K = 10
DEFAULT_TOP_N = 8
DEFAULT_VECTOR_STORE_ID = VECTOR_STORE_ID or ""
DEFAULT_MAX_HISTORY_MESSAGES = 20

# Keep logging local to this module so backend runs show node lifecycle clearly.
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    LOGGER.addHandler(handler)
LOGGER.propagate = False


def default_graph_config() -> GraphRunConfig:
    """Return the baseline graph configuration used when request has no overrides."""
    return {
        "model_id": DEFAULT_MODEL_ID,
        "reranker_model_id": DEFAULT_RERANKER_MODEL_ID,
        "top_k": DEFAULT_TOP_K,
        "top_n": DEFAULT_TOP_N,
        "vector_store_id": DEFAULT_VECTOR_STORE_ID,
    }


def _normalize_graph_config(config: GraphRunConfig | None) -> GraphRunConfig:
    """Merge user overrides with defaults and enforce safe/consistent values."""
    merged = default_graph_config()
    if config:
        merged.update(config)

    merged["top_k"] = max(1, int(merged["top_k"]))
    merged["top_n"] = max(1, int(merged["top_n"]))
    merged["vector_store_id"] = str(merged.get("vector_store_id", "")).strip()
    return merged


def _chunks_for_ui(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reduce chunk payload to UI-safe fields (filename + pages only)."""
    reduced: list[dict[str, Any]] = []
    for chunk in chunks:
        reduced.append(
            {
                "filename": str(chunk.get("filename", "unknown_file")),
                "pages": list(chunk.get("pages", [])),
            }
        )
    return reduced


def _final_state_for_ui(state: RagState) -> dict[str, Any]:
    """Build a final state snapshot safe to expose to the frontend."""
    return {
        "user_request": state.get("user_request", ""),
        "graph_config": state.get("graph_config", {}),
        "retrieved_chunks": _chunks_for_ui(list(state.get("retrieved_chunks", []))),
        "reranked_chunks": _chunks_for_ui(list(state.get("reranked_chunks", []))),
        "answer": state.get("answer", ""),
    }


def build_event(
    *,
    event_type: str,
    run_id: str,
    data: dict[str, Any],
    node: str | None = None,
) -> dict[str, Any]:
    """Build a standardized event envelope."""
    return {
        "id": f"evt_{uuid4().hex}",
        "type": event_type,
        "timestamp": int(time.time()),
        "run_id": run_id,
        "node": node,
        "data": data,
    }


class Demo6RagAgent:
    """RAG orchestrator exposing an async stream of UI-oriented execution events."""

    def __init__(
        self,
        *,
        query_rewrite_fn: Callable[..., str] | None = None,
        semantic_search_fn: Callable[..., list[dict[str, Any]]] | None = None,
        response_stream_fn: Callable[..., Iterator[Any]] | None = None,
    ):
        self.query_rewrite_fn = query_rewrite_fn or default_query_rewrite
        self.semantic_search_fn = semantic_search_fn or default_semantic_search
        self.response_stream_fn = response_stream_fn or default_response_stream

        self.query_rewriter = QueryRewriterRunnable(self.query_rewrite_fn)
        self.semantic_searcher = SemanticSearcherRunnable(self.semantic_search_fn)
        self.reranker = RerankerRunnable()
        self.answer_generator = AnswerGeneratorRunnable()

        self.node_sequence: list[tuple[str, Runnable]] = [
            ("QueryRewriter", self.query_rewriter),
            ("SemanticSearcher", self.semantic_searcher),
            ("Reranker", self.reranker),
            ("AnswerGenerator", self.answer_generator),
        ]
        self.graph = self._build_langgraph()

    def _build_langgraph(self):
        """Build and compile the fixed execution graph used by this demo."""
        workflow = StateGraph(RagState)
        workflow.add_node("QueryRewriter", self.query_rewriter)
        workflow.add_node("SemanticSearcher", self.semantic_searcher)
        workflow.add_node("Reranker", self.reranker)
        workflow.add_node("AnswerGenerator", self.answer_generator)

        workflow.add_edge(START, "QueryRewriter")
        workflow.add_edge("QueryRewriter", "SemanticSearcher")
        workflow.add_edge("SemanticSearcher", "Reranker")
        workflow.add_edge("Reranker", "AnswerGenerator")
        workflow.add_edge("AnswerGenerator", END)
        return workflow.compile()

    async def stream_events(
        self,
        *,
        user_request: str,
        history: list[dict[str, str]] | None = None,
        graph_config: GraphRunConfig | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute one agent run and emit standardized events in logical order."""
        run_id = f"run_{uuid4().hex}"
        effective_config = _normalize_graph_config(graph_config)
        # Keep only the latest history turns to cap prompt size and token usage.
        trimmed_history = list(history or [])[-DEFAULT_MAX_HISTORY_MESSAGES:]
        state: RagState = {
            "user_request": user_request,
            "history": trimmed_history,
            "graph_config": effective_config,
        }

        yield build_event(
            event_type="response.started",
            run_id=run_id,
            data={
                "message": "Execution started",
                "graph_config": effective_config,
            },
        )

        try:
            for node_name, runnable in self.node_sequence:
                LOGGER.info("run_id=%s node=%s status=started", run_id, node_name)
                yield build_event(
                    event_type="graph.node.started",
                    run_id=run_id,
                    node=node_name,
                    data={"status": "running"},
                )

                if node_name == "SemanticSearcher":
                    yield build_event(
                        event_type="response.tool_call.started",
                        run_id=run_id,
                        node=node_name,
                        data={
                            "tool_name": "semantic_search",
                            "model_id": effective_config["model_id"],
                            "top_k": effective_config["top_k"],
                        },
                    )

                node_delta = await runnable.ainvoke(state)
                state.update(node_delta)

                # Event payloads are intentionally reduced for UI/debug usage.
                yield build_event(
                    event_type="graph.state.delta",
                    run_id=run_id,
                    node=node_name,
                    data=(
                        {"chunks": _chunks_for_ui(node_delta["retrieved_chunks"])}
                        if node_name == "SemanticSearcher"
                        else (
                            {
                                "delta": {
                                    "reranked_chunks": _chunks_for_ui(
                                        node_delta["reranked_chunks"]
                                    ),
                                    "reranker_model_id": node_delta.get(
                                        "reranker_model_id", ""
                                    ),
                                }
                            }
                            if node_name == "Reranker"
                            else (
                                {"delta": {"prompt_ready": True}}
                                if node_name == "AnswerGenerator"
                                else {"delta": node_delta}
                            )
                        )
                    ),
                )

                if node_name == "AnswerGenerator":
                    user_prompt = str(state.get("answer_user_prompt", ""))
                    streamed_text = ""
                    # Forward model deltas directly as incremental UI output.
                    for delta in iter_model_text_deltas(
                        response_stream_fn=self.response_stream_fn,
                        model_id=effective_config["model_id"],
                        user_prompt=user_prompt,
                    ):
                        streamed_text += delta
                        yield build_event(
                            event_type="response.output_text.delta",
                            run_id=run_id,
                            node=node_name,
                            data={"delta": delta},
                        )

                    state["answer"] = streamed_text.strip()
                    yield build_event(
                        event_type="graph.state.delta",
                        run_id=run_id,
                        node=node_name,
                        data={"delta": {"answer": state["answer"]}},
                    )

                    yield build_event(
                        event_type="response.output_text.completed",
                        run_id=run_id,
                        node=node_name,
                        data={"text": state["answer"]},
                    )

                if node_name == "SemanticSearcher":
                    documents = len(state.get("retrieved_chunks", []))
                    yield build_event(
                        event_type="response.tool_call.completed",
                        run_id=run_id,
                        node=node_name,
                        data={
                            "tool_name": "semantic_search",
                            "documents": documents,
                            "top_k": effective_config["top_k"],
                        },
                    )

                yield build_event(
                    event_type="graph.node.completed",
                    run_id=run_id,
                    node=node_name,
                    data={"status": "completed"},
                )
                LOGGER.info("run_id=%s node=%s status=completed", run_id, node_name)

            yield build_event(
                event_type="response.completed",
                run_id=run_id,
                data={
                    "message": "Execution completed",
                    "output_text": state.get("answer", ""),
                    "final_state": _final_state_for_ui(state),
                },
            )
        except Exception as exc:
            # Keep one stable error event type for the UI, regardless of source.
            yield build_event(
                event_type="response.error",
                run_id=run_id,
                data={"message": str(exc)},
            )
