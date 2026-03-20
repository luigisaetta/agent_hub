"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that sends a simple prompt to an OCI-hosted OpenAI-compatible endpoint
    and prints the response.
    This example show streaming use.
"""

from openai import OpenAI
from common import print_example_summary, print_runtime_config, print_streamed_output

from config import BASE_URL, MODEL_ID
from config_private import KEY1, PROJECT_ID

TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 8000


def main() -> None:
    """Run a streamed Responses API request and print tokens as they arrive."""
    print_runtime_config()
    print("")
    print_example_summary("Stream token-by-token output from the model.")
    print("")

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
