# Configuration

This project uses a shared configuration at repository root and imports it from all scripts.

## Files

- `config.py`: non-secret runtime settings (region, base URLs, default model id).
- `config_private.py`: loads secret/runtime identifiers from the active `.env` profile.
- `.env.prod-chicago`, `.env.prod-frankfurt`: secret profiles (gitignored).
- `set_env.sh`: selects active secret profile.
- `show_current_env.sh`: shows currently active secret profile.

## What to edit

1. Edit `config.py`:
- `MODEL_ID`: default model used by examples/demos (for example `openai.gpt-5.2`).
  `REGION` has a default in code, but normal operation should select region via
  `source ./set_env.sh <profile>` which exports `AGENT_HUB_REGION`.

2. Fill/update the `.env.*` profile files with your values:
- `PROJECT_ID`: OCI Generative AI project OCID.
- `KEY1`: API key.
- `COMPARTMENT_ID`: compartment OCID (needed by connector and compatibility flows).
- `LANGFUSE_SECRET_KEY` / `LANGFUSE_PUBLIC_KEY` for Langfuse examples.
- `VECTOR_STORE_ID`: vector store OCID for retrieval examples.

3. Set active secret profile:

```bash
source ./set_env.sh prod-chicago
./show_current_env.sh
```

Supported profiles are production only:
- `prod-chicago`
- `prod-frankfurt`

## Endpoint behavior

`config.py` builds endpoints automatically from `REGION`:

- Data plane (`BASE_URL`): inference/responses calls.
- Control plane (`CP_BASE_URL`): vector stores and connector management.

## OCI auth mode for connector client

Set authentication mode in your active profile/shell with:

```bash
export OCI_AUTH_MODE=user_principal
```

Supported values:
- `user_principal` (default when variable is not set)
- `session`

Both `common.build_oci_genai_client(...)` and
`common.get_control_plane_client(...)` read this variable when `auth_mode` is
not passed explicitly.

`session` requires `security_token_file` + `key_file` in OCI profile.
`user_principal` requires an API-key profile (for example no
`security_token_file`, and `key_file`/`key_content` configured for the user key).

## Security notes

- Never commit real secrets in tracked files.
- Keep secret values only in `.env.*` files (already gitignored).
- Rotate keys if they were accidentally exposed.

## Running scripts correctly

Run from repo root using module mode so imports resolve consistently:

```bash
python -m examples.example01
python -m connectors.list_connectors
```

## Troubleshooting

- If you get authorization failures (`404`/policy-related), verify IAM policies and compartment/project OCIDs.
