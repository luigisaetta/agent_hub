# OCI Enterprise AI Agents Examples

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen.svg)](https://github.com/pylint-dev/pylint)
[![Tests: pytest](https://img.shields.io/badge/tests-pytest-blue.svg)](https://docs.pytest.org/)
[![Codex Ready](https://img.shields.io/badge/Codex-Ready-0A66C2)](./Agents.md)

This repository contains practical Python examples that call Oracle Cloud Infrastructure (OCI) Generative AI endpoints through the OpenAI-compatible API.

Highlights from the most useful examples and demos:
- [`examples/example01.py`](examples/example01.py): minimal text request, ideal as first connectivity smoke test.
- [`examples/example02.py`](examples/example02.py): streaming output token-by-token for chat/CLI-style incremental UX.
- [`examples/example03.py`](examples/example03.py): structured parsing into typed objects (Pydantic), useful for automation flows.
- [`examples/example05.py`](examples/example05.py): multi-turn state with the Conversations API plus streaming responses.
- [`examples/example06.py`](examples/example06.py): reasoning summary output for debugging and response explainability.
- [`examples/example23.py`](examples/example23.py): end-to-end custom function tool calling loop (`function_call` + `function_call_output`).
- [`examples/example18.py`](examples/example18.py): file-search over vector stores with inline citations in final answers.
- [`connectors/create_connector.py`](connectors/create_connector.py) + related scripts in [`connectors/`](connectors): create/sync/manage vector-store connectors to Object Storage.
- [`demos/demo2`](demos/demo2): Streamlit chatbot with web search and Langfuse-integrated observability/tracing.
- [`demos/demo4`](demos/demo4): full RAG flow with progressive loading from `pdf_rag/`, strict `file_search`, persistent conversation, streamed answers, and sidebar references with pages.
- [`demos/demo5`](demos/demo5): Streamlit vector-store explorer that returns retrieved chunk text and metadata for a user query.
- [`demos/demo6`](demos/demo6): LangGraph-style RAG backend with SSE plus Streamlit chat UI with streamed final answer and sidebar references from reranker.

## Documentation

- Configuration: [`docs/configurations.md`](docs/configurations.md)
- Testing: [`docs/testing.md`](docs/testing.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)

## Quickstart

1. Install base dependencies:

```bash
pip install -r requirements.txt
```

2. Fill the `.env` file for your target production region (for example
`.env.prod-chicago` or `.env.prod-frankfurt`) with valid values for:
`PROJECT_ID`, `KEY1`, `COMPARTMENT_ID`, `VECTOR_STORE_ID`
(and Langfuse keys only if needed; otherwise they can be left unset/empty).

3. Select active production profile:

```bash
source ./set_env.sh prod-chicago
./show_current_env.sh
```

4. Run a first connectivity example:

```bash
python -m examples.example01
```

5. Run one demo (example: Demo 4):

```bash
pip install -r demos/demo4/requirements.txt
streamlit run demos/demo4/app.py
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
| 8 | Vector store creation | [`examples/example11.py`](examples/example11.py) | Creates a vector store with metadata and expiration. | `vector_stores.create(...)` | Vector store setup flow. |  |
| 9 | File upload + list files | [`examples/example12.py`](examples/example12.py) | Uploads a local PDF file, then lists files in the project. | `files.create(...)`, `files.list(...)` | File management workflow for retrieval pipelines. | Reads `pdf/labor_market_impacts_ai.pdf`. |
| 10 | List files in vector store | [`examples/example13.py`](examples/example13.py) | Lists files already attached to a specific vector store. | `vector_stores.files.list(...)` | Inspecting ingest status/content in a vector store. | Uses a fixed `VECTOR_STORE_ID`. |
| 11 | Attach existing file to vector store | [`examples/example14.py`](examples/example14.py) | Retrieves a file by ID and attaches it to a vector store with attributes. | `files.retrieve(...)`, `vector_stores.files.create(...)` | Incremental ingest from existing uploaded files. | Uses fixed `VECTOR_STORE_ID` and `FILE_ID`. |
| 12 | Vector store file batch upload | [`examples/example15.py`](examples/example15.py) | Uploads a local PDF directly to a vector store and waits for processing. | `vector_stores.file_batches.upload_and_poll(...)` | End-to-end ingest into vector store. | Reads `pdf/labor_market_impacts_ai.pdf`. |
| 13 | Vector store semantic search | [`examples/example16.py`](examples/example16.py) | Executes a semantic query against a vector store and prints results. | `vector_stores.search(...)` | Basic retrieval/query workflow over indexed files. | Uses a fixed `VECTOR_STORE_ID`. |
| 14 | Vector store file status | [`examples/example17.py`](examples/example17.py) | Retrieves ingestion status for a specific file attached to a vector store. | `vector_stores.files.retrieve(...)` | Monitoring file ingest lifecycle and troubleshooting indexing state. | Uses fixed `VECTOR_STORE_ID` and `FILE_ID`. |
| 15 | Vector store query with file search | [`examples/example18.py`](examples/example18.py) | Queries a vector store through Responses API and prints inline references. | `responses.create(...)` + `tools=[{"type":"file_search"}]` | Retrieval-augmented QA over indexed project documents. | Uses fixed `VECTOR_STORE_ID`. |
| 16 | Langfuse integration | [`examples/example19.py`](examples/example19.py) | Sends a non-streaming Responses API request instrumented with Langfuse and flushes traces. | `langfuse.openai.OpenAI(...)`, `responses.create(...)`, `langfuse.flush()` | Observability/tracing of LLM calls. | Requires Langfuse keys/host. |
| 17 | Langfuse integration (streaming) | [`examples/example20.py`](examples/example20.py) | Sends a streaming Responses API request instrumented with Langfuse and flushes traces. | `langfuse.openai.OpenAI(...)`, `responses.create(..., stream=True)`, `langfuse.flush()` | Observability/tracing with token-by-token output. | Requires Langfuse keys/host. |
| 18 | Image generation tool | [`examples/example21.py`](examples/example21.py) | Generates an image with the image generation tool and saves it as `otter.png`. | `tools=[{"type":"image_generation"}]` | Basic tool-based image generation flow. | Script header says this is not yet working. |
| 19 | Code interpreter tool | [`examples/example22.py`](examples/example22.py) | Runs a Responses API request with `code_interpreter` so the model can execute Python in an isolated container to solve a math task and return the computed result. | `tools=[{"type":"code_interpreter","container":{"type":"auto","memory_limit":"4g"}}]`, `responses.create(...)` | Computational tasks (math/data transformations) where model-generated code execution is needed. | Prints raw `resp.output`, including tool execution artifacts. |
| 20 | Custom function tool calling | [`examples/example23.py`](examples/example23.py) | Demonstrates a complete iterative loop where the model emits `function_call`, local Python executes the function, and the script returns `function_call_output` until final answer. | `tools=[{"type":"function",...}]`, `responses.create(...)`, `previous_response_id=...` | Building agentic workflows with domain-specific tools. | Uses a simulated weather function (`get_weather`) to keep the example self-contained. |

## Detailed Demos

| # | Demo | Folder | Purpose | Key API usage | Good for | Notes |
|---|---|---|---|---|---|---|
| 1 | Responses chatbot + web search | [`demos/demo1`](demos/demo1) | Streamlit chatbot with multi-turn context and built-in web search. | `conversations.create(...)`, `responses.create(..., tools=[{"type":"web_search"}], stream=True)` | End-to-end chat UX demo using Responses API tools. | Includes basic UI/backend separation (`app.py`, `backend.py`, `state.py`). |
| 2 | Responses chatbot + web search + Langfuse | [`demos/demo2`](demos/demo2) | Streamlit chatbot with multi-turn context, built-in web search, and Langfuse traces on LLM calls. | `conversations.create(...)`, `responses.create(..., tools=[{"type":"web_search"}], stream=True)`, `langfuse.openai` instrumentation | End-to-end chat UX demo with observability/tracing. | Includes basic UI/backend separation (`app.py`, `backend.py`, `state.py`). |
| 3 | Structured extraction from legal PDFs | [`demos/demo3`](demos/demo3) | Streamlit app that previews one uploaded PDF, extracts raw text, and produces structured JSON output. | `files.create(...)`, `responses.create(...)` for PDF-to-text, `responses.parse(..., text_format=ProceduraVendita)` | End-to-end document extraction pipeline with typed schema output. | Uses hybrid models: Gemini for text extraction + GPT-5.2 for structured parsing. |
| 4 | Full RAG with file_search | [`demos/demo4`](demos/demo4) | Two-step RAG demo: progressive ingestion from `pdf_rag/` and Streamlit chat UI on indexed docs. | Loading: `vector_stores.files.list(...)`, `files.retrieve(...)`, `files.create(...)`, `vector_stores.files.create(...)`; Query: `conversations.create(...)`, `responses.create(..., tools=[{"type":"file_search"}], include=["file_search_call.results"], stream=True)` | Practical end-to-end RAG workflow with strict grounding, streaming UX, and citations. | Sidebar shows references (`filename`, `pages`) extracted from response annotations. |
| 5 | Vector store chunk explorer | [`demos/demo5`](demos/demo5) | Streamlit explorer that executes semantic search on a vector store and renders retrieved chunks plus metadata. | `vector_stores.search(...)` | Debugging retrieval quality and inspecting chunk-level evidence. | Sidebar shows runtime config (`REGION`, `VECTOR_STORE_ID`). |
| 6 | LangGraph-style RAG backend + Streamlit UI | [`demos/demo6`](demos/demo6) | FastAPI backend with 4-node LangGraph-style RAG flow and standardized SSE events, plus Streamlit chat UI with history and real-time streamed answer. | `POST /chat` with `text/event-stream`; `SemanticSearcher` uses `vector_stores.search(...)`; `AnswerGenerator` streams via Responses API | Building and debugging event-driven agent orchestration with a lightweight chat frontend. | Sidebar shows runtime config and current-turn reranker references (`filename`, `pages`) in collapsible items. |

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
| 1 | Create connector | [`connectors/create_connector.py`](connectors/create_connector.py) | Creates an Object Storage connector for a vector store. |
| 2 | List connectors | [`connectors/list_connectors.py`](connectors/list_connectors.py) | Lists vector store connectors in the configured compartment. |
| 3 | Connector stats | [`connectors/get_connector_stats.py`](connectors/get_connector_stats.py) | Retrieves synchronization statistics for one connector. |
| 4 | Trigger file sync | [`connectors/trigger_file_sync.py`](connectors/trigger_file_sync.py) | Triggers a manual file sync operation for one connector. |
| 5 | Update connector | [`connectors/update_connector.py`](connectors/update_connector.py) | Updates connector settings such as source configuration and schedule. |
| 6 | Delete connector | [`connectors/delete_connector.py`](connectors/delete_connector.py) | Deletes a connector by OCID. |
| 7 | Connector logs | [`connectors/get_connector_logs.py`](connectors/get_connector_logs.py) | Retrieves and prints recent logs for one connector. |

## Prerequisites

- Python 3.11+
- An OCI Generative AI project and endpoint access
- A valid OCI API key with permissions for Generative AI

Install dependencies:

```bash
pip install -r requirements.txt
```

If you want to use Langfuse integration
```bash
pip install langfuse
```

Install test dependencies:

```bash
pip install -r requirements-dev.txt
```

Configuration details are documented in [`docs/configurations.md`](docs/configurations.md).

## Secret Profiles

Secrets are loaded from environment profile files:
- `.env.prod-chicago`
- `.env.prod-frankfurt`

This repository supports only production profiles (`prod-*`).
When you run `source ./set_env.sh <profile>`, the script exports:
- `AGENT_HUB_REGION`
- `AGENT_HUB_ENV_FILE`

These environment variables drive runtime configuration for the current shell
session (instead of editing region values manually in code).

Each profile should define: `PROJECT_ID`, `KEY1`, `COMPARTMENT_ID`,
`LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `VECTOR_STORE_ID`.
If you do not use Langfuse, `LANGFUSE_SECRET_KEY` and `LANGFUSE_PUBLIC_KEY`
can be unset or empty strings.

Authentication mode can be selected with `OCI_AUTH_MODE`:
- `user_principal` (default if not set)
- `session`

Set the active profile from repository root:

```bash
source ./set_env.sh prod-chicago
./show_current_env.sh
```

Profiles currently available:
- `prod-chicago`
- `prod-frankfurt`

Before running examples/demos/connectors, always select one of the profiles
above in the same terminal session.

## Authentication Troubleshooting

If a script returns `401 NotAuthenticated` while using OCI session authentication:

1. Ensure you selected the profile in the same shell session:
```bash
source ./set_env.sh prod-chicago
```
2. Refresh the OCI session token for your local OCI profile **only if you are using session-based authentication** (`OCI_AUTH_MODE=session`):
```bash
oci session authenticate --profile-name DEFAULT
```

## Run Examples

From the repository root:

```bash
python -m examples.exampleXX
```

## Run Connectors

From the repository root:

```bash
python -m connectors.script_name
```

## Run Demos

From the repository root:

```bash
pip install -r demos/demo1/requirements.txt
streamlit run demos/demo1/app.py

pip install -r demos/demo2/requirements.txt
streamlit run demos/demo2/app.py

pip install -r demos/demo3/requirements.txt
streamlit run demos/demo3/app.py

pip install -r demos/demo4/requirements.txt
streamlit run demos/demo4/app.py

pip install -r demos/demo5/requirements.txt
streamlit run demos/demo5/app.py

pip install -r demos/demo6/requirements.txt
uvicorn demos.demo6.api:app --reload --port 8080
streamlit run demos/demo6/app.py
```

Testing details are documented in [`docs/testing.md`](docs/testing.md).

Project structure and module layout are documented in [`docs/architecture.md`](docs/architecture.md).

## Known Issue

See [`issues_found.md`](issues_found.md) for a current OCI authorization/policy issue (`404` with authorization failure) and policies snippet reference.

## Notes

- The examples are intentionally compact and educational.
- You can copy each script as a starting point and adapt prompt, model ID, and output handling to your own workflows.
