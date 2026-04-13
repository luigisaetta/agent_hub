# Deep Agents 01

`agents/` example based on Deep Agents (LangChain/LangGraph) with:
- separate agent backend
- separate FastAPI SSE API
- separate CLI client
- OCI OpenAI-compatible integration via `ChatOpenAI`

This example is designed for local execution (no JWT).

## Goal

Provide a second agent in the `agent_hub` project with a structure similar to `hello_world`, but using the Deep Agents framework.

## Architecture

High-level flow:
1. The CLI client sends `POST /chat` with `prompt`
2. The API receives the request and opens an SSE stream
3. The backend invokes Deep Agents with `ChatOpenAI`
4. The API forwards SSE events to the client
5. The client prints final text output or an error

## Main files

- `agents/deep_agents01/backend.py`
  - builds the deep agent (`create_deep_agent`)
  - configures `ChatOpenAI` on OCI endpoint
  - forces Responses API
  - converts output to SSE-friendly events (`response.started`, `response.output_text.delta`, `response.completed`, `response.error`)
- `agents/deep_agents01/api.py`
  - exposes `GET /health`, `GET /ready`, `POST /chat`
  - serializes events in SSE format
  - lazily initializes the backend (on first `POST /chat`)
- `agents/deep_agents01/client.py`
  - minimal CLI client
  - reads SSE stream
  - prints text output
  - prints backend errors to `stderr` and exits with code `1`
- `agents/deep_agents01/requirements.txt`
  - dependencies specific to this agent
- `agents/deep_agents01/.env.local`
  - local secrets for API key and project id (not versioned)
- `agents/deep_agents01/deep_agents01.env.sample`
  - template to create `.env.local`
- `tests/test_deep_agents01_api.py`
- `tests/test_deep_agents01_backend.py`
- `tests/test_deep_agents01_client.py`

## OCI configuration: where values come from

### Recommended local env file

This agent automatically loads:
- `agents/deep_agents01/.env.local`

Recommended workflow:

```bash
cp agents/deep_agents01/deep_agents01.env.sample agents/deep_agents01/.env.local
```

Then set in that file:
- `OPENAI_API_KEY`
- `OPENAI_PROJECT_ID`

### Endpoint and region

Endpoint is read from:
- `config.py` -> `BASE_URL`

Endpoint pattern:
- `https://inference.generativeai.{REGION}.oci.oraclecloud.com/20231130/openai/v1`

Region:
- `AGENT_HUB_REGION` (env var), fallback `us-chicago-1`

### API key

Resolution order in backend:
1. `OPENAI_API_KEY`
2. `OCI_GENAI_API_KEY`
3. explicit error if missing

### Project ID

Resolution order in backend:
1. `OPENAI_PROJECT_ID`
2. `OCI_PROJECT_ID`
3. explicit error if missing

Project ID is sent as header:
- `OpenAI-Project: <project_id>`

### Model

Default:
- `openai.gpt-5.4`

Runtime override:
- `DEEP_AGENTS_MODEL`

Example:
```bash
export DEEP_AGENTS_MODEL=openai.gpt-5.2
```

## Important point: forcing Responses API

In this environment, with `deepagents` + `langchain-openai`, auto-detection could route model calls to `chat.completions`.

With OCI and this model, that path produced:
- `openai.NotFoundError: Not Found`

To avoid regressions, backend explicitly sets:
- `use_responses_api=True`
- `output_version="responses/v1"`

This forces Responses API instead of Chat Completions.

## Installation

From repository root:

```bash
pip install -r agents/deep_agents01/requirements.txt
```

If you use Conda (as in this project):

```bash
conda run -n agent_hub pip install -r agents/deep_agents01/requirements.txt
```

## Secrets security

- Runtime secrets must be in `agents/deep_agents01/.env.local`
- `.env.local` is ignored by git
- Versioned template is `agents/deep_agents01/deep_agents01.env.sample`

## Run

### 1) Start API

```bash
uvicorn agents.deep_agents01.api:app --reload --port 8090
```

### 2) Run client

```bash
python -m agents.deep_agents01.client "Explain what Deep Agents is in short"
```

With custom URL:

```bash
python -m agents.deep_agents01.client "Give me 3 use cases" --url http://127.0.0.1:8090/chat
```

## API contract

### Endpoints

- `GET /health`
- `GET /ready`
- `POST /chat` (SSE)

### Accepted payloads

Primary form:

```json
{
  "prompt": "Explain what Deep Agents is"
}
```

Compatibility with demo-style payload:

```json
{
  "user_request": "Explain what Deep Agents is"
}
```

### Main SSE events

- `response.started`
- `graph.node.started`
- `response.output_text.delta`
- `response.error`
- `response.completed`

## Error handling

### Model runtime errors

If backend receives provider/model exceptions:
- stream does not crash
- emits `response.error`
- closes with `response.completed` containing `error`

### Client behavior

Client now:
- prints `Backend error: ...` to `stderr` when receiving `response.error`
- returns exit code `1` on error
- returns exit code `1` if no output is received

This avoids silent failure mode.

## Quick troubleshooting

### `Not Found`

Possible causes:
- model not available on selected route
- wrong endpoint/region
- API path mismatch
- Responses API not forced (already handled in this example)

Recommended checks:
1. verify `AGENT_HUB_REGION`
2. verify `BASE_URL` in `config.py`
3. verify key (`OPENAI_API_KEY` or `OCI_GENAI_API_KEY`)
4. try alternate model:
   ```bash
   export DEEP_AGENTS_MODEL=openai.gpt-5.2
   ```

### Client prints nothing

With current version this should not happen:
- on backend error: prints message and exits `1`
- on stream without text: prints `No output received from server.` and exits `1`

## Upstream example reference

Adapted from official Deep Agents quickstart:
- https://github.com/langchain-ai/deepagents

With `agent_hub`-specific integration (OCI endpoint, local config, separated API/client).
