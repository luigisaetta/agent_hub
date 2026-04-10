"""
Author: L. Saetta
Last modified: 2026-04-10
License: MIT

Description:
    Tests for Hello World FastAPI endpoints and SSE stream behavior.
"""

# pylint: disable=import-error

from __future__ import annotations

from fastapi.testclient import TestClient

from agents.hello_world import api


class _StubAgent:  # pylint: disable=too-few-public-methods
    """Small async stream stub replacing real backend agent in API tests."""

    async def stream_events(self, **kwargs):
        """Yield deterministic events compatible with API SSE serializer."""
        del kwargs
        yield {"type": "response.started", "data": {"message": "ok"}}
        yield {
            "type": "response.completed",
            "data": {"output_text": "Hello, Test!", "final_state": {}},
        }


def test_health_endpoint_returns_200():
    """GET /health should be available for liveness checks."""
    client = TestClient(api.app)
    response = client.get("/health")

    assert response.status_code == 200


def test_ready_endpoint_returns_200():
    """GET /ready should be available for readiness checks."""
    client = TestClient(api.app)
    response = client.get("/ready")

    assert response.status_code == 200


def test_chat_endpoint_streams_sse_events(monkeypatch):
    """POST /chat should stream events serialized in SSE wire format."""
    monkeypatch.setattr(api, "agent", _StubAgent())
    client = TestClient(api.app)
    response = client.post(
        "/chat",
        json={"name": "Test"},
        headers={"Accept": "text/event-stream"},
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "event: response.started" in response.text
    assert "event: response.completed" in response.text


def test_chat_endpoint_rejects_missing_name():
    """POST /chat should validate name is present and non-empty."""
    client = TestClient(api.app)
    response = client.post("/chat", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "name is required"


def test_chat_endpoint_accepts_user_request_for_compatibility(monkeypatch):
    """POST /chat accepts user_request too to match demo6-like payloads."""
    monkeypatch.setattr(api, "agent", _StubAgent())
    client = TestClient(api.app)
    response = client.post(
        "/chat",
        json={"user_request": "Ada"},
        headers={"Accept": "text/event-stream"},
    )

    assert response.status_code == 200
