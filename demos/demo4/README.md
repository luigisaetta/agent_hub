# Demo4: Full RAG with file_search (Progressive Loading + Chat UI)

Demo4 includes two parts:
- **Loading**: progressively ingest all files from `pdf_rag/` into the configured vector store, skipping filenames already present.
- **Query UI**: Streamlit chatbot with conversation memory, strict `file_search`, and streamed output.

## Prerequisites

- Existing project configuration (`config.py`, `config_private.py`)
- A vector store already created in your OCI project
- `VECTOR_STORE_ID` configured in the active `.env` profile (pointing to that existing vector store)
- Local files to ingest under `pdf_rag/`

If you still need to create a vector store, run:

```bash
python -m examples.example11
```

Then copy the created vector store id into your active `.env` profile as `VECTOR_STORE_ID`.

## Install demo dependency

```bash
pip install -r demos/demo4/requirements.txt
```

## 1) Progressive loading from pdf_rag/

From repository root:

```bash
python -m demos.demo4.load_files
```

Behavior:
- reads only `.pdf` files in `pdf_rag/`
- enforces `MAX_FILE_SIZE=5MB` and skips files above the limit
- checks by filename if already present in vector store
- uploads missing files one-by-one via `files.create(...)`
- then attaches each uploaded file to the vector store via `vector_stores.files.create(...)`

## 2) Run Streamlit UI

From repository root:

```bash
streamlit run demos/demo4/app.py
```

UI behavior:
- creates one conversation and keeps it across turns
- each user request runs strict `file_search`
- main area streams the answer token-by-token, then shows the final consolidated text
- sidebar shows references with filename and pages

## Prompt customization

Prompt text used by Demo4 is defined in:

`demos/demo4/prompts.py`

If you want to change system behavior (strictness, tone, fallback sentence), edit
`STRICT_INSTRUCTIONS` there.

## 3) Check file status in vector store

From repository root:

```bash
python -m demos.demo4.list_files_in_vector_store
```

This utility lists files currently attached to the configured vector store and
prints status-related fields (`status`, `created_at`, `usage_bytes`), plus
filename resolution when available.
