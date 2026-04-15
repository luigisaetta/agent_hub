# Examples: Vector Stores & Retrieval

This group covers vector store setup, ingestion, inspection, and retrieval workflows.

| # | Example | File | Purpose | Key API usage | Good for | Notes |
|---|---|---|---|---|---|---|
| 1 | Vector store creation | [`example11.py`](example11.py) | Creates a vector store with metadata and expiration. | `vector_stores.create(...)` | Vector store setup flow. |  |
| 2 | File upload + list files | [`example12.py`](example12.py) | Uploads a local PDF file, then lists files in the project. | `files.create(...)`, `files.list(...)` | File management workflow for retrieval pipelines. | Reads `pdf/labor_market_impacts_ai.pdf`. |
| 3 | List files in vector store | [`example13.py`](example13.py) | Lists files already attached to a specific vector store. | `vector_stores.files.list(...)` | Inspecting ingest status/content in a vector store. | Uses a fixed `VECTOR_STORE_ID`. |
| 4 | Attach existing file to vector store | [`example14.py`](example14.py) | Retrieves a file by ID and attaches it to a vector store with attributes. | `files.retrieve(...)`, `vector_stores.files.create(...)` | Incremental ingest from existing uploaded files. | Uses fixed `VECTOR_STORE_ID` and `FILE_ID`. |
| 5 | Vector store file batch upload | [`example15.py`](example15.py) | Uploads a local PDF directly to a vector store and waits for processing. | `vector_stores.file_batches.upload_and_poll(...)` | End-to-end ingest into vector store. | Reads `pdf/labor_market_impacts_ai.pdf`. |
| 6 | Vector store semantic search | [`example16.py`](example16.py) | Executes a semantic query against a vector store and prints results. | `vector_stores.search(...)` | Basic retrieval/query workflow over indexed files. | Uses a fixed `VECTOR_STORE_ID`. |
| 7 | Vector store file status | [`example17.py`](example17.py) | Retrieves ingestion status for a specific file attached to a vector store. | `vector_stores.files.retrieve(...)` | Monitoring file ingest lifecycle and troubleshooting indexing state. | Uses fixed `VECTOR_STORE_ID` and `FILE_ID`. |
| 8 | Vector store query with file search | [`example18.py`](example18.py) | Queries a vector store through Responses API and prints inline references. | `responses.create(...)` + `tools=[{"type":"file_search"}]` | Retrieval-augmented QA over indexed project documents. | Uses fixed `VECTOR_STORE_ID`. |

