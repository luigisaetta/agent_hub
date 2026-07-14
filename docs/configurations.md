# Configuration

This project uses a shared configuration at repository root and imports it from all scripts.

## Files

- `config.py`: non-secret runtime settings (region, base URLs, default model id).
- `config_private.py`: loads secret/runtime identifiers from the active `.env` profile.
- `.env.prod-chicago`, `.env.prod-frankfurt`, `.env.prod-london`: local secret
  profiles (gitignored).
- `*.env.sample`, `*.env.example`, `.env*.sample`, `.env*.example`: versioned templates
  to copy into local secret/config files.
- `set_env.sh`: selects active secret profile.
- `show_current_env.sh`: shows currently active secret profile.

## What to edit

1. Edit `config.py`:
- `MODEL_ID`: default model used by examples/demos (for example `openai.gpt-5.2`).
  `REGION` has a default in code, but normal operation should select region via
  `source ./set_env.sh <profile>` which exports `AGENT_HUB_REGION`.

2. Fill/update the `.env.*` profile files with your values:
- `PROJECT_ID`: OCI Generative AI project OCID.
- `KEY1`: API key (used when inference auth mode is `api_key`, which is the default).
- `COMPARTMENT_ID`: compartment OCID (needed by connector and compatibility flows).
- `LANGFUSE_SECRET_KEY` / `LANGFUSE_PUBLIC_KEY` for Langfuse examples.
  If Langfuse is not used, both can be unset or empty strings.
- `VECTOR_STORE_ID`: vector store OCID for retrieval examples.

Example `.env` profile:

```bash
ENV_NAME=prod-chicago
PROJECT_ID=ocid1.generativeaiproject.oc1.us-chicago-1.xxxxx
KEY1=sk-xxxxxxxxxxxxxxxxxxxxxxxx
COMPARTMENT_ID=ocid1.compartment.oc1..xxxxxxxxxxxxxxxxxxxxxxxx
LANGFUSE_SECRET_KEY=
LANGFUSE_PUBLIC_KEY=
VECTOR_STORE_ID=vs_ord_xxxxxxxxxxxxxxxxxxxxxxxxx
```

3. Set active secret profile:

```bash
source ./set_env.sh prod-chicago
./show_current_env.sh
```

Supported profiles are production only:
- `prod-chicago`
- `prod-frankfurt`
- `prod-london`

## Endpoint behavior

`config.py` builds endpoints automatically from `REGION`:

- Data plane (`BASE_URL`): inference/responses calls.
- Control plane (`CP_BASE_URL`): vector stores and connector management.

## Inference auth mode

Set inference authentication mode in your active profile/shell with:

```bash
export INFERENCE_AUTH_MODE=api_key
```

Supported values:
- `api_key` (default when variable is not set)
- `user_principal`
- `session`

`common.get_inference_client(...)` reads this variable.

- `api_key`: uses `KEY1` (OpenAI-compatible API key) as before.
- `user_principal`: uses OCI signer auth from `~/.oci/config` profile `DEFAULT`.
- `session`: uses OCI session signer auth (session-based profile).

This variable affects only inference/data-plane clients. It does not change
control-plane behavior.

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

`OCI_AUTH_MODE` is for control-plane/OCI SDK paths, not for
`common.get_inference_client(...)`.

`session` requires `security_token_file` + `key_file` in OCI profile.
`user_principal` requires an API-key profile (for example no
`security_token_file`, and `key_file`/`key_content` configured for the user key).

## Security notes

- Never commit real secrets in tracked files.
- Keep secret values only in local `.env*` files that are ignored by git.
- Do not put real secrets in versioned `.sample` or `.example` templates.
- Rotate keys if they were accidentally exposed.

## Running scripts correctly

Run from repo root using module mode so imports resolve consistently:

```bash
python -m examples.example01
python -m connectors.list_connectors
```

## Troubleshooting

- If you get authorization failures (`404`/policy-related), verify IAM policies and compartment/project OCIDs.
