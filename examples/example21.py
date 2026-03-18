"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that show ho to generate an image using the image generation tool.
    This is NOT yet working
"""

import base64

from openai import OpenAI

from common import print_example_summary, print_runtime_config
from config import BASE_URL
from config_private import KEY1, PROJECT_ID

MODEL_ID = "openai.gpt-5.2"
TEMPERATURE = 0.0

print_runtime_config()
print("")
print_example_summary("Generate an image and save it as otter.png.")
print("")

client = OpenAI(
    base_url=BASE_URL,
    api_key=KEY1,
    project=PROJECT_ID,
)

response = client.responses.create(
    model="openai.gpt-5.2",
    input="Generate an image of gray tabby cat hugging an otter with an orange scarf",
    tools=[{"type": "image_generation"}],
    store=False,
    stream=False,
)

# Save the image to a file
image_data = [
    output.result
    for output in response.output
    if output.type == "image_generation_call"
]

if image_data:
    image_base64 = image_data[0]

    with open("otter.png", "wb") as f:
        f.write(base64.b64decode(image_base64))
