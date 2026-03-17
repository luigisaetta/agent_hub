"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that shows how to analyze an image and extract some content.
"""

import base64
from openai import OpenAI

from config import BASE_URL
from config_private import KEY1, PROJECT_ID

MODEL_ID = "openai.gpt-5.2"
TEMPERATURE = 0.0


def encode_image(image_path):
    """
    This function reads an image file and encodes it in base64 format.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


base64_image = encode_image("../images/page0009.png")

client = OpenAI(
    base_url=BASE_URL,
    api_key=KEY1,
    project=PROJECT_ID,
)

response = client.responses.create(
    model="openai.gpt-4.1",
    store=False,
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Extract and summarize all the text contained in the image",
                },
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{base64_image}",
                    "detail": "high",
                },
            ],
        }
    ],
)

print(response.output_text)
