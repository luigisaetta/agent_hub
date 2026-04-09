# Demo6 Backend Event Contract (SSE)

This document describes the SSE event format and semantics emitted by
`Demo6RagAgent.stream_events(...)` and serialized by `POST /chat`.

## Transport

- Endpoint: `POST /chat`
- Response `Content-Type`: `text/event-stream`
- SSE wire format:

```text
event: <event_type>
data: <json_payload>
```

`event_type` matches `payload.type`.

## Event Envelope (common to all events)

Every event has this JSON structure:

```json
{
  "id": "evt_<hex>",
  "type": "<event_type>",
  "timestamp": 1710000000,
  "run_id": "run_<hex>",
  "node": "QueryRewriter | SemanticSearcher | Reranker | AnswerGenerator | null",
  "data": {}
}
```

Fields:

- `id`: unique event identifier within the run.
- `type`: event type (see sections below).
- `timestamp`: Unix timestamp (seconds).
- `run_id`: unique identifier of the execution run.
- `node`: graph node associated with the event; `null` for global events.
- `data`: payload specific to the event type.

## Logical Event Order

High-level order:

1. `response.started`
2. For each node (`QueryRewriter`, `SemanticSearcher`, `Reranker`, `AnswerGenerator`):
   - `graph.node.started`
   - `response.tool_call.started` (only for `SemanticSearcher`)
   - `graph.state.delta`
   - `response.output_text.delta` (zero or more times, only for `AnswerGenerator`)
   - `graph.state.delta` with final answer (only for `AnswerGenerator`)
   - `response.output_text.completed` (only for `AnswerGenerator`)
   - `response.tool_call.completed` (only for `SemanticSearcher`)
   - `graph.node.completed`
3. `response.completed`

If an exception occurs, `response.error` is emitted and the run ends.

## Event Types And Payloads

### 1) `response.started`

Global run start event.

```json
{
  "message": "Execution started",
  "graph_config": {
    "model_id": "openai.gpt-5.4",
    "reranker_model_id": "openai.gpt-5.4",
    "top_k": 10,
    "top_n": 8,
    "vector_store_id": "vs_..."
  }
}
```

### 2) `graph.node.started`

Node execution started.

```json
{
  "status": "running"
}
```

### 3) `response.tool_call.started` (only `SemanticSearcher`)

Retrieval tool call started.

```json
{
  "tool_name": "semantic_search",
  "model_id": "openai.gpt-5.4",
  "top_k": 10
}
```

### 4) `graph.state.delta`

Node-specific state delta.

#### 4.a QueryRewriter

```json
{
  "delta": {
    "rewritten_query": "query...",
    "rewriter_model_id": "openai.gpt-5.4"
  }
}
```

#### 4.b SemanticSearcher

```json
{
  "chunks": [
    {
      "filename": "doc.pdf",
      "pages": [1, 2]
    }
  ]
}
```

#### 4.c Reranker

```json
{
  "delta": {
    "reranked_chunks": [
      {
        "filename": "doc.pdf",
        "pages": [1]
      }
    ],
    "reranker_model_id": "openai.gpt-5.4"
  }
}
```

#### 4.d AnswerGenerator (prompt ready)

```json
{
  "delta": {
    "prompt_ready": true
  }
}
```

#### 4.e AnswerGenerator (final aggregated answer)

```json
{
  "delta": {
    "answer": "full final text"
  }
}
```

### 5) `response.output_text.delta` (only `AnswerGenerator`)

Incremental text chunk.

```json
{
  "delta": "token/chunk"
}
```

### 6) `response.output_text.completed` (only `AnswerGenerator`)

Text streaming completed event.

```json
{
  "text": "full final text"
}
```

### 7) `response.tool_call.completed` (only `SemanticSearcher`)

Retrieval tool call completed.

```json
{
  "tool_name": "semantic_search",
  "documents": 8,
  "top_k": 10
}
```

`documents` is the number of retrieved chunks, not the full documents themselves.

### 8) `graph.node.completed`

Node execution completed.

```json
{
  "status": "completed"
}
```

### 9) `response.completed`

Global run completion event.

```json
{
  "message": "Execution completed",
  "output_text": "full final text",
  "final_state": {
    "user_request": "user query",
    "graph_config": { "...": "..." },
    "retrieved_chunks": [
      {
        "filename": "doc.pdf",
        "pages": [1]
      }
    ],
    "reranked_chunks": [
      {
        "filename": "doc.pdf",
        "pages": [1]
      }
    ],
    "answer": "full final text"
  }
}
```

### 10) `response.error`

Stable global error event for the UI:

```json
{
  "message": "error details"
}
```

## Payload Privacy Notes

UI-oriented payloads do not expose full retrieval/rerank chunk texts:

- `SemanticSearcher` and `Reranker` only emit `filename` and `pages`.
- `response.completed.data.final_state` also includes reduced chunk payloads.

## Recommendations For SSE Clients

- Group events by `run_id`.
- Treat `response.output_text.delta` as incremental stream content.
- Treat `response.output_text.completed` and `response.completed` as completion markers.
- Treat `response.error` as a terminal error event.
