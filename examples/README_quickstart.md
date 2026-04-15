# Examples: Quickstart & Core

Use this group to get productive quickly with the OpenAI-compatible OCI APIs.

| # | Example | File | Purpose | Key API usage | Good for | Notes |
|---|---|---|---|---|---|---|
| 1 | Basic completion | [`example01.py`](example01.py) | Sends a simple request to `openai.gpt-5.2` and prints text + raw response. | `responses.create(...)` | Quick connectivity check. |  |
| 2 | Streaming response | [`example02.py`](example02.py) | Streams an answer incrementally. | `stream=True`, iterate `output_text.delta` | Chat/CLI live output. |  |
| 3 | Structured parsing | [`example03.py`](example03.py) | Extracts event data into typed `CalendarEvent`. | `responses.parse(...)`, `text_format=CalendarEvent` | Typed automation pipelines. | Uses Pydantic model output. |
| 4 | Web search tool | [`example04.py`](example04.py) | Calls the model with built-in web search enabled. | `tools=[{"type":"web_search"}]` | Retrieval-augmented answers. |  |
| 5 | Conversation state + stream | [`example05.py`](example05.py) | Creates a conversation and runs two streamed turns with shared context. | `conversations.create(...)`, `conversation=...` | Stateful assistants. |  |
| 6 | Reasoning summary output | [`example06.py`](example06.py) | Requests a response with reasoning summary and prints structured output JSON. | `reasoning={"summary":"auto"}` in `responses.create(...)` | Inspecting model reasoning summaries. |  |

