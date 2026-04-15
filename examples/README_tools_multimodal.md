# Examples: Tools & Multimodal

This group focuses on tool-calling and multimodal interactions.

| # | Example | File | Purpose | Key API usage | Good for | Notes |
|---|---|---|---|---|---|---|
| 1 | Vision input (image analysis) | [`example07.py`](example07.py) | Encodes a local image and asks the model to extract and summarize text. | `input_image` content in `responses.create(...)` | OCR-like extraction and vision prompts. | Reads `images/page0009.png`. |
| 2 | Image generation tool | [`example21.py`](example21.py) | Generates an image with the image generation tool and saves it as `otter.png`. | `tools=[{"type":"image_generation"}]` | Basic tool-based image generation flow. | Script header says this is not yet working. |
| 3 | Code interpreter tool | [`example22.py`](example22.py) | Runs a Responses API request with `code_interpreter` so the model can execute Python in an isolated container to solve a math task and return the computed result. | `tools=[{"type":"code_interpreter","container":{"type":"auto","memory_limit":"4g"}}]`, `responses.create(...)` | Computational tasks (math/data transformations) where model-generated code execution is needed. | Prints raw `resp.output`, including tool execution artifacts. |
| 4 | Custom function tool calling | [`example23.py`](example23.py) | Demonstrates a complete iterative loop where the model emits `function_call`, local Python executes the function, and the script returns `function_call_output` until final answer. | `tools=[{"type":"function",...}]`, `responses.create(...)`, `previous_response_id=...` | Building agentic workflows with domain-specific tools. | Uses a simulated weather function (`get_weather`) to keep the example self-contained. |

