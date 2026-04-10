"""
Author: L. Saetta
Last modified: 2026-04-10
License: MIT

Description:
    Tests for Hello World agent backend event model and streaming flow.
"""

# pylint: disable=import-error

from __future__ import annotations

import asyncio

from agents.hello_world.backend import HelloWorldAgent, build_event


def test_build_event_has_expected_envelope_fields():
    """Envelope includes common metadata and payload."""
    event = build_event(
        event_type="graph.node.started",
        run_id="run_123",
        node="HelloNode",
        data={"status": "running"},
    )
    assert event["id"].startswith("evt_")
    assert event["type"] == "graph.node.started"
    assert event["run_id"] == "run_123"
    assert event["node"] == "HelloNode"
    assert "timestamp" in event
    assert event["data"]["status"] == "running"


def test_stream_events_returns_hello_message_with_name():
    """Stream should emit output_text events with personalized greeting."""
    agent = HelloWorldAgent()

    async def _collect():
        return [event async for event in agent.stream_events(name="Luca")]

    events = asyncio.run(_collect())
    event_types = [event["type"] for event in events]

    assert event_types[0] == "response.started"
    assert event_types[-1] == "response.completed"
    assert "graph.node.started" in event_types
    assert "response.output_text.delta" in event_types

    final_event = next(
        event for event in events if event["type"] == "response.completed"
    )
    assert final_event["data"]["output_text"] == "Hello, Luca!"


def test_stream_events_falls_back_to_world_on_blank_name():
    """Blank input name should normalize to world."""
    agent = HelloWorldAgent()

    async def _collect():
        return [event async for event in agent.stream_events(name="  ")]

    events = asyncio.run(_collect())
    final_event = next(
        event for event in events if event["type"] == "response.completed"
    )

    assert final_event["data"]["output_text"] == "Hello, world!"
