"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that shows how to display the reasoning steps.
"""

import json

from openai import OpenAI

from common import print_example_summary, print_runtime_config
from config import BASE_URL
from config_private import KEY1, PROJECT_ID

MODEL_ID = "openai.gpt-5.2"
TEMPERATURE = 0.0


def main() -> None:
    """Request a response with reasoning enabled and print structured output."""
    print_runtime_config()
    print("")
    print_example_summary("Request reasoning summary and print output JSON.")
    print("")

    client = OpenAI(
        base_url=BASE_URL,
        api_key=KEY1,
        project=PROJECT_ID,
    )

    request = "What is the answer to 12 * (3 + 9)?"

    response = client.responses.create(
        model=MODEL_ID,
        temperature=TEMPERATURE,
        input=request,
        reasoning={"summary": "auto"},
        store=False,
    )

    print("Request:", request)
    pretty_output = json.dumps(response.to_dict()["output"], indent=4)
    print(pretty_output)


if __name__ == "__main__":
    main()
