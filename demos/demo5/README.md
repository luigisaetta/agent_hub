# Demo5: Vector Store Chunk Explorer

This demo provides a Streamlit UI to explore `vector_stores.search(...)` results.

Given a query, it searches the configured vector store and renders in the central
area:
- retrieved chunk text,
- score,
- file/chunk identifiers,
- page metadata and full additional properties.

## Prerequisites

- Existing project configuration (`config.py`, `config_private.py`)
- `VECTOR_STORE_ID` configured in the active `.env` profile
- Active production profile selected in the same shell
  (`source ./set_env.sh prod-chicago`, `prod-frankfurt`, or `prod-london`)

## Install demo dependency

```bash
pip install -r demos/demo5/requirements.txt
```

## Run

From the repository root:

```bash
streamlit run demos/demo5/app.py
```

## Sidebar configuration

The sidebar always shows the effective runtime configuration:
- `REGION`
- `VECTOR_STORE_ID`

## Notes

- Search is executed with `client.vector_stores.search(...)`.
