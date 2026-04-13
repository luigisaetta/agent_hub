"""
Author: L. Saetta
Last modified: 2026-04-13
License: MIT

Description:
    FastAPI API for local Deep Agents example.
"""

# pylint: disable=import-error,invalid-name

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from agents.deep_agents01.backend import DeepAgentsLocalBackend

app = FastAPI(title="Deep Agents Local", version="0.1.0")
_agent: DeepAgentsLocalBackend | None = None


class ChatRequest(BaseModel):
    """Input payload accepted by deep-agents API."""

    prompt: str | None = None
    user_request: str | None = None

    def resolved_prompt(self) -> str:
        """Resolve accepted aliases for prompt text."""
        return (self.prompt or self.user_request or "").strip()


def to_sse(event: dict) -> str:
    """Serialize one event into SSE wire format."""
    payload = json.dumps(event, ensure_ascii=False, default=str)
    event_type = event.get("type", "message")
    return f"event: {event_type}\ndata: {payload}\n\n"


def _get_agent() -> DeepAgentsLocalBackend:
    """Return singleton backend instance, lazily initialized on first request."""
    global _agent  # pylint: disable=global-statement
    if _agent is None:
        _agent = DeepAgentsLocalBackend()
    return _agent


@app.get("/health")
async def health() -> Response:
    """Liveness endpoint."""
    return Response(status_code=200, media_type="application/json")


@app.get("/ready")
async def ready() -> Response:
    """Readiness endpoint."""
    return Response(status_code=200, media_type="application/json")


@app.post("/chat")
async def chat_stream(payload: ChatRequest):
    """Stream deep-agent execution events over SSE."""
    user_request = payload.resolved_prompt()
    if not user_request:
        raise HTTPException(status_code=400, detail="prompt is required")

    try:
        backend = _get_agent()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=500, detail=f"backend initialization failed: {exc}"
        ) from exc

    async def event_stream() -> AsyncIterator[str]:
        async for event in backend.stream_events(user_request=user_request):
            yield to_sse(event)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=headers,
    )
