# Hello World Agent

Primo agent demo separato dalle demo generiche (`demos/`).

## Run API (host/port come demo6)

```bash
uvicorn agents.hello_world.api:app --reload --port 8080
```

## Endpoint

- `GET /health`
- `GET /ready`
- `POST /chat` (SSE)

### Payload esempio

```json
{
  "name": "Luca"
}
```

Compatibilita con payload demo6-like:

```json
{
  "user_request": "Luca"
}
```

## Client CLI

```bash
conda run -n agent_hub python -m agents.hello_world.client Luca
```

## Client CLI (JWT)

```bash
conda run -n agent_hub python -m agents.hello_world.client_jwt Luca
```

Before running, update values in the dedicated env file:
- `agents/hello_world/.env.client_jwt.local`
- Start from sample: `agents/hello_world/client_jwt.env.sample`
- Required keys: `AGENT_URL`, `OCI_DOMAIN_URL`, `OCI_CLIENT_ID`, `OCI_CLIENT_SECRET`, `OCI_SCOPE`
- Optional keys: `OCI_TOKEN_URL`, `REQUEST_TIMEOUT_SECONDS`, `DEBUG_TOKEN_HTTP_REQUEST`

You can also pass a custom env file path:

```bash
conda run -n agent_hub python -m agents.hello_world.client_jwt Luca --env-file path/to/.env.file
```

## Docker Deploy

### Build image

Da root repository:

```bash
docker build -f agents/hello_world/Dockerfile -t agent-hub-hello-world:latest .
```

### Run container

```bash
docker run --rm -p 8080:8080 --name hello-world-agent agent-hub-hello-world:latest
```

### Check endpoints

```bash
curl -i http://127.0.0.1:8080/health
curl -i http://127.0.0.1:8080/ready
```

### Docker Compose (opzionale)

```bash
docker compose -f agents/hello_world/docker-compose.yml up --build -d
docker compose -f agents/hello_world/docker-compose.yml ps
docker compose -f agents/hello_world/docker-compose.yml logs -f hello-world-agent
docker compose -f agents/hello_world/docker-compose.yml down
```
