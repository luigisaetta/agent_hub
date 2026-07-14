# Demo2: Streamlit Chatbot with Responses API, Web Search, and Langfuse

This demo builds a Streamlit chatbot that:
- uses `responses.create(...)`,
- enables the `web_search` tool,
- keeps conversational context with `conversations.create(...)` + `conversation=<id>`,
- sends traces to Langfuse for each LLM call.

## Prerequisites

- Existing project configuration (`config.py`, `config_private.py`)
- Base project dependencies already installed
- Active production profile selected in the same shell
  (`source ./set_env.sh prod-chicago`, `prod-frankfurt`, or `prod-london`)

## Install demo dependency

```bash
pip install -r demos/demo2/requirements.txt
```

## Run

From the repository root:

```bash
streamlit run demos/demo2/app.py
```
