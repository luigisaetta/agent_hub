# Agent Hub Examples for OCI OpenAI-Compatible API

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen.svg)](https://github.com/pylint-dev/pylint)

This repository contains practical Python examples that call Oracle Cloud Infrastructure (OCI) Generative AI endpoints through the OpenAI-compatible API.

The examples show how to:
- send a basic text request,
- stream model output token-by-token,
- parse responses into structured objects,
- call a model with integrated web search tooling,
- keep multi-turn state with the Conversations API,
- show how to get information about the internal LLM reasoning
- create a vector store resource.

## Project Structure

```text
agent_hub/
├── config.py
├── config_private.py
├── config_private_template.py
├── connectors/
│   ├── create_connector.py
│   ├── update_connector.py
│   ├── delete_connector.py
│   ├── list_connectors.py
│   ├── get_connector_stats.py
│   └── sync_connector.py
├── examples/
│   ├── example01.py
│   ...
│   └── example11.py
└── issues_found.md
└── README.md
```

## Prerequisites

- Python 3.11+
- An OCI Generative AI project and endpoint access
- A valid OCI API key with permissions for Generative AI

Install dependencies:

```bash
pip install openai pydantic oci oci-openai
```

## Configuration

1. Update shared endpoint configuration in [`config.py`](config.py).
2. Add your project ID and API keys in [`config_private.py`](config_private.py).

Security note:
- `config_private.py` contains secrets. Do not commit real keys in public repositories.

## Config Layout

This repository uses shared root config plus compatibility wrappers.

- Main reference: [`README_CONFIG.md`](README_CONFIG.md)
- Edit in normal usage: [`config.py`](config.py), [`config_private.py`](config_private.py)

## Run Examples

From the repository root:

```bash
python examples/exampleXX.py
```

## Detailed Examples

| # | Example | File | Purpose | Key API usage | Good for | Notes |
|---|---|---|---|---|---|---|
| 1 | Basic completion | [`examples/example01.py`](examples/example01.py) | Sends a simple request to `openai.gpt-5.2` and prints text + raw response. | `responses.create(...)` | Quick connectivity check. |  |
| 2 | Streaming response | [`examples/example02.py`](examples/example02.py) | Streams an answer incrementally. | `stream=True`, iterate `output_text.delta` | Chat/CLI live output. |  |
| 3 | Structured parsing | [`examples/example03.py`](examples/example03.py) | Extracts event data into typed `CalendarEvent`. | `responses.parse(...)`, `text_format=CalendarEvent` | Typed automation pipelines. | Uses Pydantic model output. |
| 4 | Web search tool | [`examples/example04.py`](examples/example04.py) | Calls the model with built-in web search enabled. | `tools=[{"type":"web_search"}]` | Retrieval-augmented answers. |  |
| 5 | Conversation state + stream | [`examples/example05.py`](examples/example05.py) | Creates a conversation and runs two streamed turns with shared context. | `conversations.create(...)`, `conversation=...` | Stateful assistants. |  |
| 6 | Reasoning summary output | [`examples/example06.py`](examples/example06.py) | Requests a response with reasoning summary and prints structured output JSON. | `reasoning={"summary":"auto"}` in `responses.create(...)` | Inspecting model reasoning summaries. |  |
| 7 | Vision input (image analysis) | [`examples/example07.py`](examples/example07.py) | Encodes a local image and asks the model to extract and summarize text. | `input_image` content in `responses.create(...)` | OCR-like extraction and vision prompts. | Reads `images/page0009.png`. |
| 8 | Vector store creation | [`examples/example11.py`](examples/example11.py) | Creates a vector store with metadata and expiration. | `vector_stores.create(...)` | Vector store setup flow. | (LA): working in preprod env. |
| 9 | File upload + list files | [`examples/example12.py`](examples/example12.py) | Uploads a local PDF file, then lists files in the project. | `files.create(...)`, `files.list(...)` | File management workflow for retrieval pipelines. | Reads `pdf/labor_market_impacts_ai.pdf`. |
| 10 | Image generation tool | [`examples/example21.py`](examples/example21.py) | Generates an image with the image generation tool and saves it as `otter.png`. | `tools=[{"type":"image_generation"}]` | Basic tool-based image generation flow. | Script header says this is not yet working. |

## Utility Scripts

| # | Utility | File | Description |
|---|---|---|---|
| 1 | List all files | [`examples/list_all_files.py`](examples/list_all_files.py) | Lists all files in the configured project, page by page. |
| 2 | Delete all files | [`examples/delete_all_files.py`](examples/delete_all_files.py) | Deletes all files in the configured project with per-file error handling. |
| 3 | List all vector stores | [`examples/list_all_vector_stores.py`](examples/list_all_vector_stores.py) | Lists all vector stores, page by page, with readable expiration time. |
| 4 | Delete all vector stores | [`examples/delete_all_vs.py`](examples/delete_all_vs.py) | Deletes all vector stores with per-item error handling. |

## Connector Scripts

| # | Connector Utility | File | Description |
|---|---|---|---|
| 1 | Create connector | [`connectors/create_connector.py`](connectors/create_connector.py) | Creates an Object Storage connector for a vector store (preproduction endpoint). |
| 2 | List connectors | [`connectors/list_connectors.py`](connectors/list_connectors.py) | Lists vector store connectors in the configured compartment. |
| 3 | Connector stats | [`connectors/get_connector_stats.py`](connectors/get_connector_stats.py) | Retrieves synchronization statistics for one connector. |
| 4 | Trigger sync | [`connectors/sync_connector.py`](connectors/sync_connector.py) | Starts a file sync job for an existing connector. |
| 5 | Update connector | [`connectors/update_connector.py`](connectors/update_connector.py) | Updates connector settings such as source configuration and schedule. |
| 6 | Delete connector | [`connectors/delete_connector.py`](connectors/delete_connector.py) | Deletes a connector by OCID. |

## Known Issue

See [`issues_found.md`](issues_found.md) for a current OCI authorization/policy issue (`404` with authorization failure) and policies snippet reference.

(17/03/2026) for now Vector Stores are available only in the preprod (ppe) environment.

## Notes

- The examples are intentionally compact and educational.
- You can copy each script as a starting point and adapt prompt, model ID, and output handling to your own workflows.
