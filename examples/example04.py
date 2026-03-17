"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows the usage of the web search tool,
    which allows the model to perform web searches and use the results in its response.
"""

from openai import OpenAI

from config import BASE_URL
from config_private import KEY1, PROJECT_ID

MODEL_ID = "openai.gpt-oss-120b"
TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 8000

client = OpenAI(
    base_url=BASE_URL,
    api_key=KEY1,
    project=PROJECT_ID,
)

request = "Create for me a complete report about Luigi Saetta, from Oracle"

response = client.responses.create(
    model=MODEL_ID,
    temperature=TEMPERATURE,
    max_output_tokens=MAX_OUTPUT_TOKENS,
    input=request,
    tools=[{"type": "web_search"}],
)

print("Request:", request)

print(response.output_text)
