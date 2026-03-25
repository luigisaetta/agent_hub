"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that sends a simple prompt to an OCI-hosted OpenAI-compatible endpoint
    and prints the response.
     This example shows how to use the text_format parameter to parse the response
     into a structured format
"""

from pydantic import BaseModel


from common import get_inference_client, print_example_summary, print_runtime_config
from config import MODEL_ID

TEMPERATURE = 0.0


class CalendarEvent(BaseModel):
    """
    This class defines the structure of a calendar event, with fields for the event name,
    date, and participants.
    """

    name: str
    date: str
    participants: list[str]


def main() -> None:
    """Parse unstructured text into a typed calendar event object."""
    print_runtime_config()
    print("")
    print_example_summary("Parse text into a typed Pydantic object.")
    print("")

    client = get_inference_client()

    input_text = "Alice and Bob are going to a science fair on Friday."
    response = client.responses.parse(
        model=MODEL_ID,
        input=[
            {"role": "system", "content": "Extract the event information."},
            {
                "role": "user",
                "content": input_text,
            },
        ],
        store=False,
        text_format=CalendarEvent,
    )

    event = response.output_parsed
    print("")
    print("Input text:", input_text)
    print("Parsed event object:")
    print(event)
    print("")


if __name__ == "__main__":
    main()
