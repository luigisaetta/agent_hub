"""
Author: L. Saetta
Last modified: 2026-04-10
License: MIT

Description:
    FastAPI API for the Hello World LangGraph agent.
"""

# pylint: disable=import-error

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from agents.hello_world.backend import HelloWorldAgent

app = FastAPI(title="Hello World Agent", version="0.1.0")
agent = HelloWorldAgent()


class ChatRequest(BaseModel):
    """Input payload accepted by hello-world agent API."""

    name: str | None = None
    user_request: str | None = None

    def resolved_name(self) -> str:
        """Resolve input field for compatibility with demo6 payload shape."""
        return (self.name or self.user_request or "").strip()


def to_sse(event: dict) -> str:
    """Serialize one event into SSE wire format."""
    payload = json.dumps(event, ensure_ascii=False)
    event_type = event.get("type", "message")
    return f"event: {event_type}\ndata: {payload}\n\n"


@app.get("/health")
async def health() -> Response:
    """Liveness endpoint used to verify container is alive."""
    return Response(status_code=200, media_type="application/json")


@app.get("/ready")
async def ready() -> Response:
    """Readiness endpoint used to verify container can receive traffic."""
    return Response(status_code=200, media_type="application/json")


@app.post("/chat")
async def chat_stream(payload: ChatRequest):
    """Stream hello-world execution events over SSE."""
    name = payload.resolved_name()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    async def event_stream() -> AsyncIterator[str]:
        async for event in agent.stream_events(name=name):
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
