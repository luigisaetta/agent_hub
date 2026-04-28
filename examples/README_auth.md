# Examples: Auth & Security

This group contains authentication-focused examples for OCI Identity Domain.

| # | Example | File | Purpose | Key API usage | Good for | Notes |
|---|---|---|---|---|---|---|
| 1 | OCI Identity Domain JWT token | [`example24.py`](example24.py) | Requests an OAuth2 client-credentials token from OCI Identity Domain and prints full decoded JWT content (header, payload, signature). | `POST /oauth2/v1/token` with `grant_type=client_credentials`, Base64 `Authorization: Basic ...` | Integrating with OCI domain auth and inspecting JWT claims. | Uses local env file (`--env-file`, default `examples/.env.example24.local`). |

## Example 24 setup

Create the local env file from the versioned template:

```bash
cp examples/example24.env.sample examples/.env.example24.local
```

Then edit `examples/.env.example24.local` with real OCI Identity Domain values
before running:

```bash
python -m examples.example24
```
