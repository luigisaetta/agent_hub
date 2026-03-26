"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that shows how to use conde-interpreter
    and prints the response.
"""

from common import get_inference_client, print_example_summary, print_runtime_config
from config import MODEL_ID

TEMPERATURE = 0.0


def main() -> None:
    """Run a code interpter and print the result."""
    print_runtime_config()
    print("")
    print_example_summary("Run code interpreter with a container, with Responses API.")
    print("")

    client = get_inference_client()

    instructions = """
    You are a personal math tutor. When asked a math question,
    write and run code using the python tool to answer the question.
    """

    resp = client.responses.create(
        model=MODEL_ID,
        tools=[
            {
                "type": "code_interpreter",
                "container": {"type": "auto", "memory_limit": "4g"}
            }
        ],
        instructions=instructions,
        input="I need to solve the equation 3x + 11 = 14. Can you help me?",
    )

    print(resp.output)


if __name__ == "__main__":
    main()
