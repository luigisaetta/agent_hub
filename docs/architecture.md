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

1. Scripts import settings from `config.py` and secrets/identifiers from `config_private.py`.
2. `common.clients.get_inference_client()` and `common.clients.get_control_plane_client()` provide the two OpenAI-compatible clients used by examples.
3. Scripts execute API calls and reuse common output/retrieval helpers for consistency.

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
