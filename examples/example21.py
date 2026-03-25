"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that show ho to generate an image using the image generation tool.
    This is NOT yet working
"""

import base64


from common import get_inference_client, print_example_summary, print_runtime_config
from config import MODEL_ID

TEMPERATURE = 0.0

print_runtime_config()
print("")
print_example_summary("Generate an image and save it as result.png.")
print("")

client = get_inference_client()

# INPUT = "Generate an image of gray tabby cat hugging an otter with an orange scarf"
INPUT = "Generate an image that represent the importance of Observability for AI agents"

response = client.responses.create(
    model=MODEL_ID,
    input=INPUT,
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

    with open("result.png", "wb") as f:
        f.write(base64.b64decode(image_base64))
