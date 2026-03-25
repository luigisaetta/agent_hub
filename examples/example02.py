"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that sends a simple prompt to an OCI-hosted OpenAI-compatible endpoint
    and prints the response.
    This example show streaming use.
"""

from common import (
    get_inference_client,
    print_example_summary,
    print_runtime_config,
    print_streamed_output,
)

from config import MODEL_ID

TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 12000


def main() -> None:
    """Run a streamed Responses API request and print tokens as they arrive."""
    print_runtime_config()
    print("")
    print_example_summary("Stream token-by-token output from the model.")
    print("")

    client = get_inference_client()

    request = (
        "Create a complete report about Enrico Fermi, "
        "his life and his contribution to Physics?"
    )

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
