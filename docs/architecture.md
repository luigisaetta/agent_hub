# Architecture

## Overview

This repository is organized as a practical script collection around OCI Generative AI OpenAI-compatible APIs.

Core idea:
- keep shared logic in `common/`
- keep runnable scenarios in `examples/`
- keep connector operations in `connectors/`
- keep regression/unit coverage in `tests/`

## Main modules

- `common/`
- `clients.py`: creates OpenAI-compatible clients and OCI Generative AI control-plane clients.
- `output.py`: shared output formatting and streaming-print helpers.
- `retrieval.py`: extraction helpers for file-search annotations/references.
- `models.py`: helpers related to model identifiers.

- `examples/`
- End-to-end runnable examples for Responses API, Conversations, tools, vector stores, and utility scripts for list/delete tasks.

- `connectors/`
- Scripts for lifecycle management of Object Storage connectors: create, list, stats, sync, update, delete, logs.

- `tests/`
- Pytest-based tests with fixtures and fakes to validate utility behavior without depending on live SDK/network calls.

## Runtime configuration flow

1. Scripts import non-secret settings from `config.py` (for example region and base URLs) and secrets/identifiers from `config_private.py`.
2. `config_private.py` resolves which `.env` file to load using this precedence:
- `AGENT_HUB_ENV_FILE` (explicit path exported in current shell)
- `.env.active` symlink in repository root
- region-based default profile (`.env.prod-chicago` or `.env.prod-frankfurt`)
3. The selected `.env` file is loaded with `override=True`, then required secrets are validated (`PROJECT_ID`, `KEY1`, `COMPARTMENT_ID`, etc.). Langfuse keys are optional and can be empty when Langfuse integrations are not used.
4. `common.clients.get_inference_client()` and `common.clients.get_control_plane_client()` provide the two OpenAI-compatible clients used by examples.
5. Scripts execute API calls and reuse common output/retrieval helpers for consistency.

## Secret management by environment

Secrets are never hardcoded in source files. They are imported at runtime from the `.env` profile of the selected environment.

Why this is important:
- Security: credentials remain outside committed code and can be rotated per environment.
- Isolation: each environment (for example Chicago vs Frankfurt) keeps its own keys, project, and resource IDs.
- Reproducibility: changing environment is explicit and traceable, not hidden in code edits.

Operationally:
- Use `source ./set_env.sh <profile>` to select the active profile and export `AGENT_HUB_ENV_FILE` and `AGENT_HUB_REGION`.
- Use `./show_current_env.sh` before operations on shared resources (vector stores/connectors) to confirm the active profile.

This model guarantees that the same script can run unchanged across environments, while secrets and resource identifiers are injected from the correct `.env` context.

## High-level structure

```text
agent_hub/
├── common/        # shared helpers used by examples/connectors
├── examples/      # runnable API usage samples and utility scripts
├── connectors/    # connector lifecycle scripts
├── tests/         # regression and unit tests
├── docs/          # project documentation
├── config.py
├── config_private.py
└── README.md
```

## Detailed project structure

```text
agent_hub/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── configurations.md
│   └── testing.md
├── issues_found.md
├── LICENSE
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── config.py
├── config_private.py
├── set_env.sh
├── show_current_env.sh
├── common/
│   ├── __init__.py
│   ├── clients.py
│   ├── models.py
│   ├── output.py
│   └── retrieval.py
├── connectors/
│   ├── __init__.py
│   ├── create_connector.py
│   ├── delete_connector.py
│   ├── get_connector_logs.py
│   ├── get_connector_stats.py
│   ├── list_connectors.py
│   ├── trigger_file_sync.py
│   └── update_connector.py
├── demos/
│   ├── demo1/
│   │   ├── app.py
│   │   ├── backend.py
│   │   ├── README.md
│   │   ├── requirements.txt
│   │   └── state.py
│   ├── demo2/
│   │   ├── app.py
│   │   ├── backend.py
│   │   ├── README.md
│   │   ├── requirements.txt
│   │   └── state.py
│   ├── demo3/
│   │   ├── app.py
│   │   ├── backend.py
│   │   ├── llm_schema_models.py
│   │   ├── proc_vendita.json
│   │   ├── README.md
│   │   └── requirements.txt
│   ├── demo4/
│   │   ├── app.py
│   │   ├── backend.py
│   │   ├── load_files.py
│   │   ├── README.md
│   │   ├── requirements.txt
│   │   └── state.py
│   └── demo5/
│       ├── app.py
│       ├── backend.py
│       ├── README.md
│       └── requirements.txt
├── examples/
│   ├── __init__.py
│   ├── example01.py
│   ...
│   └── example21.py
├── tests/
│   ├── conftest.py
│   └── test_*.py
├── images/
└── pdf/
```
