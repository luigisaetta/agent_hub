# Configuration

This project uses a shared configuration at repository root and imports it from all scripts.

## Files

- `config.py`: non-secret runtime settings (region, endpoint mode, base URLs, default model id).
- `config_private.py`: loads secret/runtime identifiers from the active `.env` profile.
- `config_private_template.py`: reference for required secret keys.
- `.env.preprod-chicago`, `.env.preprod-frankfurt`, `.env.prod-frankfurt`: secret profiles (gitignored).
- `set_env.sh`: selects active secret profile.
- `show_current_env.sh`: shows currently active secret profile.

## What to edit

1. Edit `config.py`:
- `REGION`: OCI region (for example `us-chicago-1` or `eu-frankfurt-1`).
- `IS_PREPROD`: set `True` for PPE endpoints, `False` for production endpoints.
- `MODEL_ID`: default model used by examples/demos (for example `openai.gpt-5.2`).

2. Set active secret profile:

```bash
source ./set_env.sh preprod-chicago
./show_current_env.sh
```

3. Fill/update the `.env.*` profile files with your values:
- `PROJECT_ID`: OCI Generative AI project OCID.
- `KEY1` / `KEY2`: API keys.
- `COMPARTMENT_ID`: compartment OCID (needed by connector and compatibility flows).
- `LANGFUSE_SECRET_KEY` / `LANGFUSE_PUBLIC_KEY` / `LF_PWD` for Langfuse examples.
- `VECTOR_STORE_ID`: vector store OCID for retrieval examples (can be empty in environments where vector stores are unavailable, e.g. current prod).

## Endpoint behavior

`config.py` builds endpoints automatically from `REGION` and `IS_PREPROD`:

- Data plane (`BASE_URL`): inference/responses calls.
- Control plane (`CP_BASE_URL`): vector stores and connector management.

When `IS_PREPROD=True`, URLs use `ppe.*`. Otherwise they use production domains.

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

- If features like vector stores are unavailable in production, try `IS_PREPROD=True`.
- If you get authorization failures (`404`/policy-related), verify IAM policies and compartment/project OCIDs.
