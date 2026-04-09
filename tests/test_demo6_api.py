"""
Author: L. Saetta
Last modified: 2026-04-09
License: MIT

Description:
    Tests for Demo 6 FastAPI API endpoints and A2A-style card discovery.
"""

# pylint: disable=import-error

from __future__ import annotations

from fastapi.testclient import TestClient

from demos.demo6 import api


class _StubAgent:  # pylint: disable=too-few-public-methods
    """Small async stream stub replacing real backend agent in API tests."""

    async def stream_events(self, **kwargs):
        """Yield deterministic events compatible with demo6 SSE serializer."""
        del kwargs
        yield {"type": "response.started", "data": {"message": "ok"}}
        yield {
            "type": "response.completed",
            "data": {"output_text": "done", "final_state": {}},
        }


def test_agent_card_well_known_endpoint_returns_expected_fields():
    """Well-known card endpoint should expose discoverable agent metadata."""
    client = TestClient(api.app)
    response = client.get("/.well-known/agent.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "a2a-card.v1"
    assert payload["id"] == "demo6-rag-agent"
    assert payload["capabilities"]["streaming"] is True
    assert payload["endpoints"]["chat_sse"].endswith("/chat")


def test_chat_endpoint_streams_sse_events(monkeypatch):
    """POST /chat should stream events serialized in SSE wire format."""
    monkeypatch.setattr(api, "agent", _StubAgent())
    client = TestClient(api.app)
    response = client.post(
        "/chat",
        json={"user_request": "ciao", "history": []},
        headers={"Accept": "text/event-stream"},
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "event: response.started" in response.text
    assert "event: response.completed" in response.text


def test_chat_endpoint_rejects_missing_user_request():
    """POST /chat should validate user_request is present and non-empty."""
    client = TestClient(api.app)
    response = client.post("/chat", json={"history": []})

    assert response.status_code == 400
    assert response.json()["detail"] == "user_request is required"
