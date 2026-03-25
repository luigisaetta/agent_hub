"""
Author: L. Saetta
Last modified: 2026-03-20
License: MIT

Description:
    This example shows how-to integrate with Langfuse to track the request.
    In this case response is streamed.
"""

import os

from langfuse.openai import openai as langfuse_openai
from langfuse import get_client

from common import (
    get_inference_client,
    print_example_summary,
    print_runtime_config,
    print_streamed_output,
)
from config import MODEL_ID, LANGFUSE_BASE_URL
from config_private import LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY

# integration with langfuse
os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_HOST"] = LANGFUSE_BASE_URL

TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 4192


def main() -> None:
    """Simple LLM call with Langfuse integration."""
    print_runtime_config()
    print("")
    print_example_summary("Streaming call with integration with Langfuse.")
    print("")

    # Use Langfuse OpenAI wrapper so requests are instrumented and traced.
    client = get_inference_client(client_class=langfuse_openai.OpenAI)

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

    # Flush via global LangFuse client
    langfuse = get_client()
    langfuse.flush()


if __name__ == "__main__":
    main()
