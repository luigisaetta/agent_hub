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
