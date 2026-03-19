# Configuration

This project uses a shared configuration at repository root and imports it from all scripts.

## Files

- `config.py`: non-secret runtime settings (region, endpoint mode, base URLs).
- `config_private.py`: secret/runtime identifiers (project id, api keys, compartment id).
- `config_private_template.py`: template to create your own `config_private.py`.

## What to edit

1. Edit `config.py`:
- `REGION`: OCI region (for example `us-chicago-1` or `eu-frankfurt-1`).
- `IS_PREPROD`: set `True` for PPE endpoints, `False` for production endpoints.

2. Create/update `config_private.py` from `config_private_template.py`:
- `PROJECT_ID`: OCI Generative AI project OCID.
- `KEY1` / `KEY2`: API keys.
- `COMPARTMENT_ID`: compartment OCID (needed by connector and compatibility flows).

## Endpoint behavior

`config.py` builds endpoints automatically from `REGION` and `IS_PREPROD`:

- Data plane (`BASE_URL`): inference/responses calls.
- Control plane (`CP_BASE_URL`): vector stores and connector management.

When `IS_PREPROD=True`, URLs use `ppe.*`. Otherwise they use production domains.

## Security notes

- Never commit real secrets in `config_private.py`.
- Keep `config_private_template.py` as placeholder values only.
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
