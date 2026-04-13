"""
Author: L. Saetta
Last modified: 2026-04-13
License: MIT

Description:
    Tests for Deep Agents local backend event model and streaming flow.
"""

# pylint: disable=import-error

from __future__ import annotations

import asyncio

from agents.deep_agents01.backend import DeepAgentsLocalBackend
from agents.deep_agents01.utility import (
    build_event,
    extract_output_text,
    resolve_project_id,
)


class _StubGraph:  # pylint: disable=too-few-public-methods
    """Simple fake graph exposing async ainvoke method."""

    async def ainvoke(self, payload):
        """Return deterministic state, validating expected input shape."""
        assert payload["messages"][0]["role"] == "user"
        return {
            "messages": [
                {"role": "assistant", "content": "Questa e una risposta di test."}
            ]
        }


class _FailingGraph:  # pylint: disable=too-few-public-methods
    """Fake graph that raises at invocation time."""

    async def ainvoke(self, payload):
        """Raise a deterministic runtime error."""
        del payload
        raise RuntimeError("Not Found")


def test_build_event_has_expected_envelope_fields():
    """Envelope includes common metadata and payload."""
    event = build_event(
        event_type="graph.node.started",
        run_id="run_123",
        node="DeepAgent",
        data={"status": "running"},
    )
    assert event["id"].startswith("evt_")
    assert event["type"] == "graph.node.started"
    assert event["run_id"] == "run_123"
    assert event["node"] == "DeepAgent"
    assert "timestamp" in event
    assert event["data"]["status"] == "running"


def test_extract_output_text_supports_assistant_messages():
    """Final text extraction should pick assistant message content."""
    state = {
        "messages": [
            {"role": "user", "content": "ciao"},
            {"role": "assistant", "content": "risposta finale"},
        ]
    }

    assert extract_output_text(state) == "risposta finale"


def test_resolve_project_id_from_environment(monkeypatch):
    """Project id should prefer environment override when provided."""
    monkeypatch.setenv("OPENAI_PROJECT_ID", "proj_env_123")
    monkeypatch.delenv("OCI_PROJECT_ID", raising=False)
    assert resolve_project_id() == "proj_env_123"


def test_stream_events_returns_completed_with_output_text():
    """Backend stream should emit start, delta and completed events."""
    backend = DeepAgentsLocalBackend(graph=_StubGraph())

    async def _collect():
        return [event async for event in backend.stream_events(user_request="test")]

    events = asyncio.run(_collect())
    event_types = [event["type"] for event in events]

    assert event_types[0] == "response.started"
    assert event_types[-1] == "response.completed"
    assert "response.output_text.delta" in event_types

    final_event = next(
        event for event in events if event["type"] == "response.completed"
    )
    assert "risposta di test" in final_event["data"]["output_text"]

    started_event = next(
        event for event in events if event["type"] == "response.started"
    )
    backend_config = started_event["data"].get("backend_config", {})
    assert backend_config.get("model")
    assert backend_config.get("openai_api_base")
    assert backend_config.get("use_responses_api") is True


def test_stream_events_emits_error_event_on_runtime_failure():
    """Backend should convert runtime errors into response.error events."""
    backend = DeepAgentsLocalBackend(graph=_FailingGraph())

    async def _collect():
        return [event async for event in backend.stream_events(user_request="test")]

    events = asyncio.run(_collect())
    event_types = [event["type"] for event in events]

    assert "response.error" in event_types
    final_event = next(
        event for event in events if event["type"] == "response.completed"
    )
    assert "error" in final_event["data"]
