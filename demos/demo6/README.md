# Demo6: LangGraph-style RAG Backend with SSE + Streamlit/Next.js UI

This demo provides:
- backend API with SSE streaming (`POST /chat`)
- Streamlit chat UI that consumes the SSE stream in real time
- Next.js chat UI (`demos/demo6/web`) with ChatGPT-style conversation layout,
  sidebar aligned to `oci_agents_workshop` style, and independent scroll area
  for user/assistant messages

Implemented goals:
- backend/frontend separation,
- HTTP streaming with SSE on `POST /chat`,
- standardized event envelope for lifecycle, graph, tool, and output events,
- runnable nodes for:
  - `QueryRewriter`
  - `SemanticSearcher`
  - `Reranker`
  - `AnswerGenerator`
- `SemanticSearcher` integrated with `vector_stores.search(...)`.
- `AnswerGenerator` uses Responses API with streamed output text deltas.
- Streamlit UI with:
  - sidebar runtime config (`model_id`, `vector_store_id`)
  - sidebar references updated after reranker (`filename` + `pages`, collapsible items)
  - central chat view (ChatGPT-style layout)
  - conversation history stored in session state and sent to backend

## Install demo dependencies

```bash
pip install -r demos/demo6/requirements.txt
```

## Docker Compose (backend API)

To run the backend API in a container with Docker Compose:

- full guide: `demos/demo6/README_DOCKER.md`
- main files:
  - `demos/demo6/Dockerfile`
  - `demos/demo6/docker-compose.yml`
  - `demos/demo6/.env.compose.example`

## Run Backend API (uvicorn)

From repository root:

```bash
uvicorn demos.demo6.api:app --reload --port 8080
```

## Run Streamlit UI

From repository root (in a second terminal):

```bash
streamlit run demos/demo6/app.py
```

## Run Next.js UI

From repository root (in a second terminal):

```bash
cd demos/demo6/web
npm install
npm run dev
```

Default frontend URL:
- `http://localhost:3000`

## Endpoint

- `POST /chat`
- `GET /.well-known/agent.json` (A2A-style agent card)
- Request body (JSON):

```json
{
  "user_request": "Explain the architecture",
  "history": [
    {"role": "user", "content": "What is demo6?"},
    {"role": "assistant", "content": "It is a LangGraph-style RAG backend."}
  ]
}
```

Optional runtime config fields:
- `model_id` (default: `openai.gpt-5.4`)
- `reranker_model_id` (default: `openai.gpt-5.4`)
- `top_k` (default: `10`)
- `top_n` (default: `8`)
- `vector_store_id` (default: loaded from env profile, same behavior as demo5)
- `history[*].role` supports: `user`, `assistant`

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
curl -N -X POST "http://127.0.0.1:8080/chat" \
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

For the full SSE event format specification:

- `demos/demo6/README_EVENTS.md`
