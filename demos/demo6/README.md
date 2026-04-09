# Demo6: LangGraph-style RAG Backend with SSE

This demo provides only the backend API (no frontend yet).

Implemented goals:
- backend/frontend separation (backend only in this phase),
- HTTP streaming with SSE on `POST /chat`,
- standardized event envelope for lifecycle, graph, tool, and output events,
- runnable nodes for:
  - `QueryRewriter`
  - `SemanticSearcher`
  - `Reranker`
  - `AnswerGenerator`
- `SemanticSearcher` integrated with `vector_stores.search(...)`.
- `AnswerGenerator` uses Responses API with streamed output text deltas.

## Install demo dependencies

```bash
pip install -r demos/demo6/requirements.txt
```

## Run Backend API (uvicorn)

From repository root:

```bash
uvicorn demos.demo6.api:app --reload --port 8000
```

## Endpoint

- `POST /chat`
- Request body (JSON):

```json
{
  "user_request": "Explain the architecture",
  "history": []
}
```

Optional runtime config fields:
- `model_id` (default: `openai.gpt-5.4`)
- `reranker_model_id` (default: `openai.gpt-5.4`)
- `top_k` (default: `10`)
- `top_n` (default: `8`)
- `vector_store_id` (default: loaded from env profile, same behavior as demo5)

Prompt configuration:
- system prompt for answer grounding is defined in
  `demos/demo6/prompts.py`.

- Headers:
  - `Content-Type: application/json`
  - `Accept: text/event-stream`

Response content type:
- `text/event-stream`

SSE event format:

```text
event: <event_type>
data: <json_payload>
```

## Quick curl example

```bash
curl -N -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"user_request":"What is LangGraph used for in this demo?","history":[]}'
```

## CLI test client

From repository root:

```bash
python -m demos.demo6.test_client "Spiegami l'architettura di demo6"
```

## Event contract (dettaglio)

Per la specifica completa del formato eventi SSE:

- `demos/demo6/README_EVENTS.md`
