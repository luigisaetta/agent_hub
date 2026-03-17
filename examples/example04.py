"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows the usage of the web search tool,
    which allows the model to perform web searches and use the results in its response.
"""

from pathlib import Path
import sys

from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import BASE_URL
from config_private import KEY1, PROJECT_ID

MODEL_ID = "openai.gpt-oss-120b"
TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 8000


def main() -> None:
    """Run a request with the built-in web search tool enabled."""
    client = OpenAI(
        base_url=BASE_URL,
        api_key=KEY1,
        project=PROJECT_ID,
    )

    request = "Create for me a complete report about Luigi Saetta, from Oracle"

    response = client.responses.create(
        model=MODEL_ID,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        input=request,
        tools=[{"type": "web_search"}],
    )

    print("Request:", request)
    print(response.output_text)


if __name__ == "__main__":
    main()
