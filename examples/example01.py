"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that sends a simple prompt to an OCI-hosted OpenAI-compatible endpoint
    and prints the response.
"""

from common import get_inference_client, print_example_summary, print_runtime_config
from config import MODEL_ID

TEMPERATURE = 0.0


def main() -> None:
    """Run a basic Responses API request and print the result."""
    print_runtime_config()
    print("")
    print_example_summary("Basic text completion with Responses API.")
    print("")

    client = get_inference_client()

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
    print("")


if __name__ == "__main__":
    main()
