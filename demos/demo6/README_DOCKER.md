# Demo6 Docker Deploy (Backend API)

This guide packages and runs only the backend API (`demos.demo6.api`) with Docker Compose.

## Files

- `demos/demo6/Dockerfile`
- `demos/demo6/docker-compose.yml`
- `demos/demo6/.env.compose.example`

## Prerequisites

- Docker Engine + Docker Compose v2 (`docker compose version`)
- Existing `agent_hub` secrets profile file (for example `.env.prod-chicago`)

## Quick Start

From repository root:

```bash
cp demos/demo6/.env.compose.example demos/demo6/.env.compose
```

Edit `demos/demo6/.env.compose` and set at least:

- `AGENT_HUB_SECRETS_FILE` to an **absolute path** to your secrets file
- `AGENT_HUB_REGION` to the target OCI region

Start:

```bash
docker compose --env-file demos/demo6/.env.compose -f demos/demo6/docker-compose.yml up --build -d
```

Check status/logs:

```bash
docker compose --env-file demos/demo6/.env.compose -f demos/demo6/docker-compose.yml ps
docker compose --env-file demos/demo6/.env.compose -f demos/demo6/docker-compose.yml logs -f demo6-api
```

Stop:

```bash
docker compose --env-file demos/demo6/.env.compose -f demos/demo6/docker-compose.yml down
```

## Endpoints

- `GET /health`
- `GET /ready`
- `GET /.well-known/agent.json`
- `POST /chat` (SSE stream)

Default local URL: `http://127.0.0.1:8000`

## Configurable Settings

The following settings are in `demos/demo6/.env.compose`:

- `DEMO6_HOST_PORT`: host port mapped to container port 8000.
- `DEMO6_API_CONTAINER_NAME`: container name override.
- `DEMO6_IMAGE_NAME`: final Docker image name.
- `DEMO6_UVICORN_WORKERS`: uvicorn worker count.
- `DEMO6_LOG_LEVEL`: uvicorn log level (`info`, `debug`, ...).
- `AGENT_HUB_REGION`: region used by `config.py`.
- `AGENT_HUB_SECRETS_FILE`: host path to env secrets file mounted read-only in container.

Runtime model/retrieval settings can still be overridden per request on `POST /chat`
(`model_id`, `reranker_model_id`, `top_k`, `top_n`, `vector_store_id`).
