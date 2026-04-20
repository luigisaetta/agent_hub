"""
Author: L. Saetta
Last modified: 2026-04-20
License: MIT

Description:
    Demo 6 FastAPI backend exposing SSE endpoint for simulated LangGraph RAG.
"""

# pylint: disable=import-error

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from demos.demo6.backend import Demo6RagAgent, GraphRunConfig

app = FastAPI(title="Demo6 RAG Backend", version="0.1.0")
agent = Demo6RagAgent()
AGENT_CARD_PATH = "/.well-known/agent.json"
ALLOWED_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


def build_agent_card(base_url: str) -> dict[str, Any]:
    """Build a minimal A2A-style agent card for demo6 backend."""
    normalized_base = base_url.rstrip("/")
    return {
        "schema_version": "a2a-card.v1",
        "id": "demo6-rag-agent",
        "name": "Demo6 RAG Agent",
        "description": (
            "LangGraph-style RAG assistant with SSE streaming and semantic search."
        ),
        "url": normalized_base,
        "version": "0.1.0",
        "default_input_modes": ["text/plain"],
        "default_output_modes": ["text/plain"],
        "capabilities": {
            "streaming": True,
            "push_notifications": False,
            "history": True,
        },
        "skills": [
            {
                "id": "rag_qa",
                "name": "RAG Question Answering",
                "description": (
                    "Rewrites query, retrieves/reranks chunks from vector store, "
                    "then streams grounded answer."
                ),
                "tags": ["rag", "semantic-search", "sse", "langgraph"],
                "examples": [
                    "Spiegami l'architettura di demo6",
                    "Quali sono i nodi del flusso?",
                ],
            }
        ],
        "endpoints": {
            "chat_sse": f"{normalized_base}/chat",
            "health": f"{normalized_base}/health",
            "ready": f"{normalized_base}/ready",
            "agent_card": f"{normalized_base}{AGENT_CARD_PATH}",
        },
    }


class ChatStreamRequest(BaseModel):
    """Request payload for chat stream endpoint."""

    class MessageItem(BaseModel):
        """One history message item."""

        role: Literal["user", "assistant"]
        content: str

    user_request: str | None = None
    history: list[MessageItem] = Field(default_factory=list)
    model_id: str | None = None
    reranker_model_id: str | None = None
    top_k: int | None = None
    top_n: int | None = None
    vector_store_id: str | None = None

    def resolved_query(self) -> str:
        """Return the effective query accepted by backend."""
        return (self.user_request or "").strip()

    def graph_config(self) -> GraphRunConfig:
        """Build optional graph config override from request body."""
        config: GraphRunConfig = {}
        if self.model_id:
            config["model_id"] = self.model_id
        if self.reranker_model_id:
            config["reranker_model_id"] = self.reranker_model_id
        if self.top_k is not None:
            config["top_k"] = self.top_k
        if self.top_n is not None:
            config["top_n"] = self.top_n
        if self.vector_store_id:
            config["vector_store_id"] = self.vector_store_id
        return config

    def history_payload(self) -> list[dict[str, str]]:
        """Return history payload in a simple serializable structure."""
        return [
            {"role": item.role, "content": item.content}
            for item in self.history
            if item.content.strip()
        ]


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


@app.get(AGENT_CARD_PATH)
async def agent_card(request: Request) -> dict[str, Any]:
    """Expose a well-known A2A-style card for discovery."""
    return build_agent_card(str(request.base_url))


@app.post("/chat")
async def chat_stream(payload: ChatStreamRequest):
    """Stream standardized execution events over SSE."""
    query = payload.resolved_query()
    if not query:
        raise HTTPException(status_code=400, detail="user_request is required")

    async def event_stream() -> AsyncIterator[str]:
        async for event in agent.stream_events(
            user_request=query,
            history=payload.history_payload(),
            graph_config=payload.graph_config(),
        ):
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
