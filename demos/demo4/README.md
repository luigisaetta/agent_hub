# Demo4: Full RAG with file_search (Progressive Loading + Chat UI)

Demo4 includes two parts:
- **Loading**: progressively ingest all files from `pdf_rag/` into the configured vector store, skipping filenames already present.
- **Query UI**: Streamlit chatbot with conversation memory, strict `file_search`, and streamed output.

## Prerequisites

- Existing project configuration (`config.py`, `config_private.py`)
- `VECTOR_STORE_ID` configured in the active `.env` profile
- Local files to ingest under `pdf_rag/`

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
