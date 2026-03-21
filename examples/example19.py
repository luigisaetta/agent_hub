"""
Author: L. Saetta
Last modified: 2026-03-20
License: MIT

Description:
    This example shows how-to integrate with Langfuse to track the request.

    LA (17/03/2026): for now it is working only in preprod env.
"""

import os

from langfuse.openai import openai
from langfuse import get_client

from common import (
    print_example_summary,
    print_runtime_config,
)
from config import MODEL_ID, LANGFUSE_BASE_URL, BASE_URL
from config_private import PROJECT_ID, LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, KEY1

# integration with langfuse
os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_HOST"] = LANGFUSE_BASE_URL


def main() -> None:
    """Simple LLM call with Langfuse integration."""
    print_runtime_config()
    print("")
    print_example_summary("Simple non-streaming call with integration with Langfuse.")
    print("")

    client = openai.OpenAI(
        base_url=BASE_URL,
        api_key=KEY1,
        project=PROJECT_ID,
    )

    request = "Tell me about G. Parisi and his work on Spin Glasses?"

    response = client.responses.create(
        model=MODEL_ID,
        temperature=0.0,
        input=request,
    )

    print("Request:", request)
    print(response.output_text)
    print("")

    # Flush via global LangFuse client
    langfuse = get_client()
    langfuse.flush()


if __name__ == "__main__":
    main()
