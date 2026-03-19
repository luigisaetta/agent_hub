# Demo1: Streamlit Chatbot with Responses API and Web Search

This demo builds a Streamlit chatbot that:
- uses `responses.create(...)`,
- enables the `web_search` tool,
- keeps conversational context with `conversations.create(...)` + `conversation=<id>`.

## Prerequisites

- Existing project configuration (`config.py`, `config_private.py`)
- Base project dependencies already installed

## Install demo dependency

```bash
pip install -r demos/demo1/requirements.txt
```

## Run

From the repository root:

```bash
streamlit run demos/demo1/app.py
```

## OpenAI Agent SDK Note

This first version uses the Responses API directly (aligned with the repository `exampleXX` style).  
If needed, a follow-up variant can be added using the OpenAI Agent SDK.
