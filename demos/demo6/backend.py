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

from common import get_inference_client
from config_private import PROJECT_ID, VECTOR_STORE_ID
from demos.demo6.prompts import ANSWER_SYSTEM_PROMPT


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


def _as_dict(value: Any) -> dict[str, Any]:
    """Return value as dict when possible, otherwise return an empty dict."""
    if isinstance(value, dict):
        return value
    return {}


def _normalize_pages(value: Any) -> list[Any]:
    """Normalize page metadata to a list shape for uniform downstream handling."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def extract_chunk_text(item: Any) -> str:
    """Extract plain chunk text from a vector-store item (SDK object or dict-like)."""
    content = getattr(item, "content", None)
    if isinstance(content, list):
        text_parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and block.get("text"):
                    text_parts.append(str(block["text"]))
                continue

            if getattr(block, "type", None) == "text" and getattr(block, "text", None):
                text_parts.append(str(block.text))

        if text_parts:
            return "\n".join(text_parts).strip()

    text = getattr(item, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    return ""


def normalize_search_item(item: Any, rank: int) -> dict[str, Any]:
    """Convert a raw vector-store item to the internal chunk representation."""
    additional_properties = _as_dict(getattr(item, "additional_properties", None))
    pages = _normalize_pages(additional_properties.get("page_numbers"))
    return {
        "rank": rank,
        "score": float(getattr(item, "score", 0.0) or 0.0),
        "filename": getattr(item, "filename", None) or "unknown_file",
        "file_id": getattr(item, "file_id", None) or "",
        "chunk_id": additional_properties.get("chunk_id", "N/A"),
        "pages": pages,
        "text": extract_chunk_text(item),
        "metadata": additional_properties,
    }


def normalize_search_results(search_results: Any) -> list[dict[str, Any]]:
    """Normalize search results and sort chunks by descending score."""
    raw_items = list(getattr(search_results, "data", []) or [])
    sorted_items = sorted(
        raw_items,
        key=lambda item: getattr(item, "score", 0.0) or 0.0,
        reverse=True,
    )
    return [
        normalize_search_item(item, rank=index)
        for index, item in enumerate(sorted_items, start=1)
    ]


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


def _default_semantic_search(
    *,
    query: str,
    top_k: int,
    vector_store_id: str,
) -> list[dict[str, Any]]:
    """Run semantic retrieval against the configured vector store."""
    client = get_inference_client()
    search_results = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=query,
        max_num_results=top_k,
        extra_headers={"OpenAI-Project": PROJECT_ID},
    )
    return normalize_search_results(search_results)


def _default_response_stream(
    *,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
) -> Iterator[Any]:
    """Open a streaming Responses API call for final answer generation."""
    client = get_inference_client()
    return client.responses.create(
        model=model_id,
        temperature=0.0,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        extra_headers={"OpenAI-Project": PROJECT_ID},
        stream=True,
    )


class QueryRewriterRunnable(Runnable):
    """No-op query rewriter node (current phase keeps the request unchanged)."""

    def invoke(self, input: RagState, config=None, **kwargs) -> dict[str, Any]:
        del config, kwargs
        user_request = str(input.get("user_request", "")).strip()
        graph_config = _normalize_graph_config(input.get("graph_config"))
        return {
            "rewritten_query": user_request,
            "rewriter_model_id": graph_config["model_id"],
        }


class SemanticSearcherRunnable(Runnable):
    """Retrieval node backed by `vector_stores.search(...)`."""

    def __init__(self, semantic_search_fn: Callable[..., list[dict[str, Any]]]):
        self.semantic_search_fn = semantic_search_fn

    def invoke(self, input: RagState, config=None, **kwargs) -> dict[str, Any]:
        del config, kwargs
        rewritten_query = str(input.get("rewritten_query", "")).strip()
        base = rewritten_query or str(input.get("user_request", "")).strip()
        graph_config = _normalize_graph_config(input.get("graph_config"))
        if not graph_config["vector_store_id"]:
            raise RuntimeError(
                "vector_store_id is empty. Configure VECTOR_STORE_ID in env or pass it in request."
            )
        chunks = self.semantic_search_fn(
            query=base,
            top_k=graph_config["top_k"],
            vector_store_id=graph_config["vector_store_id"],
        )
        return {
            "retrieved_chunks": chunks,
            "search_model_id": graph_config["model_id"],
        }


class RerankerRunnable(Runnable):
    """Reranker node using score-based ordering with `top_n` truncation."""

    def invoke(self, input: RagState, config=None, **kwargs) -> dict[str, Any]:
        del config, kwargs
        retrieved = list(input.get("retrieved_chunks", []))
        graph_config = _normalize_graph_config(input.get("graph_config"))
        reranked = sorted(
            retrieved, key=lambda item: item.get("score", 0), reverse=True
        )
        return {
            "reranked_chunks": reranked[: graph_config["top_n"]],
            "reranker_model_id": graph_config["reranker_model_id"],
        }


class AnswerGeneratorRunnable(Runnable):
    """Node that builds the grounded prompt consumed by final generation."""

    def invoke(self, input: RagState, config=None, **kwargs) -> dict[str, Any]:
        del config, kwargs
        reranked = list(input.get("reranked_chunks", []))
        user_request = str(input.get("user_request", "")).strip()
        history = list(input.get("history", []))

        history_lines = [
            f"{message.get('role', 'user')}: {message.get('content', '').strip()}"
            for message in history
            if str(message.get("content", "")).strip()
        ]
        history_block = (
            "\n".join(history_lines) if history_lines else "No prior messages."
        )

        # Keep chunk formatting explicit so the model can cite only provided evidence.
        chunk_lines: list[str] = []
        for index, chunk in enumerate(reranked, start=1):
            chunk_lines.append(
                (
                    f"[{index}] filename={chunk.get('filename', 'unknown_file')} "
                    f"score={float(chunk.get('score', 0.0) or 0.0):.4f} "
                    f"chunk_id={chunk.get('chunk_id', 'N/A')}\n"
                    f"text: {chunk.get('text', '')}"
                )
            )
        chunks_block = (
            "\n\n".join(chunk_lines) if chunk_lines else "No retrieved chunks."
        )

        answer_user_prompt = (
            "User request:\n"
            f"{user_request}\n\n"
            "Conversation history:\n"
            f"{history_block}\n\n"
            "Retrieved document chunks:\n"
            f"{chunks_block}\n\n"
            "Write the final answer for the user."
        )
        return {"answer_user_prompt": answer_user_prompt}


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
        semantic_search_fn: Callable[..., list[dict[str, Any]]] | None = None,
        response_stream_fn: Callable[..., Iterator[Any]] | None = None,
    ):
        self.semantic_search_fn = semantic_search_fn or _default_semantic_search
        self.response_stream_fn = response_stream_fn or _default_response_stream

        self.query_rewriter = QueryRewriterRunnable()
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

    def _stream_answer_from_model(
        self, *, model_id: str, user_prompt: str
    ) -> Iterator[str]:
        """Yield response text deltas from Responses API streaming events."""
        stream = self.response_stream_fn(
            model_id=model_id,
            system_prompt=ANSWER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        emitted_delta = False
        for event in stream:
            event_type = getattr(event, "type", "")
            if event_type == "response.output_text.delta":
                delta = getattr(event, "delta", "")
                if delta:
                    emitted_delta = True
                    yield str(delta)
            elif event_type in {
                "response.output_text.done",
                "response.output_text.completed",
            }:
                # Some providers may only emit a final text chunk with no deltas.
                final_chunk = getattr(event, "text", "")
                if final_chunk and not emitted_delta:
                    yield str(final_chunk)

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
                    for delta in self._stream_answer_from_model(
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
