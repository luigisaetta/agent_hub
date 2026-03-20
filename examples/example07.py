"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that shows how to analyze an image and extract some content.
"""

import base64
from pathlib import Path

from openai import OpenAI

from common import print_example_summary, print_runtime_config
from config import BASE_URL, MODEL_ID
from config_private import KEY1, PROJECT_ID

TEMPERATURE = 0.0


def encode_image(image_path: Path) -> str:
    """
    This function reads an image file and encodes it in base64 format.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def main() -> None:
    """Encode an image and ask the model to extract and summarize its text."""
    print_runtime_config()
    print("")
    print_example_summary("Analyze an image and extract/summarize text.")
    print("")

    root_dir = Path(__file__).resolve().parents[1]
    image_path = root_dir / "images" / "page0009.png"
    base64_image = encode_image(image_path)

    client = OpenAI(
        base_url=BASE_URL,
        api_key=KEY1,
        project=PROJECT_ID,
    )

    response = client.responses.create(
        model=MODEL_ID,
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
    print("")


if __name__ == "__main__":
    main()
