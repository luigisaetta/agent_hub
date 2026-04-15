# Streamlit Generalized Agent Client

A Streamlit client to test OCI Enterprise AI hosted agent endpoints with flexible
payloads (JSON or plain text) and optional JWT authentication.

## Run

From the repository root:

```bash
streamlit run agents/streamlit_client/app.py
```

## Sidebar

- drag-and-drop `.env` upload with `Populate UI from .env file`
- automatic mapping from `.env` variables to UI fields: `AGENT_URL`, `GENAI_APPLICATION_ID`, `REGION`, `OCI_DOMAIN_URL`, `OCI_CLIENT_ID`, `OCI_CLIENT_SECRET`, `OCI_SCOPE`, `OCI_TOKEN_URL`, `REQUEST_TIMEOUT_SECONDS`
- toggle `Create JWT token`
- `client_id`
- `client_secret`
- `GenAI application id` (used to derive the URL automatically)
- `region`
- `Agent URL (derived, editable)`
- `Agent endpoint path` (default: `/actions/invoke/chat`)
- JWT parameters: `OCI domain URL`, `OCI scope`, `OCI token URL (optional)`, `Show important JWT claims`

## Usage

1. Fill runtime configuration in the sidebar.
2. Enter payload in the main area (JSON or plain text).
3. Click `Invoke Agent`.
4. Inspect the final output and parsed SSE events.
