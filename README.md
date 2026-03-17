# Agent Hub Examples for OCI OpenAI-Compatible API

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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
├── examples/
│   ├── config.py
│   ├── config_private.py
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

1. Update shared endpoint configuration in [`examples/config.py`](examples/config.py).
2. Add your project ID and API keys in [`examples/config_private.py`](examples/config_private.py).

Security note:
- `config_private.py` contains secrets. Do not commit real keys in public repositories.

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
| 6 | Vector store creation | [`examples/example11.py`](examples/example11.py) | Creates a vector store with metadata and expiration. | `vector_stores.create(...)` | Vector store setup flow. | (LA): working in preprod env. |

## Known Issue

See [`issues_found.md`](issues_found.md) for a current OCI authorization/policy issue (`404` with authorization failure) and policies snippet reference.

## Notes

- The examples are intentionally compact and educational.
- You can copy each script as a starting point and adapt prompt, model ID, and output handling to your own workflows.
