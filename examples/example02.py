"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that sends a simple prompt to an OCI-hosted OpenAI-compatible endpoint
    and prints the response.
    This example show streaming use.
"""

from pathlib import Path
import sys

from openai import OpenAI
from utils import print_streamed_output

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import BASE_URL
from config_private import KEY1, PROJECT_ID

MODEL_ID = "openai.gpt-5.2"
TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 8000


def main() -> None:
    """Run a streamed Responses API request and print tokens as they arrive."""
    client = OpenAI(
        base_url=BASE_URL,
        api_key=KEY1,
        project=PROJECT_ID,
    )

    request = "Tell me something about Enrico Fermi?"

    response = client.responses.create(
        model=MODEL_ID,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        input=request,
        stream=True,
    )

    print("")
    print("Request:", request)
    print_streamed_output(response)
    print("\n\n")


if __name__ == "__main__":
    main()
