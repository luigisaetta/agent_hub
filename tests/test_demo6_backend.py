"""
Author: L. Saetta
Last modified: 2026-04-08
License: MIT

Description:
    Tests for Demo 6 backend event model and streaming flow.
"""

# pylint: disable=import-error

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from demos.demo6.backend import (
    DEFAULT_MODEL_ID,
    DEFAULT_RERANKER_MODEL_ID,
    DEFAULT_TOP_K,
    DEFAULT_TOP_N,
    Demo6RagAgent,
    build_event,
)


def _fake_semantic_search(*, query: str, top_k: int, vector_store_id: str):
    """Deterministic semantic search stub for tests."""
    return [
        {
            "rank": 1,
            "score": 0.9,
            "filename": "doc1.pdf",
            "file_id": "f1",
            "chunk_id": "c1",
            "pages": [1],
            "text": f"chunk for {query}",
            "metadata": {"source": vector_store_id, "requested_top_k": top_k},
        },
        {
            "rank": 2,
            "score": 0.8,
            "filename": "doc2.pdf",
            "file_id": "f2",
            "chunk_id": "c2",
            "pages": [2],
            "text": "another chunk",
            "metadata": {"source": vector_store_id, "requested_top_k": top_k},
        },
    ][:top_k]


def _fake_response_stream(*, model_id: str, system_prompt: str, user_prompt: str):
    """Deterministic response stream stub for answer generation."""
    assert model_id
    assert system_prompt
    assert "Retrieved document chunks" in user_prompt
    return iter(
        [
            SimpleNamespace(type="response.output_text.delta", delta="Grounded "),
            SimpleNamespace(type="response.output_text.delta", delta="answer."),
            SimpleNamespace(type="response.completed"),
        ]
    )


def _fake_query_rewrite(
    *, model_id: str, user_request: str, history: list[dict[str, str]]
) -> str:
    """Deterministic rewrite stub for tests."""
    del model_id
    if not history:
        return user_request
    return f"standalone: {user_request}"


def _make_agent() -> Demo6RagAgent:
    """Create test agent with fully stubbed external integrations."""
    return Demo6RagAgent(
        query_rewrite_fn=_fake_query_rewrite,
        semantic_search_fn=_fake_semantic_search,
        response_stream_fn=_fake_response_stream,
    )


def test_build_event_has_expected_envelope_fields():
    """Envelope includes common metadata and payload."""
    event = build_event(
        event_type="graph.node.started",
        run_id="run_123",
        node="QueryRewriter",
        data={"status": "running"},
    )
    assert event["id"].startswith("evt_")
    assert event["type"] == "graph.node.started"
    assert event["run_id"] == "run_123"
    assert event["node"] == "QueryRewriter"
    assert "timestamp" in event
    assert event["data"]["status"] == "running"


def test_stream_events_includes_expected_types_and_node_order():
    """Streaming output contains expected event types and node sequence."""
    agent = _make_agent()

    async def _collect():
        return [
            event
            async for event in agent.stream_events(
                user_request="test query",
                history=[],
                graph_config={"vector_store_id": "vs_test"},
            )
        ]

    events = asyncio.run(_collect())
    event_types = [event["type"] for event in events]

    assert event_types[0] == "response.started"
    assert event_types[-1] == "response.completed"
    assert "response.tool_call.started" in event_types
    assert "response.tool_call.completed" in event_types
    assert "response.output_text.delta" in event_types
    assert "response.output_text.completed" in event_types

    started_nodes = [
        event["node"] for event in events if event["type"] == "graph.node.started"
    ]
    assert started_nodes == [
        "QueryRewriter",
        "SemanticSearcher",
        "Reranker",
        "AnswerGenerator",
    ]


def test_stream_events_uses_default_graph_config():
    """Default config is emitted on response.started and used by nodes."""
    agent = _make_agent()

    async def _collect():
        return [
            event
            async for event in agent.stream_events(
                user_request="config defaults",
                history=[],
                graph_config={"vector_store_id": "vs_default"},
            )
        ]

    events = asyncio.run(_collect())
    started = next(event for event in events if event["type"] == "response.started")
    config = started["data"]["graph_config"]

    assert config["model_id"] == DEFAULT_MODEL_ID
    assert config["reranker_model_id"] == DEFAULT_RERANKER_MODEL_ID
    assert config["top_k"] == DEFAULT_TOP_K
    assert config["top_n"] == DEFAULT_TOP_N
    assert config["vector_store_id"] == "vs_default"


def test_stream_events_applies_runtime_graph_config_overrides():
    """Custom run config is propagated and influences retrieval/rerank events."""
    agent = _make_agent()

    async def _collect():
        return [
            event
            async for event in agent.stream_events(
                user_request="config overrides",
                history=[],
                graph_config={
                    "model_id": "openai.gpt-5.4-mini",
                    "reranker_model_id": "openai.gpt-5.4-mini",
                    "top_k": 2,
                    "top_n": 1,
                    "vector_store_id": "vs_custom",
                },
            )
        ]

    events = asyncio.run(_collect())

    tool_start = next(
        event for event in events if event["type"] == "response.tool_call.started"
    )
    assert tool_start["data"]["model_id"] == "openai.gpt-5.4-mini"
    assert tool_start["data"]["top_k"] == 2

    rerank_delta = next(
        event
        for event in events
        if event["type"] == "graph.state.delta" and event.get("node") == "Reranker"
    )
    assert len(rerank_delta["data"]["delta"]["reranked_chunks"]) == 1


