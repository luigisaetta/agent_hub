"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows the usage of the web search tool,
    which allows the model to perform web searches and use the results in its response.
"""

from common import get_inference_client, print_example_summary, print_runtime_config
from config import MODEL_ID

TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 8000


def main() -> None:
    """Run a request with the built-in web search tool enabled."""
    print_runtime_config()
    print("")
    print_example_summary("Use web_search tool for retrieval-augmented response.")
    print("")

    client = get_inference_client()

    request = """Create for me a complete report about Luigi Saetta, from Oracle.
    Find accurate and up-to-date information about him, and use it 
    to write a report about his career, achievements, and current position. 
    Use the web search tool to find the most recent information about him."""

    response = client.responses.create(
        model=MODEL_ID,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        input=request,
        tools=[{"type": "web_search"}],
    )

    print("Request:", request)
    print(response.output_text)
    print("")


if __name__ == "__main__":
    main()
