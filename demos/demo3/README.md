# Demo3: Streamlit Single-PDF Preview and Processing

This demo provides a first iteration of a PDF processing flow with Streamlit.

Features:
- upload exactly one PDF from the sidebar,
- render an immediate PDF preview in the sidebar (HTML inline viewer),
- process the uploaded file with a dedicated **Process PDF** button,
- upload the PDF to the Responses API,
- extract full text using `google.gemini-2.5-pro`,
- parse the full extracted text into the Pydantic schema in `llm_schema_models.py`,
- show structured JSON in the central area of Streamlit,
- show processing metrics (timings and token usage).

## Prerequisites

- Project configuration already available in this repository
- Python 3.11+
- Active production profile selected in the same shell
  (`source ./set_env.sh prod-chicago` or `source ./set_env.sh prod-frankfurt`)

## Install demo dependencies

```bash
pip install -r demos/demo3/requirements.txt
```

## Run

From the repository root:

```bash
streamlit run demos/demo3/app.py
```

## Current Behavior

1. Upload a PDF in the sidebar.
2. The sidebar immediately shows the PDF preview.
3. Click **Process PDF** to run the first-step workflow.
4. The app displays:
   - structured JSON generated from the full extracted text,
   - processing metrics (total time, step times, and tokens in/out/total).

## Notes

- Structured extraction is executed with `responses.parse(...)` and `text_format=ProceduraVendita`.
- The schema source file is `demos/demo3/llm_schema_models.py`.
- The extracted raw text is used internally in the pipeline and is not shown in the UI.