def test_query_rewriter_is_noop():
    """QueryRewriter keeps user_request unchanged when history is empty."""
    agent = _make_agent()

    async def _collect():
        return [
            event
            async for event in agent.stream_events(
                user_request="original request",
                history=[],
                graph_config={"vector_store_id": "vs_test"},
            )
        ]

    events = asyncio.run(_collect())
    rewrite_delta = next(
        event
        for event in events
        if event["type"] == "graph.state.delta" and event.get("node") == "QueryRewriter"
    )
    assert rewrite_delta["data"]["delta"]["rewritten_query"] == "original request"


def test_query_rewriter_rewrites_when_history_is_present():
    """QueryRewriter calls rewrite function when history is not empty."""
    agent = _make_agent()

    async def _collect():
        return [
            event
            async for event in agent.stream_events(
                user_request="e quando è nata?",
                history=[{"role": "user", "content": "Parlami di Ada Lovelace"}],
                graph_config={"vector_store_id": "vs_test"},
            )
        ]

    events = asyncio.run(_collect())
    rewrite_delta = next(
        event
        for event in events
        if event["type"] == "graph.state.delta" and event.get("node") == "QueryRewriter"
    )
    assert (
        rewrite_delta["data"]["delta"]["rewritten_query"]
        == "standalone: e quando è nata?"
    )


def test_semantic_delta_contains_chunks_payload():
    """SemanticSearcher emits chunk list as data payload."""
    agent = _make_agent()

    async def _collect():
        return [
            event
            async for event in agent.stream_events(
                user_request="search request",
                history=[],
                graph_config={"vector_store_id": "vs_test"},
            )
        ]

    events = asyncio.run(_collect())
    semantic_delta = next(
        event
        for event in events
        if event["type"] == "graph.state.delta"
        and event.get("node") == "SemanticSearcher"
    )
    assert "chunks" in semantic_delta["data"]
    assert len(semantic_delta["data"]["chunks"]) == 2
    for item in semantic_delta["data"]["chunks"]:
        assert set(item.keys()) == {"filename", "pages"}


def test_events_do_not_expose_chunk_texts_in_ui_payloads():
    """UI event payloads for retrieval/rerank/final state must hide chunk texts."""
    agent = _make_agent()

    async def _collect():
        return [
            event
            async for event in agent.stream_events(
                user_request="privacy check",
                history=[],
                graph_config={"vector_store_id": "vs_test"},
            )
        ]

    events = asyncio.run(_collect())

    semantic_delta = next(
        event
        for event in events
        if event["type"] == "graph.state.delta"
        and event.get("node") == "SemanticSearcher"
    )
    rerank_delta = next(
        event
        for event in events
        if event["type"] == "graph.state.delta" and event.get("node") == "Reranker"
    )
    completed = next(event for event in events if event["type"] == "response.completed")

    for item in semantic_delta["data"]["chunks"]:
        assert "text" not in item

    for item in rerank_delta["data"]["delta"]["reranked_chunks"]:
        assert "text" not in item

    for item in completed["data"]["final_state"]["retrieved_chunks"]:
        assert "text" not in item

    for item in completed["data"]["final_state"]["reranked_chunks"]:
        assert "text" not in item


def test_answer_generator_streams_model_output():
    """AnswerGenerator forwards model deltas and completed text."""
    agent = _make_agent()

    async def _collect():
        return [
            event
            async for event in agent.stream_events(
                user_request="stream answer",
                history=[],
                graph_config={"vector_store_id": "vs_test"},
            )
        ]

    events = asyncio.run(_collect())
    deltas = [
        event["data"]["delta"]
        for event in events
        if event["type"] == "response.output_text.delta"
    ]
    completed = next(
        event for event in events if event["type"] == "response.output_text.completed"
    )
    assert "".join(deltas) == "Grounded answer."
    assert completed["data"]["text"] == "Grounded answer."


def test_history_is_trimmed_to_last_20_messages():
    """History longer than 20 messages is trimmed before generation."""
    captured_prompts: list[str] = []

    def _capturing_response_stream(
        *, model_id: str, system_prompt: str, user_prompt: str
    ):
        del model_id, system_prompt
        captured_prompts.append(user_prompt)
        return iter([SimpleNamespace(type="response.output_text.delta", delta="ok")])

    agent = Demo6RagAgent(
        query_rewrite_fn=_fake_query_rewrite,
        semantic_search_fn=_fake_semantic_search,
        response_stream_fn=_capturing_response_stream,
    )

    history = [{"role": "user", "content": f"m{i}"} for i in range(25)]

    async def _collect():
        return [
            event
            async for event in agent.stream_events(
                user_request="history trim",
                history=history,
                graph_config={"vector_store_id": "vs_test"},
            )
        ]

    asyncio.run(_collect())
    assert len(captured_prompts) == 1
    prompt = captured_prompts[0]
    assert "user: m0" not in prompt
    assert "user: m4" not in prompt
    assert "user: m5" in prompt
    assert "user: m24" in prompt
