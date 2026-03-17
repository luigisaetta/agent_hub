"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that sends a simple prompt to an OCI-hosted OpenAI-compatible endpoint
    and prints the response.
"""

from openai import OpenAI

from config import BASE_URL
from config_private import KEY1, PROJECT_ID

MODEL_ID = "openai.gpt-5.2"
TEMPERATURE = 0.0

client = OpenAI(
    base_url=BASE_URL,
    api_key=KEY1,
    project=PROJECT_ID,
)

request = "What is 2x2?"

response = client.responses.create(
    model=MODEL_ID,
    temperature=TEMPERATURE,
    input=request,
)

print("Request:", request)
print(response.output_text)

print("")
print("Full response:", response)
