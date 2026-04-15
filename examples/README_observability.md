# Examples: Observability

This group shows Langfuse instrumentation patterns for Responses API calls.

| # | Example | File | Purpose | Key API usage | Good for | Notes |
|---|---|---|---|---|---|---|
| 1 | Langfuse integration | [`example19.py`](example19.py) | Sends a non-streaming Responses API request instrumented with Langfuse and flushes traces. | `langfuse.openai.OpenAI(...)`, `responses.create(...)`, `langfuse.flush()` | Observability/tracing of LLM calls. | Requires Langfuse keys/host. |
| 2 | Langfuse integration (streaming) | [`example20.py`](example20.py) | Sends a streaming Responses API request instrumented with Langfuse and flushes traces. | `langfuse.openai.OpenAI(...)`, `responses.create(..., stream=True)`, `langfuse.flush()` | Observability/tracing with token-by-token output. | Requires Langfuse keys/host. |

